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
from sdwsn_controller.tsch.scheduler import TSCHScheduler
from sdwsn_controller.tsch.schedule import cell_type
import logging

logger = logging.getLogger(f'main.{__name__}')


class HardCodedScheduler(TSCHScheduler):
    def __init__(
            self,
            network
    ):
        self.__name = "Hard Coded Scheduler"
        super().__init__(
            network=network
        )

    @property
    def name(self):
        return self.__name

    def add_link(self, tx_id, rx_id, ch, ts):
        tx_node = self.network.nodes_add(tx_id)
        rx_node = self.network.nodes_add(rx_id)
        tx_node.tsch_add_link(cell_type.UC_TX, ch, ts, rx_node.id)
        rx_node.tsch_add_link(cell_type.UC_RX, ch, ts)

    def run(self, path, current_sf_size):
        logger.debug(
            f"running hard coded scheduler for sf size {current_sf_size}")
        # Set the slotframe size
        self.network.tsch_clear()
        self.network.tsch_slotframe_size = current_sf_size
        # Schedule Tx - Node 2 - 1
        self.add_link(2, 1, 1, 1)
        # Schedule Tx - Node 3 - 1
        self.add_link(3, 1, 1, 2)
        # Schedule Tx - Node 4 - 1
        self.add_link(4, 1, 1, 3)
        # Schedule Tx - Node 5 - 2
        self.add_link(5, 2, 1, 4)
        # Schedule Tx - Node 6 - 3
        self.add_link(6, 3, 1, 5)
        # Schedule Tx - Node 7 - 4
        self.add_link(7, 4, 1, 6)
        # Schedule Tx - Node 8 - 5
        self.add_link(8, 5, 1, 7)
        # Schedule Tx - Node 9 - 6
        self.add_link(9, 6, 1, 8)
        # Schedule Tx - Node 10 - 7
        self.add_link(10, 7, 1, 9)

        # Print the schedule
        self.network.tsch_print()
