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

from sdwsn_controller.controller.base_controller import BaseController

from time import sleep


logger = logging.getLogger(f'main.{__name__}')


class USBController(BaseController):
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

        logger.info("Building USB controller")

        super().__init__(
            config
        )

    # Controller related functions

    def timeout(self):
        sleep(0.02)

    def start(self):
        # Get the simulation running
        super().start()

    def stop(self):
        super().stop()

    def reset(self):
        # logger.info('Resetting controller, etc.')
        self.stop()
        self.start()
