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

import logging

from rich.table import Table

from sdwsn_controller.common import common


logger = logging.getLogger(f'main.{__name__}')


class Delay():
    def __init__(
        self,
        # cycle_seq,
        seq,
        delay
    ) -> None:
        # assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        assert isinstance(delay, int)
        # self.cycle_seq = cycle_seq
        self.seq = seq
        self.delay = delay


class DelaySamples():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.callback = None
        self.clear()

    def clear(self):
        self.samples = {}

    def size(self):
        return len(self.samples)

    def register_callback(self, callback):
        self.callback = callback

    def get_sample(self, seq):
        return self.samples.get(seq)

    def get_average(self):
        last_samples = []
        for sample in self.samples.values():
            # if sample.cycle_seq == cycle_seq:
            last_samples.append(sample.delay)
        return sum(last_samples) / len(last_samples)

    def add_sample(self, seq, delay) -> Delay:
        if self.get_sample(seq):
            return
        logger.debug(
            f'Node {self.node.id}: add delay {delay}, seq {seq}')
        delay_sample = Delay(seq=seq, delay=delay)
        self.samples.update({seq: delay_sample})
        # Fire callback
        if self.callback:
            self.callback(id=self.node.id, seq=seq, delay=delay)
        return delay_sample

    def print(self):
        table = Table(
            title=f"Delay samples (Cycle seq: {self.node.cycle_seq})")

        table.add_column("Node", justify="center",
                         style="cyan", no_wrap=True)
        # table.add_column("Cycle sequence", justify="center", style="magenta")
        table.add_column("Sequence", justify="center", style="magenta")
        table.add_column("Delay", justify="center", style="green")
        for key in self.samples:
            # if cycle_seq is not None:
            #     if key[0] == cycle_seq:
            #         delay = self.samples.get(key)
            #         table.add_row(str(self.node.id), str(delay.cycle_seq),
            #                       str(delay.seq), str(delay.delay))
            # else:
            delay = self.samples.get(key)
            table.add_row(self.node.sid,
                          str(delay.seq), str(delay.delay))

        logger.debug(f"Delay samples\n{common.log_table(table)}")
