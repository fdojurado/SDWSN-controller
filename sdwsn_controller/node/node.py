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

from sdwsn_controller.neighbors.neighbor import NeighborTable, Neighbor
from sdwsn_controller.performance_metrics.energy import EnergySamples
from sdwsn_controller.performance_metrics.delay import DelaySamples
from sdwsn_controller.performance_metrics.pdr import PDRSamples
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
        self.energy = EnergySamples(self)
        self.delay = DelaySamples(self)
        self.pdr = PDRSamples(self)
        self.rank = 255
        self.reset_stats()

    # ---------------------------------------------------------------------------

    def neighbors_get(self):
        return self.neighbors.neighbors

    def neighbor_add(self, neighbor_id, rssi, etx) -> Neighbor:
        return self.neighbors.add_neighbor(
            neighbor_id=neighbor_id, rssi=rssi, etx=etx)

    def neighbor_print(self):
        self.neighbors.print()

    def neighbors_len(self):
        return self.neighbors.size()

    # ---------------------------------------------------------------------------

    def energy_add(self, cycle_seq, seq, energy):
        energy = self.energy.add_sample(
            cycle_seq=cycle_seq, seq=seq, energy=energy)
        return energy

    def energy_print(self, cycle_seq=None):
        self.energy.print(cycle_seq)

    def energy_get_last(self, cycle_sequence):
        return self.energy.get_sample_last(cycle_sequence)

    # ---------------------------------------------------------------------------

    def delay_add(self, cycle_seq, seq, delay):
        delay = self.delay.add_sample(
            cycle_seq=cycle_seq, seq=seq, delay=delay)
        return delay

    def delay_print(self, cycle_seq=None):
        self.delay.print(cycle_seq)

    def delay_get_average(self, cycle_sequence):
        return self.delay.get_average(cycle_sequence)

    # ---------------------------------------------------------------------------

    def pdr_add(self, cycle_seq, seq):
        delay = self.pdr.add_sample(
            cycle_seq=cycle_seq, seq=seq)
        return delay

    def pdr_print(self, cycle_seq=None):
        self.pdr.print(cycle_seq)

    def pdr_get_average(self, cycle_sequence):
        return self.pdr.get_average(cycle_sequence)

    # ---------------------------------------------------------------------------

    def route_add(self, dst_id, nexthop_id):
        return self.routes.add_route(destination_id=dst_id, nexthop_id=nexthop_id)

    def route_print(self):
        self.routes.print()

    def route_clear(self):
        self.routes.clear()

    def routes_get(self):
        return self.routes.routes

    # ---------------------------------------------------------------------------

    def tsch_print(self):
        self.tsch_schedules.print()

    def tsch_add_link(self, schedule_type, ch, ts, dst=None):
        self.tsch_schedules.add_tsch_schedule(
            schedule_type=schedule_type, ch=ch, ts=ts, dst=dst)

    def tsch_get(self):
        return self.tsch_schedules.tsch_schedules

    def tsch_last_ts(self):
        return self.tsch_schedules.last_ts

    def tsch_last_ch(self):
        return self.tsch_schedules.last_ch

    def tsch_link_exists(self, dst_id):
        return self.tsch_schedules.get_destination(dst_id=dst_id)

    def tsch_timeslot_free(self, ts) -> bool:
        return self.tsch_schedules.timeslot_free(ts)

    def tsch_clear(self):
        self.tsch_schedules.clear()

    # ---------------------------------------------------------------------------

    def clear(self):
        self.neighbors.clear()
        self.tsch_schedules.clear()
        self.routes.clear()
        self.energy.clear()
        self.delay.clear()
        self.pdr.clear()

    def reset_stats(self):
        self.tsch_pkt_sent = 0
        self.routing_pkt_sent = 0
        self.na_rcv = 0
