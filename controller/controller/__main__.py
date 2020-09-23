import config
# from controller.serial import SerialBus
from controller.serial.serial import SerialBus

# Cooja address and port
HOST = 'localhost'  # Assuming cooja running locally
PORT = 60001        # The port used by cooja

if __name__ == '__main__':
    """ Start the serial interface """
    serial = SerialBus('localhost',60001)
    serial.connect()
