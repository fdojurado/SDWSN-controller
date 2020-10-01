import config
# from controller.serial import SerialBus
from controller.serial.serial import SerialBus
from controller.database.database import Database
from controller.message import Message

# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja

if __name__ == '__main__':
    """ Initialise database """
    Database.initialise()
    name = "daniel"
    user = {
        'name': name,
        'age': 23,
        'blog': [
            {'neighbors': 5,
             'ranks': 4},
            {'neighbors': 8,
             'ranks': 7}
        ]
    }

    a = Database.insert("example", user)
    # print(a)
    Database.list_collections()
    a = Database.find_one("example", user)
    print(a)
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
                msg.print_packet()

    except KeyboardInterrupt:
        pass  # exit normally
