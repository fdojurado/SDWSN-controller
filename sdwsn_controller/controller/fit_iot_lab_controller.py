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

from time import sleep

import logging

logger = logging.getLogger(f'main.{__name__}')


class FitIoTLABController(BaseController):
    def __init__(
        self,
        # Network
        network: object = None,
        # RL related
        reward_processing: object = None,
        # Routing
        routing: object = None,
        # TSCH scheduler
        tsch_scheduler: object = None
    ):

        logger.info("Building FIT IoT COntroller")

        super().__init__(
            reward_processing=reward_processing,
            routing=routing,
            network=network,
            tsch_scheduler=tsch_scheduler
        )

    def timeout(self):
        sleep(1.2)

    def set_timeout(self):
        self.network.timeout = 10

    def fit_iot_lab_start(self):
        sleep(10)
        self.set_timeout()
        logger.info(
            f'starting FIT IoT LAB controller with timeout \
                {self.network.timeout}')
        # Initialize main controller
        self.start()

    def fit_iot_lab_stop(self):
        logger.info('stopping FIT IoT LAB controller')
        # Stop main controller
        self.stop()

    def reset(self):
        logger.info('Resetting FIT IoT LAB controller')
        self.fit_iot_lab_stop()
        self.fit_iot_lab_start()
