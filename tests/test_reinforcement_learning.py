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
from sdwsn_network_reconfiguration.network_config import NetworkReconfig


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

    # Create a serial interface instance
    serial_interface = SerialBus(args.socket, args.port)
    # Create an instance of the Database
    myDB = Database('mySDN', args.db, args.dbPort)
    # Create an instance of the packet dissector
    myPacketDissector = packet_dissector.PacketDissector(
        'MyDissector', myDB)
    # Create an instance of the network reconfiguration
    myNC = NetworkReconfig()

    # Create an instance of the RL environment
    env = Env(args.tschmaxchannel, args.tschmaxslotframe)
    # Wrap the environment to limit the max steps per episode
    env = TimeLimitWrapper(env, max_steps=200)
    # Create an instance of the RL model to use
    model = DQN('MlpPolicy', env, verbose=1, learning_starts=100,
                target_update_interval=8, exploration_fraction=0.2)
    # Create an instance of the reinforcement learning module
    drl = ReinforcementLearning(serial_interface, myNC, myDB, myPacketDissector,
                                env=env, model=model, processing_window=200)

    drl.exec()

    while True:
        sleep(0.1)


if __name__ == '__main__':
    main()
    sys.exit(0)
