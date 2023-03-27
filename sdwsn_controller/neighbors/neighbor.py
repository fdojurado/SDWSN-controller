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

from rich.table import Table

from sdwsn_controller.common import common


logger = logging.getLogger(f'main.{__name__}')


class Neighbor():
    def __init__(
        self,
        neighbor_id,
        rssi,
        etx
    ) -> None:
        assert isinstance(neighbor_id, int)
        assert isinstance(rssi, int)
        assert isinstance(etx, int)
        self.neighbor_id = neighbor_id
        self.rssi = rssi
        self.etx = etx


class NeighborTable():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.clear()

    def clear(self):
        self.neighbors = {}

    def size(self) -> int:
        return len(self.neighbors)

    def get_neighbor(self, neighbor_id) -> Neighbor:
        self.neighbors.get(neighbor_id)

    def add_neighbor(self, neighbor_id, rssi, etx) -> Neighbor:
        nbr = self.neighbors.get(neighbor_id)
        if nbr is not None:
            logger.debug(
                f"Neighbor ID {neighbor_id} already exists. Updating RSSI and ETX.")
            nbr.rssi = rssi
            nbr.etx = etx
            return nbr
        logger.debug(
            f'Node {self.node.id}: add neighbor to {neighbor_id} ({rssi}, {etx})')
        nbr = Neighbor(neighbor_id=neighbor_id, rssi=rssi, etx=etx)
        self.neighbors.update({neighbor_id: nbr})
        return nbr

    def lookup_neighbor(self, neighbor_id) -> Neighbor:
        if neighbor_id in self.neighbors:
            return self.neighbors.get(neighbor_id)

    def print(self):
        table = Table(title=f"Neighbor table for node: {self.node.id}")

        table.add_column("Neighbor", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("RSSI", justify="center", style="magenta")
        table.add_column("ETX", justify="center", style="magenta")
        for key in self.neighbors:
            neighbor = self.neighbors.get(key)
            table.add_row(str(neighbor.neighbor_id),
                          str(neighbor.rssi), str(neighbor.etx))

        logger.debug(f"Neighbor table\n{common.log_table(table)}")
