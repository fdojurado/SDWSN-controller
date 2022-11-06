#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from sdwsn_controller.controller.base_controller import BaseController
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.serial.serial import SerialBus
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from sdwsn_controller.routing.dijkstra import Dijkstra

from rich.progress import Progress
from time import sleep
import logging
import signal
import os


logger = logging.getLogger('main.'+__name__)


class Controller(BaseController):
    def __init__(
        self,
        # Controller related
        contiki_source: str = '/Users/fernando/contiki-ng',
        simulation_folder: str = 'examples/elise',
        simulation_script: str = 'cooja-elise.csc',
        # Sink/socket communication
        socket_address: str = '127.0.0.1',
        socket_port: int = 60001,
        # Database
        db_name: str = None,
        db_host: str = None,
        db_port: int = None,
        # Simulation
        simulation_name: str = 'mySimulation',
        # Window
        processing_window: int = 200,
        # Routing
        router: object = Dijkstra(),
        # TSCH scheduler
        tsch_scheduler: object = ContentionFreeScheduler(500, 3)
    ):

        logger.info("Building controller")

        # Controller related variables
        self.__proc = None

        self.__contiki_source = contiki_source
        self.__cooja_log = os.path.join(
            self.__contiki_source, simulation_folder, 'COOJA.log')
        self.__testlog = os.path.join(
            self.__contiki_source, simulation_folder, 'COOJA.testlog')
        self.__simulation_folder = os.path.join(
            self.__contiki_source, simulation_folder)
        self.__cooja_path = os.path.normpath(
            os.path.join(self.__contiki_source, "tools", "cooja"))
        self.__simulation_script = os.path.join(
            self.__contiki_source, simulation_folder, simulation_script)

        logger.info(f"Contiki source: {self.__contiki_source}")
        logger.info(f"Cooja log: {self.__cooja_log}")
        logger.info(f"Cooja test log: {self.__testlog}")
        logger.info(f"Cooja path: {self.__cooja_path}")
        logger.info(f"Simulation folder: {self.__simulation_folder}")
        logger.info(f"Simulation script: {self.__simulation_script}")
        logger.info(f'Socket address: {socket_address}')
        logger.info(f'Socket port: {socket_port}')

        # We only create a DB if this is explicitly pass to the class.
        # This is done to speed up the training in the numerical env.
        if db_name is not None and db_host is not None and db_port is not None:
            self.__db = DatabaseManager(
                name=db_name,
                host=db_host,
                port=db_port
            )
            logger.info(f'DB name: {db_name}')
            logger.info(f'DB host: {db_host}')
            logger.info(f'DB port: {db_port}')
        else:
            self.__db = None

        logger.info(f'simulation name: {simulation_name}')
        logger.info(f'Processing window: {processing_window}')

        # Create packet dissector
        self.__packet_dissector = PacketDissector(database=self.db)

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler

        # Create an instance of Router
        self.__router = router

        # Create a socket/sink communication
        self.__socket = SerialBus(socket_address, socket_port)

        # Processing window
        self.__processing_window = processing_window

        super().__init__()

     # Database
    @property
    def db(self):
        return self.__db

    # Packet dissector
    @property
    def packet_dissector(self):
        return self.__packet_dissector

    # TSCH scheduler
    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    # Routing
    @property
    def router(self):
        return self.__router

    # Serial Interface
    @property
    def socket(self):
        return self.__socket

    # Processing window
    @property
    def processing_window(self):
        return self.__processing_window

    @processing_window.setter
    def processing_window(self, val):
        self.__processing_window = val

    # Controller related functions

    def timeout(self):
        sleep(1.2)

    def start_cooja(self):
        # cleanup
        try:
            os.remove(self.__testlog)
        except FileNotFoundError as ex:
            pass
        except PermissionError as ex:
            print("Cannot remove previous Cooja output:", ex)
            return False

        try:
            os.remove(self.__cooja_log)
        except FileNotFoundError as ex:
            pass
        except PermissionError as ex:
            print("Cannot remove previous Cooja log:", ex)
            return False

        args = " ".join(["cd", self.__cooja_path, "&&", "./gradlew run --args='-nogui=" +
                         self.__simulation_script, "-contiki=" + self.__contiki_source+" -logdir="+self.__simulation_folder+" -logname=COOJA"+"'"])

        self.__proc = Popen(args, stdout=PIPE, stderr=STDOUT, stdin=PIPE,
                            shell=True, universal_newlines=True, preexec_fn=os.setsid)

        status = 0
        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Waiting for Cooja to start...", total=300)

            while not progress.finished:
                progress.update(task1, advance=1)
                if os.access(self.__cooja_log, os.R_OK):
                    status = 1
                    progress.update(task1, completed=300)
                sleep(1)

        if status == 0:
            raise Exception(f"Failed to start Cooja.")

        self.__wait_socket_running()

    def __cooja_socket_status(self):
        # This method checks whether the socket is currently running in Cooja
        if not os.access(self.__cooja_log, os.R_OK):
            logger.warning(
                'The input file "{}" does not exist'.format(self.__cooja_log))

        is_listening = False
        is_fatal = False

        with open(self.__cooja_log, "r") as f:
            contents = f.read()
            read_line = "Listening on port: " + \
                str(self.socket.port)
            fatal_line = "Simulation not loaded"
            is_listening = read_line in contents
            # logger.info(f'listening result: {is_listening}')
            is_fatal = fatal_line in contents
        return is_listening, is_fatal

    def __wait_socket_running(self):
        cooja_socket_active, fatal_error = self.__cooja_socket_status()
        status = 0
        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Setting up Cooja simulation...", total=300)
            while not progress.finished:
                progress.update(task1, advance=1)
                cooja_socket_active, fatal_error = self.__cooja_socket_status()
                if fatal_error:
                    logger.warning(
                        "Simulation compilation error, starting over ...")
                    self.start()
                if cooja_socket_active == True:
                    status = 1
                    progress.update(task1, completed=300)

                sleep(1)

        if status == 0:
            raise Exception(f"Failed to start the simulation.")

        logger.info("Cooja socket interface is up and running")

    def start(self):
        # Get the simulation running
        self.start_cooja()
        super().start()

    def stop(self):
        if self.__proc:
            os.killpg(os.getpgid(self.__proc.pid), signal.SIGTERM)
        super().stop()

    def reset(self):
        logger.info('Resetting controller, etc.')
        self.stop()
        self.start()
