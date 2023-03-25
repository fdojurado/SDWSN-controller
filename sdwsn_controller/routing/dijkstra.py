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
from sdwsn_controller.routing.router import Router
import networkx as nx
import logging

logger = logging.getLogger(f'main.{__name__}')


class Dijkstra(Router):
    def __init__(
            self,
            network
    ):
        self.__name = "Dijkstra"
        super().__init__(
            network=network
        )

    @property
    def name(self):
        return self.__name

    def run(self, G):
        # Clear all previous routes
        self.network.routes_clear()
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                node = self.network.nodes_get(node)
                logger.debug("sp from node "+str(node.id))
                try:
                    node_path = nx.dijkstra_path(
                        G, node.id, 1, weight='weight')
                    logger.debug("dijkstra path")
                    logger.debug(node_path)
                    path[node.id] = node_path
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    node.route_add(0, node_path[1])
                except nx.NetworkXNoPath:
                    logger.exception("path not found")

        logger.debug("total path")
        logger.debug(path)
        self.network.routes_print()
        return path
