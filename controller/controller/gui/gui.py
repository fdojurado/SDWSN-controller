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

        for F in (StartPage, setup_page):

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
                             command=lambda: controller.show_frame(setup_page))
        button1.pack()

        button2 = ttk.Button(self, text="Disagree",
                             command=quit)
        button2.pack()


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page One!!!", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()


class setup_page(tk.Frame):

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

        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage)).grid(row=101, column=1)

    def connect(self, host, port):
        """ Start the serial interface """
        print(host)
        print(port)
        serial = SerialBus(host, port)
        serial.connect()

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
