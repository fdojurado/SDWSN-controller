from controller.serial.serial import SerialBus

class NetworkConfig(object):

    def send_nc(self):
        print('Sending NC packet')
    
    def process_nc(self):
        print('Processing NC packet')

    def ack_nc(self):
        print('Processing NC ack')