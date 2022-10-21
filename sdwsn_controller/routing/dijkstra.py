from sdwsn_controller.routing.routing_table import RoutingTable
import networkx as nx
import logging

logger = logging.getLogger('main.'+__name__)


class Dijkstra(RoutingTable):
    def __init__(self):
        super().__init__()

    def run(self, G):
        # Clear all previous routes
        self.routing_table_clear_routes()
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                logger.debug("sp from node "+str(node))
                try:
                    node_path = nx.dijkstra_path(G, node, 1, weight='weight')
                    logger.debug("dijkstra path")
                    logger.debug(node_path)
                    path[node] = node_path
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    self.routing_table_add_route(
                        str(node)+".0", "1.1", str(node_path[1])+".0")
                except nx.NetworkXNoPath:
                    logger.exception("path not found")
        self.routing_table_print_table()
        logger.debug("total path")
        logger.debug(path)
        return path
