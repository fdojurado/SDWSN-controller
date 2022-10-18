import random
from sdwsn_controller.tsch.schedule import Schedule, cell_type
import logging

logger = logging.getLogger('main.'+__name__)

class ContentionFreeScheduler(Schedule):
    def __init__(
            self,
            sf_size: int = 500,
            channel_offsets: int = 3
    ):
        super().__init__(
            sf_size,
            channel_offsets)

    def run(self, path, current_sf_size):
        logger.debug(f"running contention free scheduler for sf size {current_sf_size}")
        self.slot_frame_size = current_sf_size
        for _, p in path.items():
            if(len(p) >= 2):
                logger.debug(f"try to add uc for {p}")
                for i in range(len(p)-1):
                    # Tx node
                    tx_node = p[i]
                    tx_node = str(tx_node)+".0"
                    # Rx node
                    rx_node = p[i+1]
                    rx_node = str(rx_node)+".0"
                    logger.debug(f'link {tx_node}-{rx_node}')
                    # We first check whether the Tx-Rx link already exists.
                    if not self.schedule_link_exists(tx_node, rx_node):
                        logger.debug(f'link {tx_node}-{rx_node} does not exists')
                        # Random Tx link to RX if it is available
                        ts = random.randrange(0,
                                              current_sf_size-1)
                        ch = random.randrange(0,
                                              self.max_number_channels-1)
                        # Let's first check whether this timeslot is already in use in the schedule
                        while(not self.schedule_timeslot_free(ts)):
                            ts = random.randrange(0, current_sf_size-1)
                            logger.debug(f"ts already in use, we now try ts={ts}")
                        # We have found an empty timeslot
                        logger.debug(f'empty time slot {ts} found for {tx_node}-{rx_node}')
                        # Schedule Tx
                        self.schedule_add_uc(
                            tx_node, cell_type.UC_TX, ch, ts, rx_node)
                        # Schedule Rx
                        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Print the schedule
        self.schedule_print_table()
        self.schedule_print_grid()
