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


logger = logging.getLogger('main.'+__name__)


class GUIController(BaseController):
    def __init__(
        self,
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
        """
        This controller is intended to run  along COOJA using the GUI.

        Args:
            socket (SinkComm object, optional): Serial connection to the sink. Defaults to None.
            db (Database object, optional): Database. Defaults to None.
            reward_processing (RewardProcessing object, optional):Reward processing for RL. Defaults to None.
            packet_dissector (Dissector object, optional): Packet dissector. Defaults to None.
            processing_window (int, optional): Number of packets for a new cycle. Defaults to 200.
            router (Router object, optional): Centralized routing algorithm. Defaults to None.
            tsch_scheduler (Scheduler object, optional): Centralized TSCH scheduler. Defaults to None.
        """

        logger.info("Building GUI controller")

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

    def start(self):
        # Get the simulation running
        super().start()

    def stop(self):
        super().stop()

    def reset(self):
        logger.info('Resetting controller, etc.')
        self.stop()
        self.start()
