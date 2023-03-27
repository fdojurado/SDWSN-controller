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
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(f'main.{__name__}')


class TSCHScheduler(ABC):
    def __init__(
            self,
            network
    ) -> None:
        self.__network = network
        super().__init__()

    @property
    def network(self):
        return self.__network

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def run(self):
        pass
