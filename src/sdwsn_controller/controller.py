import threading
from time import sleep
from sdwsn_common import common
from threading import Thread


class Controller():
    def __init__(self, serial_interface=None, network_reconfiguration=None, database=None, packet_dissector=None):
        # Save instance of a serial interface
        self.serial = serial_interface
        # Save instance of the network reconfiguration module
        self.network_reconfiguration = network_reconfiguration
        # Save instance of the Database
        self.db = database
        # Initialize DB
        self.db.initialise()
        # Save instance of packet dissector
        self.packet_dissector = packet_dissector

    def serial_start(self):
        # Connect serial
        if self.serial.connect() != 0:
            print('unsuccessful serial connection')
            return 0
        # Read serial
        self._read_ser_thread = threading.Thread(target=self._read_ser)
        self._read_ser_thread.start()
        return 1

    def _read_ser(self):
        while(1):
            try:
                msg = self.serial.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
            except TypeError:
                pass

    def run(self):
        print(f'controller running')
        # Initialize the database
        if self.db is None:
            return
        self.db.initialise()
        # initialize the serial interface
        if self.serial is not None:
            if self.serial.connect() != 0:
                print("error initializing serial")
                return 0

            else:
                print('serial connection successful')
        else:
            print('error initializing serial')
            return 0
        # Start the serial interface
        serial_thread = Thread(target=self.serial.read)
        serial_thread.daemon = True
        serial_thread.start()

        while(1):
            # Anything in serial?
            if self.serial.msg is not None:
                # handle serial packet
                self.packet_dissector.handle_serial_packet(
                    self.serial.msg)
                self.serial.msg = None
