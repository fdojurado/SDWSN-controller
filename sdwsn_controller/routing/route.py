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
from abc import ABC, abstractmethod
from rich.table import Table
import pandas as pd
import logging

logger = logging.getLogger('main.'+__name__)


# ---------------------------------------------------------------------------
class Route():
    def __init__(
        self,
        dst_id: str = None,
        nexthop_id: str = None
    ) -> None:
        assert isinstance(dst_id, str)
        assert isinstance(nexthop_id, str)
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
        self.routes.get(destination_id)

    def add_route(self, destination_id, nexthop_id) -> Route:
        if self.routes.get(destination_id):
            return
        logger.debug(
            f'Node {self.node.id}: add route to {destination_id} via {nexthop_id}')
        route = Route(dst_id=destination_id, nexthop_id=nexthop_id)
        self.routes.update(destination_id, route)
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
            logger.debug(f"Node {self.node.id}: no nexthop for {destination_id}")
        return route.nexthop_id if route is not None else None

    def print_routes(self):
        table = Table(title="Routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for key in self.routes:
            route = self.routes.get(key)
            table.add_row(self.node.id, route.dst_id, route.nexthop_id)

        logger.info(f"Routing table\n{common.log_table(table)}")


# ---------------------------------------------------------------------------


class Router(ABC):
    """
    This is the base class for the routing.
    The routes are stored in a pandas DataFrame. This may not be
    the best way to do this, but for now it is working good.
    """

    def __init__(
        self
    ):
        self.column_names = ['scr', 'dst', 'via']
        self.__routes = pd.DataFrame(columns=self.column_names)

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @property
    def router_routes(self):
        return self.__routes

    @router_routes.setter
    def router_routes(self, val):
        self.__routes = val

    def router_add_route(self, scr, dst, via):
        """
        This adds a route to the current routing paths.
        This checks whether the route currently exist in the routing table or not.
        If it does then it simply returns; otherwise it adds the route to the routing
        table.
        TODO: Maybe remove the route verification and leave this task to the routing
        algorithm?

        Args:
            scr (str): The address of the source node.
            dst (str): The address of the destination node.
            via (str): The address of the relaying node.
        """
        print(f"Router add route, scr:{scr}, dst:{dst}, via:{via}")
        # Let's first check if the route is already in the dataframe
        if ((self.router_routes['scr'] == scr) & (self.router_routes['dst'] == dst) &
                (self.router_routes['via'] == via)).any():
            return
        else:
            df = pd.DataFrame([[scr, dst, via]], columns=self.column_names)
            self.router_routes = pd.concat(
                [self.router_routes, df], ignore_index=True)  # adding a row

    def router_print(self):
        """
        It prints the routes as a pandas DataFrame.
        """
        logger.info(self.router_routes.to_string())

    def router_print_table(self):
        """
        Prints a nice table using Rich library.
        """
        table = Table(title="Routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for _, row in self.router_routes.iterrows():
            table.add_row(row['scr'],
                          row['dst'], row['via'])

        logger.info(f"Routing table\n{common.log_table(table)}")

    def router_remove_route(self, scr, dst, via):
        """
        It removes a single route from the routing table

        Args:
            scr (str): The address of the source node.
            dst (str): The address of the destination node.
            via (str): The address of the relaying node.
        """
        df = self.router_routes
        idx = df.index[df['scr'] == scr & df['dst']
                       == dst & df['via'] == via]
        # Check that the index is not empty. Which means we find the target row.
        if (idx.empty):
            logger.warning('route/index not found')
            return
        self.router_routes = df.drop(idx)
        self.print_routes()

    def router_clear_routes(self):
        """
        Clears all routes from the routing table
        """
        self.router_routes.drop(
            self.router_routes.index, inplace=True)
