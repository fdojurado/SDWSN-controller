import config
# from controller.serial import SerialBus
from controller.serial.serial import SerialBus
from controller.message import Message

# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja

if __name__ == '__main__':
    """ Start the serial interface """
    serial = SerialBus('localhost', 60001)
    msg = Message()
    # serial.connect()
    try:
        while True:
            msg = serial.recv(1)
            if msg is not None:
                print('msg')
                print(msg.addr1)

    except KeyboardInterrupt:
        pass  # exit normally
