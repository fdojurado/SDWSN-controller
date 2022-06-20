import sys
import argparse
import multiprocessing as mp
from time import sleep

from sdwsn_common import common
from sdwsn_packet import packet_dissector
from sdwsn_serial.serial import SerialBus
from sdwsn_controller.controller import Controller
from sdwsn_database.database import Database
from sdwsn_reinforcement_learning.reinforcement_learning import ReinforcementLearning
from sdwsn_reinforcement_learning.env import Env
from sdwsn_reinforcement_learning.wrappers import TimeLimitWrapper
from stable_baselines3 import DQN


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--dbPort', type=int, default=27017,
                        help='Database port')
    parser.add_argument('-tmc', '--tschmaxchannel', type=int, default=3,
                        help='Maximum TSCH channel offset')
    parser.add_argument('-tsfs', '--tschmaxslotframe', type=int, default=100,
                        help='Maximum TSCH slotframe size')

    args = parser.parse_args()

    print(args)

    # Initialize global variables
    # globals.globals_initialize()

    # Create a serial interface instance
    serial_interface = SerialBus(args.socket, args.port)
    # Create an instance of the Database
    myDB = Database('mySDN', args.db, args.dbPort)
    # Create an instance of the packet dissector
    myPacketDissector = packet_dissector.PacketDissector(
        'MyDissector', myDB, None, None)
    # Create an instance of the controller
    controller = Controller(serial_interface=serial_interface,
                            database=myDB, packet_dissector=myPacketDissector)
    # Start the serial interface
    serial = controller.serial_start()
    if not serial:
        sys.exit(1)
    # Add it to the controller
    # controller.db = myDB
    # # Create an instance of the packet dissector
    # myPacketDissector = packet_dissector.PacketDissector(
    #     'MyDissector', myDB, None, None)
    # # Add it to the controller
    # controller.packet_dissector = myPacketDissector

    # # Create an instance of the RL environment
    # env = Env(args.tschmaxchannel, args.tschmaxslotframe)
    # # Wrap the environment to limit the max steps per episode
    # env = TimeLimitWrapper(env, max_steps=200)
    # # Create an instance of the reinforcement learning module
    # drl = ReinforcementLearning(
    #     controller_input, controller_output, env=env, processing_window=200)
    # # Create an instance of the RL model to use
    # # model = DQN('MlpPolicy', env, verbose=1, learning_starts=100,
    # #             target_update_interval=8, exploration_fraction=0.2)
    # # # Add it to the RL instance
    # # drl.model = model

    # # Start the controller
    # controller.daemon = True
    # controller.start()
    # # Start the RL module
    # drl.daemon = True
    # drl.start()

    while True:
        sleep(0.1)


if __name__ == '__main__':
    main()
    sys.exit(0)
