from tkinter import ttk
import tkinter as tk
from matplotlib import style
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib
import urllib
import json
from matplotlib import pyplot as plt
from controller.serial.serial import SerialBus
from controller.database.database import Database

import pandas as pd
import numpy as np
matplotlib.use("TkAgg")

style.use('ggplot')

# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Helvetica", 10)
SMALL_FONT = ("Helvetica", 8)

f = Figure()
a = f.add_subplot(111)


def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()


def animate(i):
    pullData = open("sampleText.txt", "r").read()
    dataList = pullData.split('\n')
    xList = []
    yList = []
    for eachLine in dataList:
        if len(eachLine) > 1:
            x, y = eachLine.split(',')
            xList.append(int(x))
            yList.append(int(y))

    a.clear()
    a.plot(xList, yList)


class SDNcontrollerapp(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        # tk.Tk.iconbitmap(self, default="clienticon.ico")
        tk.Tk.wm_title(self, "SDN serial controller")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(
            label="Save settings", command=lambda: popupmsg('Not supported just yet!'))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}

        for F in (StartPage, setupPage, MainPage):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text=("""SDN controller
        use at your own risk. There is no promise
        of warranty."""), font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button1 = ttk.Button(self, text="Agree",
                             command=lambda: controller.show_frame(setupPage))
        button1.pack()

        button2 = ttk.Button(self, text="Disagree",
                             command=quit)
        button2.pack()


class MainPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        print('main page')
        label = tk.Label(
            self, text="Software-Defined Wireless Sensor Networks", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        label2 = tk.Label(self, text="Serial interface", font=LARGE_FONT)
        label2.pack(pady=10, padx=10)

        # Calling DataFrame constructor on list
        # print('database packet')
        # coll = Database.find("packets", {})
        # df = pd.DataFrame(coll)
        # print(df)

        # self.df = df

        # Using treeview widget
        self.treev = ttk.Treeview(self, selectmode='browse')
        # Calling pack method w.r.to treeview
        self.treev.pack()

        self.heading_set = 0

        # Constructing vertical scrollbar
        # with treeview
        verscrlbar = ttk.Scrollbar(
            self,  orient="vertical",  command=self.treev.yview)

        # Calling pack method w.r.to verical
        # scrollbar
        verscrlbar.pack(fill='x')

        # Configuring treeview
        # treev.configure(xscrollcommand=verscrlbar.set)

        # Defining number of columns
        # self.treev["columns"] = (df.columns.values)

        print('heading')

        self.read_database()

        button1 = ttk.Button(self, text="Back to setup",
                             command=lambda: controller.show_frame(setupPage))
        button1.pack()
        self.update_item()

    def update_item(self):
        """ Check if database already exists in treev """
        self.read_database()
        self.after(1000, self.update_item)

    def read_database(self):
        print('database packet')
        coll = Database.find("packets", {})
        self.df = pd.DataFrame(coll)

        # print(df)
        if not self.df.empty:
            if self.heading_set == 0:

                # Defining number of columns
                self.treev["columns"] = (self.df.columns.values)
                # Defining heading
                self.treev['show'] = 'headings'

                for x in range(len(self.df.columns.values)):
                    if x == 1:
                        self.treev.column(x, width=200)
                    elif x == 7:
                        self.treev.column(x, width=150)
                    else:
                        self.treev.column(x, width=70)
                    self.treev.heading(x, text=self.df.columns.values[x])
                self.heading_set = 1

            for i in range(len(self.df)):
                """ check if item already exists in treev """
                id = self.df.iloc[i, :].tolist()[0]
                if self.in_treeview(str(id)) == 0:
                    self.treev.insert('', 'end', text="L"+str(i),
                                      values=(self.df.iloc[i, :].tolist()))

    def in_treeview(self, id):
        for item in self.treev.get_children():
            # print(self.treev.item(item)['values'][0])
            # print(self.df.iloc[i, :].tolist()[0])
            value = self.treev.item(item)['values'][0]
            if value == id:
                print('item in treeview')
                return 1
        return 0


class setupPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        tk.Label(
            self, text="Setup connection to the WSN!", font=LARGE_FONT).grid(row=0, column=600)
        # label.pack(pady=10, padx=10)

        entries = []

        label_host = tk.Label(
            self, text="Host", font=LARGE_FONT)
        label_host.grid(row=50, column=1)
        host = tk.Entry(self)
        host.grid(row=50, column=2)

        entries.append((label_host, host))

        label_port = tk.Label(
            self, text="Port", font=LARGE_FONT)
        label_port.grid(row=51, column=1)
        port = tk.Entry(self)
        port.grid(row=51, column=2)

        entries.append((label_port, port))

        self.host = HOST
        self.port = PORT

        if host.get() != '':
            self.host = host.get()
        if port.get() != '':
            self.port = port.get()

        host.delete(0, tk.END)
        host.insert(0, self.host)
        port.delete(0, tk.END)
        port.insert(0, self.port)
        # print(entries)
        # host.pack(pady=5, padx=10)

        # connect = ttk.Button(self, text="Connect",
        #                       command=(lambda e=entries: self.fetch(e))).grid(row=52, column=2)
        ttk.Button(self, text="Connect",
                   command=lambda: self.connect(self.host, self.port)).grid(row=52, column=2)

        ttk.Button(self, text="Back to Home",
                   command=lambda: controller.show_frame(StartPage)).grid(row=101, column=1)

        ttk.Button(self, text="Main page",
                   command=lambda: controller.show_frame(MainPage)).grid(row=101, column=3)

    def connect(self, host, port):
        """ Start the serial interface """
        print(host)
        print(port)
        serial = SerialBus(host, port)
        if serial.connect() == 1:
            print('connection succesful')
            popupmsg('connection succesful')
            # controller.show_frame(MainPage)
        else:
            print('connection unsuccesful')
            popupmsg('connection unsuccesful')

    def fetch(self, entries):
        # print(entries)
        for entry in entries:
            field = entry[0].cget("text")
            text = entry[1].get()
            print('%s: "%s"' % (field, text))

        # button1.pack()

        # host_label = tk.Label(self, text="Host", font=LARGE_FONT)
        # host_label.pack(pady=10, padx=10)

        # host = tk.Entry(self)
        # host.pack(pady=5, padx=10)

        # canvas = FigureCanvasTkAgg(f, self)
        # canvas.draw()
        # canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # toolbar = NavigationToolbar2Tk(canvas, self)
        # toolbar.update()
        # canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
