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


class Energy():
    def __init__(
        self,
        # cycle_seq,
        seq,
        energy
    ) -> None:
        # assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        assert isinstance(energy, int)
        # self.cycle_seq = cycle_seq
        self.seq = seq
        self.energy = energy


class EnergySamples():
    def __init__(
        self,
        node
    ) -> None:
        self.node = node
        self.callback = None
        self.clear()

    def clear(self):
        self.samples = {}
        self.last_seq = 0

    def size(self):
        return len(self.samples)

    def register_callback(self, callback):
        self.callback = callback

    def get_sample(self, seq):
        return self.samples.get(seq)

    def get_sample_last(self):
        return self.get_sample(self.last_seq).energy

    def add_sample(self, seq, energy) -> Energy:
        if self.get_sample(seq):
            return
        logger.debug(
            f'Node {self.node.id}: add energy {energy}, seq {seq}')
        energy_sample = Energy(seq=seq, energy=energy)
        self.samples.update({seq: energy_sample})
        if seq > self.last_seq:
            self.last_seq = seq
        # Fire callback
        if self.callback:
            self.callback(id=self.node.id, seq=seq, energy=energy)
        return energy_sample

    def print(self):
        table = Table(
            title=f"Energy samples (Cycle seq: {self.node.cycle_seq})")

        table.add_column("Node", justify="center",
                         style="cyan", no_wrap=True)
        # table.add_column("Cycle sequence", justify="center", style="magenta")
        table.add_column("Sequence", justify="center", style="magenta")
        table.add_column("Energy", justify="center", style="green")
        for key in self.samples:
            # if cycle_seq is not None:
            #     if key[0] == cycle_seq:
            #         energy = self.samples.get(key)
            #         table.add_row(str(self.node.id), str(energy.cycle_seq),
            #                       str(energy.seq), str(energy.energy))
            # else:
            energy = self.samples.get(key)
            table.add_row(self.node.sid,
                          str(energy.seq), str(energy.energy))

        logger.debug(f"Energy samples\n{common.log_table(table)}")
