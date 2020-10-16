import config
# from controller.serial import SerialBus
from controller.serial.serial import SerialBus
from controller.database.database import Database
from controller.gui.gui import SDNcontrollerapp, f, animate
from controller.message import Message
from controller.node import Node
import socket
import tkinter as tk
import pandas as pd
import matplotlib.animation as animation


# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja


if __name__ == '__main__':
    # root = tk.Tk()
    # MainApplication(root).pack(side="top", fill="both", expand=True)
    # root = Tk()
    """ Initialise database """
    Database.initialise()
    # name = "daniel"
    # user = {
    #     'name': name,
    #     'age': 23,
    #     'blog': [
    #         {'neighbors': 5,
    #          'ranks': 4},
    #         {'neighbors': 8,
    #          'ranks': 7}
    #     ]
    # }

    # a = Database.insert("example", user)
    # print(a)
    Database.print_documents("nodes")
    Database.list_collections()
    """ Initialise GUI """
    app = SDNcontrollerapp()
    app.geometry("1280x720")
    ani = animation.FuncAnimation(f, animate, interval=5000)
    app.mainloop()

