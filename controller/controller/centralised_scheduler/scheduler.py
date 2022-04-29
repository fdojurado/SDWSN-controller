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
                            node = p[i]
                            neigbour = p[i+1]
                            # print("rx ", str(node), "tx: ", str(neigbour))
                            timeslot = randrange(0,
                                                 self.schedule.slotframe_size-1)
                            channeloffset = randrange(1,
                                                      self.schedule.num_channel_offsets-1)
                            self.schedule.add_uc(
                                str(node), cell_type.UC_RX, channeloffset, timeslot)
                            self.schedule.add_uc(
                                str(neigbour), cell_type.UC_TX, destination=node)

                    else:
                        # print("add an uc rx for node ", p[0])
                        timeslot = randrange(0, self.schedule.slotframe_size-1)
                        channeloffset = randrange(1,
                                                  self.schedule.num_channel_offsets-1)
                        self.schedule.add_uc(
                            p[0], cell_type.UC_RX, channeloffset, timeslot)
                self.schedule.print_schedule()
                # Let's build the message in json format
                self.nc_job_queue.put(self.schedule.schedule_toJSON())
                # job = {"type": 0, "payload": self.schedule.schedule}
                # json_dump = json.dumps(job)
                # print(json_dump)
                # self.nc_job_queue.put(json_dump)
