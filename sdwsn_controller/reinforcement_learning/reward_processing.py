from abc import ABC, abstractmethod
import numpy as np
from sdwsn_controller.database.db_manager import DatabaseManager, SLOT_DURATION
from sdwsn_controller.database.database import NODES_INFO


class RewardProcessing(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def calculate_reward(self):
        pass


class EmulatedRewardProcessing(RewardProcessing):
    def __init__(
        self,
        database: object = DatabaseManager(),
        power_min: int = 0,
        power_max: int = 5000,
        delay_min: int = SLOT_DURATION,
        delay_max: int = 15000,
    ):
        self.db = database
        self.__power_min = power_min
        self.__power_max = power_max
        self.__delay_min = delay_min
        self.__delay_max = delay_max
        super().__init__()

    def calculate_reward(self, alpha, beta, delta, sequence):
        # Get the sensor nodes to loop in ascending order
        nodes = self.db.get_sensor_nodes_in_order()
        # Get the normalized average power consumption for this cycle
        power_wam, power_mean, power_normalized = self.__get_network_power_consumption(
            nodes, sequence)
        power = [power_wam, power_mean, power_normalized]
        # Get the normalized average delay for this cycle
        delay_wam, delay_mean, delay_normalized = self.__get_network_delay(
            nodes, sequence)
        delay = [delay_wam, delay_mean, delay_normalized]
        # Get the normalized average pdr for this cycle
        pdr_wam, pdf_mean = self.__get_network_pdr(nodes, sequence)
        pdr = [pdr_wam, pdf_mean]
        # Calculate the reward
        reward = -1*(alpha*power_normalized+beta *
                     delay_normalized-delta*pdr_wam)
        return reward, power, delay, pdr

    def __get_network_power_consumption(self, nodes, sequence):
        # Variable to keep track of the number of energy consumption samples
        power_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.db.get_last_power_consumption(
                node, power_samples, sequence)
        print(f"power samples for sequence {sequence}")
        print(power_samples)
        # We now need to compute the weighted arithmetic mean
        power_wam, power_mean = self.__power_weighted_arithmetic_mean(
            power_samples)
        # We now need to normalize the power WAM
        normalized_power = (power_wam - self.__power_min) / \
            (self.__power_max-self.__power_min)
        print(f'normalized power {normalized_power}')
        return power_wam, power_mean, normalized_power

    def __power_weighted_arithmetic_mean(self, power_samples):
        weights = []
        all_power_samples = []
        for elem in power_samples:
            node = elem[0]
            power = elem[1]
            all_power_samples.append(power)
            # print(f'Finding the WAM of {node} with power {power}')
            weight = self.__power_compute_wam_weight(node)
            weights.append(weight)
        print(f'power all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_power = np.array(all_power_samples)
        all_power_transpose = np.transpose(all_power)
        # print(f'transpose all power {all_power_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_power_transpose)
        # Overall network mean
        normal_mean = all_power.sum()/len(all_power_samples)
        print(f'power network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __power_compute_wam_weight(self, node):
        # Let's first get the rank of the sensor node
        node_rank = self.db.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.db.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.db.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    def __get_network_delay(self, nodes, sequence):
        # Variable to keep track of the number of delay samples
        delay_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.db.get_avg_delay(
                node, delay_samples, sequence)
        print(f"delay samples for sequence {sequence}")
        print(delay_samples)
        # We now need to compute the weighted arithmetic mean
        delay_wam, delay_mean = self.__delay_weighted_arithmetic_mean(
            delay_samples)
        # We now need to normalize the power WAM
        normalized_delay = (delay_wam - self.__delay_min) / \
            (self.__delay_max-self.__delay_min)
        print(f'normalized delay {normalized_delay}')
        return delay_wam, delay_mean, normalized_delay

    def __delay_weighted_arithmetic_mean(self, delay_samples):
        weights = []
        all_delay_samples = []
        for elem in delay_samples:
            node = elem[0]
            delay = elem[1]
            all_delay_samples.append(delay)
            weight = self.__delay_compute_wam_weight(node)
            weights.append(weight)
        print(f'delay all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_delay = np.array(all_delay_samples)
        all_delay_transpose = np.transpose(all_delay)
        # print(f'transpose all delay {all_delay_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_delay_transpose)
        # Overall network mean
        normal_mean = all_delay.sum()/len(all_delay_samples)
        print(f'delay network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __delay_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank
        # Let's get the rank of the sensor node
        node_rank = self.db.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Calculate the weight
        weight = 1 - node_rank/(last_rank+1)
        # print(f'computing WAM of node {node} rank {node_rank} weight {weight}')
        return weight

    def __get_network_pdr(self, nodes, sequence):
        # Variable to keep track of the number of pdr samples
        pdr_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.db.get_avg_pdr(
                node, pdr_samples, sequence)
        print(f"pdr samples for sequence {sequence}")
        print(pdr_samples)
        # We now need to compute the weighted arithmetic mean
        pdr_wam, pdr_mean = self.__pdr_weighted_arithmetic_mean(
            pdr_samples)
        print(f'normalized pdr {pdr_wam}')
        return pdr_wam, pdr_mean

    def __pdr_weighted_arithmetic_mean(self, pdr_samples):
        weights = []
        all_pdr_samples = []
        for elem in pdr_samples:
            node = elem[0]
            pdr = elem[1]
            all_pdr_samples.append(pdr)
            weight = self.__pdr_compute_wam_weight(node)
            weights.append(weight)
        print(f'pdr all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_pdr = np.array(all_pdr_samples)
        all_pdr_transpose = np.transpose(all_pdr)
        # print(f'transpose all pdr {all_pdr_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_pdr_transpose)
        # Overall network mean
        normal_mean = all_pdr.sum()/len(all_pdr_samples)
        print(f'pdr network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def __pdr_compute_wam_weight(self, node):
        # We assume that the wight depends on the rank of
        # the node and the number of NBRs
        # Let's first get the rank of the sensor node
        node_rank = self.db.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.db.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.db.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing pdr WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight
