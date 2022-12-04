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

from sdwsn_controller.database.db_manager import DatabaseManager, SLOT_DURATION
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.common import common
from abc import ABC, abstractmethod
from rich.table import Table
import numpy as np
import logging

logger = logging.getLogger('main.'+__name__)


class RewardProcessing(ABC):
    def __init__(
        self
    ) -> None:
        super().__init__()

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def calculate_reward(self):
        pass


class EmulatedRewardProcessing(RewardProcessing):
    def __init__(
        self,
        network,
        power_min: int = 0,
        power_max: int = 5000,
        delay_min: int = SLOT_DURATION,
        delay_max: int = 15000,
        power_norm_offset: float = 0.0,
        delay_norm_offset: float = 0.0,
        reliability_norm_offset: float = 0.0
    ):
        self.__power_min = power_min
        self.__power_max = power_max
        self.__delay_min = delay_min
        self.__delay_max = delay_max
        self.__power_norm_offset = power_norm_offset
        self.__delay_norm_offset = delay_norm_offset
        self.__reliability_norm_offset = reliability_norm_offset
        self.__name = "Emulated Reward Processing"
        self.__network = network

        super().__init__()

    @property
    def name(self):
        return self.__name

    def calculate_reward(self, alpha, beta, delta, cycle_sequence):
        # Get the sensor nodes to loop in ascending order
        # nodes = self.db.get_sensor_nodes_in_order()
        # Get the normalized average power consumption for this cycle
        power_wam, power_mean, power_normalized = self.__get_network_power_consumption(
            cycle_sequence)
        power = [power_wam, power_mean, power_normalized]
        # Get the normalized average delay for this cycle
        delay_wam, delay_mean, delay_normalized = self.__get_network_delay(
            cycle_sequence)
        delay = [delay_wam, delay_mean, delay_normalized]
        # Get the normalized average pdr for this cycle
        pdr_wam, pdf_mean = self.__get_network_pdr(cycle_sequence)
        pdr = [pdr_wam, pdf_mean]
        # Calculate the reward
        reward = 2-1*(alpha*power_normalized+beta *
                      delay_normalized-delta*pdr_wam)
        return reward, power, delay, pdr

    def __get_network_power_consumption(self, cycle_sequence):
        # Variable to keep track of the number of energy consumption samples
        power_samples = {}
        # We first loop through all sensor nodes
        for node in self.__network.nodes.values():
            # Get all samples from the start of the network configuration
            if node.id != 1:
                # node.energy_print()
                power_samples.update(
                    {node: node.energy_get_last(cycle_sequence)})

        def power_samples_table(samples):
            table = Table(title="Power samples")
            table.add_column("Sensor node", justify="center", style="magenta")
            table.add_column("Avg. power consumption [mW]",
                             justify="center", style="green")
            sum_energy = 0
            for key in samples:
                energy = samples.get(key)
                table.add_row(str(key.id), str(energy))
                sum_energy += energy
            # Table add avg. at the end
            table.add_row("Average", str(sum_energy/len(samples)))
            return table

        logger.info(
            f"Power samples (SF: {self.__network.tsch_slotframe_size}) \n{common.log_table(power_samples_table(power_samples))}")
        # We now need to compute the weighted arithmetic mean
        power_wam, power_mean = self.__power_weighted_arithmetic_mean(
            power_samples)
        # We now need to normalize the power WAM
        normalized_power = self.__power_norm_offset + ((power_wam - self.__power_min) /
                                                       (self.__power_max-self.__power_min))
        logger.info(f'normalized power {normalized_power}')
        return power_wam, power_mean, normalized_power

    def __power_weighted_arithmetic_mean(self, power_samples):
        weights = []
        all_power_samples = []
        for key in power_samples:
            node = key
            power = power_samples.get(key)
            all_power_samples.append(power)
            logger.debug(f'Finding the WAM of {node.id} with power {power}')
            weight = self.__power_compute_wam_weight(node)
            weights.append(weight)
        logger.debug(f'power all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # logger.info(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        logger.debug(f'normalized weights {normalized_weights}')
        all_power = np.array(all_power_samples)
        all_power_transpose = np.transpose(all_power)
        # logger.info(f'transpose all power {all_power_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_power_transpose)
        # Overall network mean
        normal_mean = all_power.sum()/len(all_power_samples)
        logger.info(f'power network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __power_compute_wam_weight(self, node):
        # Let's first get the rank of the sensor node
        node_rank = node.rank
        # Get the value of the greatest rank of the network
        last_rank = self.__network.nodes_last_rank()
        # Let's get the number of neighbors
        num_nbr = node.neighbors_len()
        # Get the total number of sensor nodes
        N = self.__network.nodes_size()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        logger.debug(
            f'computing WAM of node {node.id} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    def __get_network_delay(self, cycle_sequence):
        # Variable to keep track of the number of delay samples
        delay_samples = {}
        # We first loop through all sensor nodes
        for node in self.__network.nodes.values():
            # Get all samples from the start of the network configuration
            if node.id != 1:
                # node.delay_print()
                delay_samples.update(
                    {node: node.delay_get_average(cycle_sequence)})

        def delay_samples_table(samples):
            table = Table(title="Delay samples")
            table.add_column("Sensor node", justify="center", style="magenta")
            table.add_column("Avg. delay [ms]",
                             justify="center", style="green")
            sum_delay = 0
            for key in samples:
                delay = samples.get(key)
                table.add_row(str(key.id), str(delay))
                sum_delay += delay
            table.add_row("Average", str(sum_delay/len(samples)))
            return table

        logger.info(
            f"Delay samples (SF: {self.__network.tsch_slotframe_size}) for cycle_sequence {cycle_sequence}\n{common.log_table(delay_samples_table(delay_samples))}")
        # We now need to compute the weighted arithmetic mean
        delay_wam, delay_mean = self.__delay_weighted_arithmetic_mean(
            delay_samples)
        # We now need to normalize the power WAM
        normalized_delay = self.__delay_norm_offset + ((delay_wam - self.__delay_min) /
                                                       (self.__delay_max-self.__delay_min))
        logger.debug(f'normalized delay {normalized_delay}')
        return delay_wam, delay_mean, normalized_delay

    def __delay_weighted_arithmetic_mean(self, delay_samples):
        weights = []
        all_delay_samples = []
        for key in delay_samples:
            node = key
            delay = delay_samples.get(key)
            all_delay_samples.append(delay)
            logger.debug(f'Finding the WAM of {node.id} with delay {delay}')
            weight = self.__delay_compute_wam_weight(node)
            weights.append(weight)
        logger.debug(f'delay all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        logger.debug(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        logger.debug(f'normalized weights {normalized_weights}')
        all_delay = np.array(all_delay_samples)
        all_delay_transpose = np.transpose(all_delay)
        # logger.info(f'transpose all delay {all_delay_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_delay_transpose)
        # Overall network mean
        normal_mean = all_delay.sum()/len(all_delay_samples)
        logger.debug(f'delay network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __delay_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank
        # Let's get the rank of the sensor node
        node_rank = node.rank
        # Get the value of the greatest rank of the network
        last_rank = self.__network.nodes_last_rank()
        # Calculate the weight
        weight = 1 - node_rank/(last_rank+1)
        logger.debug(
            f'computing WAM of node {node.id} rank {node_rank} weight {weight}')
        return weight

    def __get_network_pdr(self, cycle_sequence):
        # Variable to keep track of the number of pdr samples
        pdr_samples = {}
        # We first loop through all sensor nodes
        for node in self.__network.nodes.values():
            # Get all samples from the start of the network configuration
            if node.id != 1:
                # node.pdr_print()
                pdr_samples.update(
                    {node: node.pdr_get_average(cycle_sequence)})

        def pdr_samples_table(samples):
            table = Table(title="PDR samples")
            table.add_column("Sensor node", justify="center", style="magenta")
            table.add_column("Avg. PDR",
                             justify="center", style="green")
            sum_pdr = 0
            for key in samples:
                pdr = samples.get(key)
                table.add_row(str(key.id), str(pdr))
                sum_pdr += pdr
            table.add_row("Average", str(sum_pdr/len(samples)))
            return table

        logger.info(
            f"PDR samples (SF: {self.__network.tsch_slotframe_size}) for cycle_sequence {cycle_sequence}\n{common.log_table(pdr_samples_table(pdr_samples))}")
        # We now need to compute the weighted arithmetic mean
        pdr_wam, pdr_mean = self.__pdr_weighted_arithmetic_mean(
            pdr_samples)
        logger.debug(f'normalized pdr {pdr_wam}')
        pdr_wam = pdr_wam - self.__reliability_norm_offset
        return pdr_wam, pdr_mean

    def __pdr_weighted_arithmetic_mean(self, pdr_samples):
        weights = []
        all_pdr_samples = []
        for key in pdr_samples:
            node = key
            pdr = pdr_samples.get(key)
            all_pdr_samples.append(pdr)
            logger.debug(f'Finding the WAM of {node.id} with delay {pdr}')
            weight = self.__pdr_compute_wam_weight(node)
            weights.append(weight)
        logger.debug(f'pdr all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # logger.info(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        logger.debug(f'normalized weights {normalized_weights}')
        all_pdr = np.array(all_pdr_samples)
        all_pdr_transpose = np.transpose(all_pdr)
        # logger.info(f'transpose all pdr {all_pdr_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_pdr_transpose)
        # Overall network mean
        normal_mean = all_pdr.sum()/len(all_pdr_samples)
        logger.debug(f'pdr network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __pdr_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank of
        # the node and the number of NBRs
        # Let's first get the rank of the sensor node
        node_rank = node.rank
        # Get the value of the greatest rank of the network
        last_rank = self.__network.nodes_last_rank()
        # Let's get the number of neighbors
        num_nbr = node.neighbors_len()
        # Get the total number of sensor nodes
        N = self.__network.nodes_size()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        logger.debug(
            f'computing pdr WAM of node {node.id} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight
