""" This python script holds common functions used across the controller """
import multiprocessing as mp
from sdwsn_serial import serial

# Function to connect to a specific host and port
def socket_connect(host, port, send, rcv):
    print(f'socket connection to {host} and port {port}')
    return serial.SerialBus(host, port, send, rcv)

# Function to get data from multiprocessing queue
def get_data_from_mqueue(queue):
    return queue.get()