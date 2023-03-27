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

# This file contains the up-to-date information of the routes currently
# deployed at the WSN.

from sdwsn_controller.common import common
from rich.table import Table
import logging

logger = logging.getLogger(f'main.{__name__}')


# ---------------------------------------------------------------------------
class Route():
    def __init__(
        self,
        dst_id,
        nexthop_id
    ) -> None:
        # assert isinstance(dst_id, str)
        # assert isinstance(nexthop_id, str)
        self.dst_id = dst_id
        self.nexthop_id = nexthop_id

    def is_direct(self) -> bool:
        return self.dst_id == self.nexthop_id

# ---------------------------------------------------------------------------


class RoutingTable():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.clear()

    def clear(self):
        self.routes = {}
        self.default_route = None

    def size(self):
        return len(self.routes)

    def get_route(self, destination_id):
        return self.routes.get(destination_id)

    def add_route(self, destination_id, nexthop_id) -> Route:
        if self.routes.get(destination_id):
            return
        logger.debug(
            f'Node {self.node.id}: add route to {destination_id} via {nexthop_id}')
        route = Route(dst_id=destination_id, nexthop_id=nexthop_id)
        self.routes.update({destination_id: route})
        return route

    def remove_route(self, destination_id):
        logger.debug(f"Node {self.node.id}: remove route to {destination_id}")
        if destination_id in self.routes:
            del self.routes[destination_id]

    def add_default_route(self):
        pass

    def remove_default_route(self):
        pass

    def lookup_route(self, destination_id):
        if destination_id in self.routes:
            return self.routes.get(destination_id)

    def get_nexthop(self, destination_id):
        if destination_id == self.node.id:
            return destination_id
        route = self.lookup_route(destination_id)
        if route is None:
            logger.debug(
                f"Node {self.node.id}: no nexthop for {destination_id}")
        return route.nexthop_id if route is not None else None

    def print(self):
        table = Table(title="Routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for key in self.routes:
            route = self.routes.get(key)
            table.add_row(str(self.node.id), str(
                route.dst_id), str(route.nexthop_id))

        logger.info(f"Routing table\n{common.log_table(table)}")
