import config
# from controller.serial import SerialBus
from controller.serial.serial import SerialBus
from controller.database.database import Database
from controller.message import Message
from controller.node import Node
from datetime import datetime
import socket

# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja


def process_nodes(msg):
    addr0 = str(msg.addr0)
    addr1 = str(msg.addr1)
    addr = addr0+'.'+addr1
    # print(addr)
    data = msg.data
    # print(data)
    energy = data[0:2]
    energy = socket.htons(int(energy.hex(), 16))
    # print(energy)
    rank = data[2]
    prev_ranks = data[3]
    next_ranks = data[4]
    total_ranks = data[5]
    total_nb = data[6]
    alive = data[7]
    # nodes = Node(addr=addr, energy=energy, rank=rank, prev_ranks=prev_ranks,
    #  next_ranks=next_ranks, total_ranks=total_ranks, total_nb=total_nb, alive=alive)
    # nodes.print_packet()
    data = {
        'time': datetime.now(),
        'energy': energy,
        'rank': rank,
        'prev_ranks': prev_ranks,
        'next_ranks': next_ranks,
        'total_ranks': total_ranks,
        'total_nb': total_nb,
        'alive': alive,
    }
    node = {
        '_id': addr,
        'data': [
            data,
        ]
    }
    if Database.exist("nodes", addr) == 0:
        Database.insert("nodes", node)
    else:
        Database.push_doc("nodes", addr, data)
    Database.print_documents("nodes")
    # Database.list_collections()
    # node = {
    #     '_id': addr,
    #     'energy': msg.,
    #     'rank': rank
    # }


def handle_serial(msg):
    msg.print_packet()
    if(msg.message_type == 2):
        print("nodes' info")
        process_nodes(msg)


if __name__ == '__main__':
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
    # a = Database.find_one("example", user)
    # print(a)
    """ Start the serial interface """
    serial = SerialBus('localhost', 60001)
    msg = Message()
    serial.connect()
    try:
        # send a message
        # message = Message(addr0=1, addr1=0x7D, message_type=5,
        #                   payload_len=3, reserved0=5, reserved1=9, data=[0x55, 0x7E, 0x33])
        # serial.send(message)
        while True:
            msg = serial.recv(0.1)
            if msg is not None:
                print('msg')
                print(msg.addr1)
                print(msg)
                handle_serial(msg)

    except KeyboardInterrupt:
        pass  # exit normally
