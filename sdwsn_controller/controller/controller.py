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

import logging

import os

from rich.progress import Progress

from sdwsn_controller.controller.base_controller import BaseController
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

from time import sleep


logger = logging.getLogger(f'main.{__name__}')


class Controller(BaseController):
    def __init__(
        self,
        config
    ):
        """
        This controller is intended to run run Cooja natively and without GUI.

        Args:
            contiki_source (str, optional): Path to the Contiki-NG source folder. Defaults to '/Users/fernando/contiki-ng'.
            simulation_folder (str, optional): Folder where the .csc file resides. Defaults to 'examples/elise'.
            simulation_script (str, optional): The .csc file to run. Defaults to 'cooja-elise.csc'.
            socket (SinkComm object, optional): Serial connection to the sink. Defaults to None.
            db (Database object, optional): Database. Defaults to None.
            reward_processing (RewardProcessing object, optional):Reward processing for RL. Defaults to None.
            packet_dissector (Dissector object, optional): Packet dissector. Defaults to None.
            processing_window (int, optional): Number of packets for a new cycle. Defaults to 200.
            routing (Router object, optional): Centralized routing algorithm. Defaults to None.
            tsch_scheduler (Scheduler object, optional): Centralized TSCH scheduler. Defaults to None.
        """

        # self.config = config

        # assert isinstance(contiki_source, str)
        # assert isinstance(simulation_folder, str)
        # assert isinstance(simulation_script, str)

        logger.info("Building native controller")

        # Controller related variables
        self.__proc = None

        self.__contiki_source = config.contiki.source
        self.__cooja_log = os.path.join(
            self.__contiki_source, config.contiki.script_folder, 'COOJA.log')
        self.__testlog = os.path.join(
            self.__contiki_source, config.contiki.script_folder, 'COOJA.testlog')
        self.__simulation_folder = os.path.join(
            self.__contiki_source, config.contiki.script_folder)
        self.__cooja_path = os.path.normpath(
            os.path.join(self.__contiki_source, "tools", "cooja"))
        self.__simulation_script = os.path.join(
            self.__contiki_source, config.contiki.script_folder, config.contiki.simulation_script)

        self.__new_simulation_script = None

        self.__port = config.contiki.port

        logger.info(f"Contiki source: {self.__contiki_source}")
        logger.info(f"Cooja log: {self.__cooja_log}")
        logger.info(f"Cooja test log: {self.__testlog}")
        logger.info(f"Cooja path: {self.__cooja_path}")
        logger.info(f"Simulation folder: {self.__simulation_folder}")
        logger.info(f"Simulation script: {self.__simulation_script}")

        super().__init__(
            config
        )

    # Controller related functions

    def timeout(self):
        sleep(0.02)

    def start_cooja(self):
        # cleanup
        try:
            os.remove(self.__testlog)
        except FileNotFoundError:
            pass
        except PermissionError as ex:
            logger.error("Cannot remove previous Cooja output:", ex)
            return False

        try:
            os.remove(self.__cooja_log)
        except FileNotFoundError:
            pass
        except PermissionError as ex:
            logger.error("Cannot remove previous Cooja log:", ex)
            return False

        # We need to overwrite the port of the serial socket in the
        # csc simulation file
        with open(self.__simulation_script, "r") as input_file:
            self.__new_simulation_script = self.__simulation_script.split('.')
            self.__new_simulation_script = "".join(
                [self.__new_simulation_script[0], "-temp.csc"])
            filedata = input_file.read()
            # Replace the target string
            filedata = filedata.replace(str(60001), str(self.__port))
            with open(self.__new_simulation_script, "w") as new_tmp_file:
                new_tmp_file.write(filedata)

        args = " ".join(["cd", self.__cooja_path, "&&", "exec ./gradlew run --args='-nogui=" +
                         self.__new_simulation_script, "-contiki=" + self.__contiki_source+" -logdir=" +
                         self.__simulation_folder+" -logname=COOJA"+"'"])

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
            raise Exception("Failed to start Cooja.")

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
                str(self.__port)
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
                if cooja_socket_active:
                    status = 1
                    progress.update(task1, completed=300)

                sleep(1)

        if status == 0:
            raise Exception("Failed to start the simulation.")

        logger.info("Cooja socket interface is up and running")

    def start(self):
        # Get the simulation running
        self.start_cooja()
        super().start()

    def stop(self):
        if self.__proc:
            try:
                self.__proc.communicate(timeout=15)
            except TimeoutExpired:
                self.__proc.kill()
                self.__proc.communicate()
        # Delete the tmp simulation csc file if exists
        if self.__new_simulation_script is not None:
            if os.path.exists(self.__new_simulation_script):
                os.remove(self.__new_simulation_script)
        # Delete COOJA.log and COOJA.testlog
        if os.path.exists(self.__cooja_log):
            os.remove(self.__cooja_log)
        if os.path.exists(self.__testlog):
            os.remove(self.__testlog)
        super().stop()

    def reset(self):
        # logger.info('Resetting controller, etc.')
        self.stop()
        self.start()
