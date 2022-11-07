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
from subprocess import Popen, PIPE, STDOUT

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
        socket: object = None,
        # Database
        db: object = None,
        # RL related
        reward_processing: object = None,
        # Packet dissector
        packet_dissector: object = None,
        # Window
        processing_window: int = 200,
        # Routing
        router: object = None,
        # TSCH scheduler
        tsch_scheduler: object = None
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

        super().__init__(
            socket=socket,
            db=db,
            reward_processing=reward_processing,
            packet_dissector=packet_dissector,
            processing_window=processing_window,
            router=router,
            tsch_scheduler=tsch_scheduler
        )

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
