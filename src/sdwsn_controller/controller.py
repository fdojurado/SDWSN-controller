import imp
import multiprocessing as mp
from time import sleep
from sdwsn_common import common
from threading import Thread


class Controller(mp.Process):
    def __init__(self, input_queue=mp.Queue(), output_queue=mp.Queue(), serial_interface=None, network_reconfiguration=None, database=None, packet_dissector=None):
        mp.Process.__init__(self)
        # Save instance of a serial interface
        self.serial = serial_interface
        # Save instance of the network reconfiguration module
        self.network_reconfiguration = network_reconfiguration
        # Save instance of the Database
        self.db = database
        # Save instance of packet dissector
        self.packet_dissector = packet_dissector
        # Set queues
        self.input_queue = input_queue
        self.output_queue = output_queue

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
