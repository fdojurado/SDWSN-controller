import random
from sdwsn_controller.tsch.schedule import cell_type
import logging

logger = logging.getLogger('main.'+__name__)


class ContentionFreeScheduler():
    def __init__(self):
        self.__name = "Contention Free Scheduler"

    @property
    def name(self):
        return self.__name

    def run(self, path, current_sf_size, network):
        logger.debug(
            f"running contention free scheduler for sf size {current_sf_size}")
        network.tsch_clear()
        network.tsch_slotframe_size = current_sf_size
        for _, p in path.items():
            if (len(p) >= 2):
                logger.debug(f"add uc for {p}")
                for i in range(len(p)-1):
                    # Tx node
                    tx_node = network.nodes_add(p[i])
                    # Rx node
                    rx_node = network.nodes_add(p[i+1])
                    logger.debug(f'link {tx_node.id}-{rx_node.id}')
                    # We first check whether the Tx-Rx link already exists.
                    if not network.tsch_link_exists(tx_node, rx_node):
                        logger.debug(
                            f'link {tx_node.id}-{rx_node.id} does not exists')
                        # Random Tx link to RX if it is available
                        ts = random.randrange(0,
                                              current_sf_size-1)
                        ch = random.randrange(0,
                                              network.tsch_max_ch-1)
                        # Let's first check whether this timeslot is already in use in the schedule
                        while (not network.tsch_timeslot_free(ts)):
                            logger.debug(
                                f"ts {ts} already in use")
                            ts = random.randrange(0, current_sf_size-1)
                        # We have found an empty timeslot
                        logger.debug(
                            f'empty time slot {ts} found for {tx_node.id}-{rx_node.id}')
                        # Schedule Tx
                        tx_node.tsch_add_link(
                            cell_type.UC_TX, ch, ts, rx_node.id)
                        # Schedule Rx
                        rx_node.tsch_add_link(cell_type.UC_RX, ch, ts)
        # Print the schedule
        network.tsch_print()
