import random
from sdwsn_tsch.schedule import cell_type


def contention_free_schedule(schedule, path, slotframe_size):
    print("running contention free scheduler")
    schedule.clear_schedule()
    for _, p in path.items():
        if(len(p) >= 2):
            print("try to add uc for ", p)
            for i in range(len(p)-1):
                # Tx node
                tx_node = p[i]
                tx_node = str(tx_node)+".0"
                # Rx node
                rx_node = p[i+1]
                rx_node = str(rx_node)+".0"
                print(f'link {tx_node}-{rx_node}')
                # We first check whether the Tx-Rx link already exists.
                if not schedule.link_exists(tx_node, rx_node):
                    print(f'link {tx_node}-{rx_node} does not exists')
                    # Random Tx link to RX if it is available
                    ts = random.randrange(0,
                                          slotframe_size-1)
                    ch = random.randrange(0,
                                          schedule.num_channel_offsets-1)
                    # Let's first check whether this timeslot is already in use in the schedule
                    while(not schedule.timeslot_free_in_schedule(ts)):
                        ts = random.randrange(0, slotframe_size-1)
                        print(f"ts already in use, we now try ts={ts}")
                    # We have found an empty timeslot
                    print(f'empty time slot {ts} found for {tx_node}-{rx_node}')
                    # Schedule Tx
                    schedule.add_uc(
                        tx_node, cell_type.UC_TX, ch, ts, rx_node)
                    # Schedule Rx
                    schedule.add_uc(rx_node, cell_type.UC_RX, ch, ts)
                else:
                    print(f'link {tx_node}-{rx_node} already exists')
