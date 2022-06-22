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
from sdwsn_reinforcement_learning.wrappers import TimeLimitWrapper, SaveModelSaveBuffer
from stable_baselines3 import DQN
from sdwsn_network_reconfiguration.network_config import NetworkReconfig
from sdwsn_docker.docker import CoojaDocker
from stable_baselines3.common.callbacks import EveryNTimesteps


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

    mount = {
        'target': '/home/user/contiki-ng',
        'source': '/Users/fernando/contiki-ng',
        'type': 'bind'
    }
    sysctls = {
        'net.ipv6.conf.all.disable_ipv6': 0
    }

    # Simulation file to run
    cmd = '/bin/sh -c "cd examples/benchmarks/rl-sdwsn && ./run-cooja.py"'

    ports = {
        'container': 60001,
        'host': 60001
    }

    socket_file = '/Users/fernando/contiki-ng/examples/benchmarks/rl-sdwsn/COOJA.log'

    cooja_container = CoojaDocker(
        'contiker/contiki-ng', cmd, mount, sysctls, ports, socket_file=socket_file)

    # Callback to save the model and replay buffer every N steps.
    save_model_replay = SaveModelSaveBuffer(save_path='./logs/')
    event_callback = EveryNTimesteps(n_steps=50, callback=save_model_replay)

    # Create a serial interface instance
    serial_interface = SerialBus(args.socket, args.port)
    # Create an instance of the Database
    myDB = Database('mySDN', args.db, args.dbPort)
    # Create an instance of the packet dissector
    myPacketDissector = packet_dissector.PacketDissector(
        'MyDissector', myDB)
    # Create an instance of the network reconfiguration
    myNC = NetworkReconfig(serial_interface, myPacketDissector)

    # Create an instance of the RL environment
    env = Env(myPacketDissector, myNC, cooja_container, serial_interface,
              args.tschmaxchannel, args.tschmaxslotframe, processing_window=200)
    # Wrap the environment to limit the max steps per episode
    env = TimeLimitWrapper(env, cooja_container, myDB,
                           'example', max_steps=200)
    # Create an instance of the RL model to use
    model = DQN('MlpPolicy', env, verbose=1, learning_starts=100,
                target_update_interval=8, exploration_fraction=0.2)
    # Create an instance of the reinforcement learning module
    drl = ReinforcementLearning(serial_interface, myNC, myDB, myPacketDissector,
                                env=env, model=model, callback=event_callback, processing_window=200)

    saved_model = './logs/rl_model_250_steps'
    saved_buffer = './logs/rl_model_buffer_250_steps'

    # drl.exec()
    drl.continue_learning(saved_model, saved_buffer, env)


    # while True:
    #     sleep(0.1)
if __name__ == '__main__':
    main()
    sys.exit(0)
