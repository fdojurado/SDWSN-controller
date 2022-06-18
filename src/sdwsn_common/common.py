""" This python script holds common functions used across the controller """
import multiprocessing as mp
from sdwsn_serial import serial

# Function to connect to a specific host and port




# Function to get data from multiprocessing queue
def mqueue_empty(queue):
    empty = queue.empty()
    # print(f"empty: {empty}")
    return empty
def get_data_from_mqueue(queue):
    return queue.get()
