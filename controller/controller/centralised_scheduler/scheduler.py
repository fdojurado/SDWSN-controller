import multiprocessing as mp
from controller.centralised_scheduler.schedule import *
from random import randrange
import json

# This is a simple scheduler which puts a tx and rx uc link for each edge in the current routing protocol.
# Rx for relay nodes are assigned randomly


class Scheduler(mp.Process):
    def __init__(self, config, verbose, input_queue, output_queue, nc_job_queue):
        mp.Process.__init__(self)
        self.config = config
        self.verbose = verbose
        self.input_queue = input_queue
        self.nc_job_queue = nc_job_queue
        self.output_queue = output_queue
        self.schedule = Schedule(
            self.config.tsch.slotframe_size, self.config.tsch.num_of_channels)

    def run(self):
        while(1):
            # Look for incoming jobs
            if not self.input_queue.empty():
                path = self.input_queue.get()
                print("job for scheduler")
                print(path)
                self.schedule.clear_schedule()
                for u, p in path.items():
                    if(len(p) >= 2):
                        # print("try to add uc for ", p)
                        for i in range(len(p)-1):
                            # TODO: find a way to avoid forcing the last addr of
                            # sensor nodes to 0.
                            node = p[i+1]
                            node = str(node)+".0"
                            neighbor = p[i]
                            neighbor = str(neighbor)+".0"
                            # print("rx ", str(node), "tx: ", str(neighbor))
                            timeslot = randrange(0,
                                                 self.schedule.slotframe_size-1)
                            channeloffset = randrange(1,
                                                      self.schedule.num_channel_offsets-1)
                            self.schedule.add_uc(
                                str(node), cell_type.UC_RX, channeloffset, timeslot)
                            self.schedule.add_uc(
                                str(neighbor), cell_type.UC_TX, destination=node)

                    else:
                        # print("add an uc rx for node ", p[0])
                        timeslot = randrange(0, self.schedule.slotframe_size-1)
                        channeloffset = randrange(1,
                                                  self.schedule.num_channel_offsets-1)
                        self.schedule.add_uc(
                            p[0], cell_type.UC_RX, channeloffset, timeslot)
                self.schedule.print_schedule()
                # Save the slotframe size in SLOTFRAME_LEN collection
                self.save_slotframe_len()
                # Let's build the message in json format
                self.output_queue.put(self.schedule.schedule_toJSON())

    def save_slotframe_len(self):
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "slotframe_len": self.schedule.slotframe_size,
        }
        Database.insert(SLOTFRAME_LEN, data)
