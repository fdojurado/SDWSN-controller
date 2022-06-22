import threading
from time import sleep
from sdwsn_common import common
from threading import Thread
from abc import ABC, abstractmethod
from sdwsn_serial.serial import SerialBus
from sdwsn_database.database import Database
from sdwsn_packet.packet_dissector import PacketDissector


class BaseController(ABC):
    def __init__(
            self,
            serial_interface=type[SerialBus],
            packet_dissector=type[PacketDissector]
    ):
        # Save instance of a serial interface
        self.ser = serial_interface
        # Save instance of packet dissector
        self.packet_dissector = packet_dissector
        # Variable to check whether the controller is running or not
        self.is_running = False

    def controller_start(self):
        # Initialize database
        self.packet_dissector.initialise_db()
        # Start the serial interface
        self.__controller_serial_start()
        # Restart variables at packet dissector
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # Set running flag
        self.is_running = True

    def controller_stop(self):
        # Clear the running flag
        self.is_running = False
        # Stop the serial interface
        self.controller_serial_stop()
        # Reset the packet dissector sequence
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0

    def controller_serial_stop(self):
        self.ser.shutdown()

    def __controller_serial_start(self):
        # Connect serial
        if self.ser.connect() != 0:
            print('unsuccessful serial connection')
            return 0
        # Read serial
        self._read_ser_thread = threading.Thread(target=self.__read_ser)
        self._read_ser_thread.start()
        return 1

    def controller_send_data(self, data):
        if self.is_running:
            print("sending serial packet")
            # Send data to the serial send interface
            self.ser.send(data)
        else:
            print("Couldn't send data, controller is Not running")

    def controller_reliable_send(self, data, ack):
        # Reliable data transmission
        # set retransmission
        rtx = 0
        # Send NC packet through serial interface
        self.controller_send_data(data)
        # Result variable to see if the sending went well
        result = 0
        while True:
            if (self.packet_dissector.ack_pkt.reserved0 == ack):
                print("correct ACK received")
                result = 1
                break
            print("ACK not received")
            # We stop sending the current NC packet if
            # we reached the max RTx or we received ACK
            if(rtx >= 7):
                print("ACK never received")
                break
            # We resend the packet if retransmission < 7
            rtx = rtx + 1
            self.controller_send_data(data)
            sleep(1.2)
        return result

    def __read_ser(self):
        while(1):
            try:
                msg = self.ser.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
                if not self.is_running:
                    break
            except TypeError:
                pass
