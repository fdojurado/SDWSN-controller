import random
from sdwsn_tsch.schedule import Schedule, cell_type


class ContentionFreeScheduler(Schedule):
    def __init__(
            self,
            sf_size: int = 100,
            channel_offsets: int = 3
    ):
        super().__init__(
            sf_size,
            channel_offsets)

    def run(self, path, current_sf_size):
        print("running contention free scheduler")
        for _, p in path.items():
            if(len(p) >= 2):
                # print("try to add uc for ", p)
                for i in range(len(p)-1):
                    # Tx node
                    tx_node = p[i]
                    tx_node = str(tx_node)+".0"
                    # Rx node
                    rx_node = p[i+1]
                    rx_node = str(rx_node)+".0"
                    # print(f'link {tx_node}-{rx_node}')
                    # We first check whether the Tx-Rx link already exists.
                    if not self.schedule_link_exists(tx_node, rx_node):
                        # print(f'link {tx_node}-{rx_node} does not exists')
                        # Random Tx link to RX if it is available
                        ts = random.randrange(0,
                                              current_sf_size-1)
                        ch = random.randrange(0,
                                              self.num_channel_offsets-1)
                        # Let's first check whether this timeslot is already in use in the schedule
                        while(not self.schedule_timeslot_free(ts)):
                            ts = random.randrange(0, current_sf_size-1)
                            # print(f"ts already in use, we now try ts={ts}")
                        # We have found an empty timeslot
                        # print(f'empty time slot {ts} found for {tx_node}-{rx_node}')
                        # Schedule Tx
                        self.schedule_add_uc(
                            tx_node, cell_type.UC_TX, ch, ts, rx_node)
                        # Schedule Rx
                        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
