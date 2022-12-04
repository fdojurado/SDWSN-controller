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


logger = logging.getLogger('main.'+__name__)


class Delay():
    def __init__(
        self,
        cycle_seq,
        seq,
        delay
    ) -> None:
        assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        assert isinstance(delay, int)
        self.cycle_seq = cycle_seq
        self.seq = seq
        self.delay = delay


class DelaySamples():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.clear()

    def clear(self):
        self.samples = {}

    def size(self):
        return len(self.samples)

    def get_sample(self, cycle_seq, seq):
        return self.samples.get((cycle_seq, seq))

    def get_average(self, cycle_seq):
        last_samples = []
        for sample in self.samples.values():
            if sample.cycle_seq == cycle_seq:
                last_samples.append(sample.delay)
        return sum(last_samples) / len(last_samples)

    def add_sample(self, cycle_seq, seq, delay) -> Delay:
        if self.get_sample(cycle_seq, seq):
            return
        logger.debug(
            f'Node {self.node.id}: add delay {delay}, cycle seq {cycle_seq}, seq {seq}')
        energy_sample = Delay(cycle_seq=cycle_seq,
                              seq=seq, delay=delay)
        self.samples.update({(cycle_seq, seq): energy_sample})
        return energy_sample

    def print(self, cycle_seq):
        table = Table(title="Delay samples")

        table.add_column("Node", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Cycle sequence", justify="center", style="magenta")
        table.add_column("Sequence", justify="center", style="magenta")
        table.add_column("Delay", justify="center", style="green")
        for key in self.samples:
            if cycle_seq is not None:
                if key[0] == cycle_seq:
                    delay = self.samples.get(key)
                    table.add_row(str(self.node.id), str(delay.cycle_seq),
                                  str(delay.seq), str(delay.delay))
            else:
                delay = self.samples.get(key)
                table.add_row(str(self.node.id), str(delay.cycle_seq),
                              str(delay.seq), str(delay.delay))

        logger.info(f"Delay samples\n{common.log_table(table)}")
