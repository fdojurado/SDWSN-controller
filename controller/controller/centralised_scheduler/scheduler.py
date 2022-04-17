import multiprocessing as mp
from controller.centralised_scheduler.schedule import *
from random import randrange

# This is a simple scheduler which puts a tx and rx uc link for each edge in the current routing protocol.


class Scheduler(mp.Process):
    def __init__(self, config, verbose, input_queue, output_queue):
        mp.Process.__init__(self)
        self.config = config
        self.verbose = verbose
        self.input_queue = input_queue
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
                        print("try to add uc for ", p)
                        for i in range(len(p)-1):
                            node = p[i]
                            neigbour = p[i+1]
                            print("rx ", str(node), "tx: ", str(neigbour))
                            timeslot = randrange(
                                self.schedule.slotframe_size-1)
                            channeloffset = randrange(
                                self.schedule.num_channel_offsets-1)
                            self.schedule.add_uc(
                                str(node), UC_RX, channeloffset, timeslot)
                            self.schedule.add_uc(
                                str(neigbour), UC_TX, destination=node)

                    else:
                        print("add an uc rx for node ", p[0])
                        timeslot = randrange(self.schedule.slotframe_size-1)
                        channeloffset = randrange(
                            self.schedule.num_channel_offsets-1)
                        self.schedule.add_uc(
                            p[0], UC_RX, channeloffset, timeslot)
