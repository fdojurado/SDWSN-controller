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


class RoutingTable(ABC):
    """
    This is the base class for the routing.
    The routes are stored in a pandas DataFrame. This may not be
    the best way to do this, but for now it is working good.
    """

    def __init__(self):
        self.column_names = ['scr', 'dst', 'via']
        self.__routes = pd.DataFrame(columns=self.column_names)

    @abstractmethod
    def run(self):
        pass

    @property
    def routing_table_routes(self):
        return self.__routes

    @routing_table_routes.setter
    def routing_table_routes(self, val):
        self.__routes = val

    def routing_table_add_route(self, scr, dst, via):
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
        # Let's first check if the route is already in the dataframe
        if ((self.routing_table_routes['scr'] == scr) & (self.routing_table_routes['dst'] == dst) & (self.routing_table_routes['via'] == via)).any():
            return
        else:
            df = pd.DataFrame([[scr, dst, via]], columns=self.column_names)
            self.routing_table_routes = pd.concat(
                [self.routing_table_routes, df], ignore_index=True)  # adding a row

    def routing_table_print(self):
        """
        It prints the routes as a pandas DataFrame.
        """
        logger.info(self.routing_table_routes.to_string())

    def routing_table_print_table(self):
        """
        Prints a nice table using Rich library.
        """
        table = Table(title="Routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for _, row in self.routing_table_routes.iterrows():
            table.add_row(row['scr'],
                          row['dst'], row['via'])

        logger.info(f"Routing table\n{common.log_table(table)}")

    def routing_table_remove_route(self, scr, dst, via):
        """
        It removes a single route from the routing table

        Args:
            scr (str): The address of the source node.
            dst (str): The address of the destination node.
            via (str): The address of the relaying node.
        """
        df = self.routing_table_routes
        idx = df.index[df['scr'] == scr & df['dst']
                       == dst & df['via'] == via]
        # Check that the index is not empty. Which means we find the target row.
        if(idx.empty):
            logger.warning('route/index not found')
            return
        self.routing_table_routes = df.drop(idx)
        self.print_routes()

    def routing_table_clear_routes(self):
        """
        Clears all routes from the routing table
        """
        self.routing_table_routes.drop(
            self.routing_table_routes.index, inplace=True)
