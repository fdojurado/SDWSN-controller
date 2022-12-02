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

from sdwsn_controller.neighbors.neighbor import NeighborTable
from sdwsn_controller.routing.route import RoutingTable
from sdwsn_controller.tsch.schedule import TSCHScheduleTable

logger = logging.getLogger('main.'+__name__)


class Node():
    def __init__(
        self,
        id
    ) -> None:
        assert isinstance(id, int), "node ID must be a integer"
        assert id > 0, "node ID must be positive"
        self.id = id
        self.sid = str(id)
        self.neighbors = NeighborTable(self)
        self.tsch_schedules = TSCHScheduleTable(self)
        self.routes = RoutingTable(self)
        self.reset_stats()

    def reset_stats(self):
        self.tsch_pkt_sent = 0
        self.routing_pkt_sent = 0
        self.na_rcv = 0
