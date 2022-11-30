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
from datetime import datetime
from sdwsn_controller.database.database import Database, OBSERVATIONS
from sdwsn_controller.packet.packet import SDN_NAPL_LEN, NA_Packet_Payload

import pandas as pd
# Constants for packet delay calculation
SLOT_DURATION = 10


class PDR():
    def __init__(
        self,
        timestamp: float = 0.0,
        cycle_seq: int = 0,
        seq: int = 0
    ):
        assert isinstance(timestamp, float)
        assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        self.__timestamp = timestamp
        self.__cycle_seq = cycle_seq
        self.__seq = seq

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def cycle_seq(self):
        return self.__cycle_seq

    @property
    def seq(self):
        return self.__seq

    def to_dict(self):
        data = {
            'timestamp': self.timestamp,
            'cycle_seq': self.cycle_seq,
            'seq': self.seq
        }
        return data

    def __repr__(self) -> str:
        return "PDR(timestamp: {}, cycle seq: {}, seq: {})".format(
            self.timestamp,
            self.cycle_seq,
            self.seq)


class Delay():
    def __init__(
        self,
        timestamp: float = 0.0,
        cycle_seq: int = 0,
        seq: int = 0,
        sampled_delay: int = 0
    ):
        assert isinstance(timestamp, float)
        assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        assert isinstance(sampled_delay, int)
        self.__timestamp = timestamp
        self.__cycle_seq = cycle_seq
        self.__seq = seq
        self.__sampled_delay = sampled_delay

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def cycle_seq(self):
        return self.__cycle_seq

    @property
    def seq(self):
        return self.__seq

    @property
    def sampled_delay(self):
        return self.__sampled_delay

    def to_dict(self):
        data = {
            'timestamp': self.timestamp,
            'cycle_seq': self.cycle_seq,
            'seq': self.seq,
            'sampled_delay': self.sampled_delay,
        }
        return data

    def __repr__(self) -> str:
        return "Delay(timestamp: {}, cycle seq: {}, seq: {}, sampled delay: {})".format(
            self.timestamp,
            self.cycle_seq,
            self.seq,
            self.sampled_delay)


class Energy():
    def __init__(
        self,
        timestamp: float = 0.0,
        cycle_seq: int = 0,
        seq: int = 0,
        ewma_energy: int = 0
    ):
        assert isinstance(timestamp, float)
        assert isinstance(cycle_seq, int)
        assert isinstance(seq, int)
        assert isinstance(ewma_energy, int)
        self.__timestamp = timestamp
        self.__cycle_seq = cycle_seq
        self.__seq = seq
        self.__ewma_energy = ewma_energy

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def cycle_seq(self):
        return self.__cycle_seq

    @property
    def seq(self):
        return self.__seq

    @property
    def ewma_energy(self):
        return self.__ewma_energy

    def to_dict(self):
        data = {
            'timestamp': self.timestamp,
            'cycle_seq': self.cycle_seq,
            'seq': self.seq,
            'ewma_energy': self.ewma_energy
        }
        return data

    def __repr__(self) -> str:
        return "Energy(timestamp: {}, cycle seq: {}, seq: {}, ewma energy: {})".format(
            self.timestamp,
            self.cycle_seq,
            self.seq,
            self.ewma_energy
        )


class Neighbor():
    def __init__(
        self,
        timestamp: float = 0.0,
        dst: str = None,
        rssi: int = 0,
        etx: int = 0
    ):
        assert isinstance(timestamp, float)
        assert isinstance(dst, str)
        assert isinstance(rssi, int)
        assert isinstance(etx, int)
        self.__timestamp = timestamp
        self.__dst = dst
        self.__rssi = rssi
        self.__etx = etx

    def to_dict(self):
        data = {
            'timestamp': self.timestamp,
            'dst': self.dst,
            'rssi': self.rssi,
            'etx': self.etx,
        }
        return data

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def dst(self):
        return self.__dst

    @property
    def rssi(self):
        return self.__rssi

    @property
    def etx(self):
        return self.__etx

    def __repr__(self) -> str:
        return "Neighbor(timestamp: {}, dst: {}, rssi: {}, etx: {})".format(
            self.timestamp,
            self.dst,
            self.rssi,
            self.etx
        )


class NodesInfoItem():
    def __init__(
        self,
        node_id: str = None,
        rank: int = 0
    ):
        assert isinstance(node_id, str)
        assert isinstance(rank, int)
        self.__node_id = node_id
        self.__pdr = []
        self.__delay = []
        self.__energy = []
        self.__neighbors = []
        self.__neighbors_timestamp = 0.0
        self.__rank = rank

    def to_dict(self):
        pdr_dict = []
        if not self.pdr:
            pdr_dict = self.pdr
        else:
            for item in self.pdr:
                pdr_dict.append(item.to_dict())

        delay_dict = []
        if not self.delay:
            delay_dict = self.delay
        else:
            for item in self.delay:
                delay_dict.append(item.to_dict())

        energy_dict = []
        if not self.energy:
            energy_dict = self.energy
        else:
            for item in self.energy:
                energy_dict.append(item.to_dict())

        nbrs_dict = []
        if not self.nbr:
            nbrs_dict = self.nbr
        else:
            for item in self.nbr:
                nbrs_dict.append(item.to_dict())

        data = {
            'node_id': self.node_id,
            'pdr': pdr_dict,
            'delay': delay_dict,
            'energy': energy_dict,
            'rank': self.rank,
            'neighbors': nbrs_dict,
        }
        return data

    @property
    def node_id(self):
        # print("reading energy")
        return self.__node_id

    @property
    def energy(self):
        # print("reading energy")
        return self.__energy

    @energy.setter
    def energy(self, val):
        assert isinstance(val, Energy)
        self.__energy.append(val)

    def get_nodes_energy_cycle_seq(self, cycle_seq) -> Energy:
        energy_samples = []
        for item in self.energy:
            if item.cycle_seq == cycle_seq:
                energy_samples.append(item)
        return energy_samples

    def get_nodes_delay_cycle_seq(self, cycle_seq) -> Delay:
        delay_samples = []
        for item in self.delay:
            if item.cycle_seq == cycle_seq:
                delay_samples.append(item)
        return delay_samples

    def get_nodes_pdr_cycle_seq(self, cycle_seq) -> PDR:
        pdr_samples = []
        for item in self.pdr:
            if item.cycle_seq == cycle_seq:
                pdr_samples.append(item)
        return pdr_samples

    @property
    def pdr(self):
        return self.__pdr

    @pdr.setter
    def pdr(self, val):
        assert isinstance(val, PDR)
        self.__pdr.append(val)

    @property
    def delay(self):
        return self.__delay

    @delay.setter
    def delay(self, val):
        assert isinstance(val, Delay)
        self.__delay.append(val)

    @property
    def nbr(self):
        return self.__neighbors

    @property
    def nbr_timestamp(self):
        return self.__neighbors_timestamp

    @nbr_timestamp.setter
    def nbr_timestamp(self, val):
        assert isinstance(val, float)
        self.__neighbors_timestamp = val

    @nbr.setter
    def nbr(self, val):
        assert isinstance(val, Neighbor)
        self.nbr_timestamp = val.timestamp
        self.__neighbors.append(val)

    @property
    def rank(self):
        return self.__rank

    @rank.setter
    def rank(self, val):
        assert isinstance(val, int)
        self.__rank = val

    def delete_obj_pdr(self):
        if not self.pdr:
            return
        for item in self.pdr:
            del item

    def delete_obj_delay(self):
        if not self.delay:
            return
        for item in self.delay:
            del item

    def delete_obj_energy(self):
        if not self.energy:
            return
        for item in self.energy:
            del item

    def delete_obj_nbr(self):
        if not self.nbr:
            return
        for item in self.nbr:
            del item

    def __repr__(self) -> str:
        return "NodesInfoItem(node id={}, rank={}, pdr={}, delay={}, energy={}, neighbors={})".format(
            self.node_id, self.rank, self.pdr, self.delay, self.energy, self.nbr)


class NodesInfo():
    def __init__(
        self,
        nodes_info_list: list = None
    ):
        assert isinstance(nodes_info_list, list)
        self.__nodes_info_list = nodes_info_list

    @property
    def nodes_info_list(self):
        # print(f"reading nodes_info_list")
        return self.__nodes_info_list

    @nodes_info_list.setter
    def nodes_info_list(self, val):
        # print(f"appending to nodes_info_list: {val}")
        assert isinstance(val, NodesInfoItem)
        self.__nodes_info_list.append(val)

    def length(self):
        return len(self.nodes_info_list)

    def unique(self, list1):

        # insert the list to the set
        list_set = set(list1)
        # convert the set to the list
        unique_list = list(list_set)
        return unique_list

    def delete_all(self):
        for item in self.nodes_info_list:
            item.delete_obj_pdr()
            item.delete_obj_delay()
            item.delete_obj_energy()
            item.delete_obj_nbr()
            del item

        self.nodes_info_list.clear()

    def get_last_index_wsn(self):
        """
        Gets the greatest node id of all WSN. The last index is
        calculated looking into NBR links.

        Returns:
            str: Greatest node id.
        """
        index_array = []
        for item in self.nodes_info_list:
            for nbr in item.nbr:
                node_id = item.node_id
                index_array.append(float(node_id))
                index_array.append(float(nbr.dst))
        unique_node_ids = self.unique(index_array)
        max_node_id = max(unique_node_ids)
        return int(max_node_id)

    def get_sensor_nodes_in_order(self):
        index_array = []
        for item in self.nodes_info_list:
            for nbr in item.nbr:
                node_id = item.node_id
                if str(node_id) != '1.0':
                    index_array.append(float(node_id))
                if str(nbr.dst) != '1.0':
                    index_array.append(float(nbr.dst))
        unique_node_ids = self.unique(index_array)
        unique_node_ids.sort()
        unique_node_ids = [str(x) for x in unique_node_ids]
        return unique_node_ids

    def get_energy_cycle_seq(self, addr, cycle_seq):
        """
        Get the last energy sample within the give
        cycle sequence.

        Args:
            cycle_seq (int): The cycle sequence.

        Returns:
            int: The last energy sample in the cycle sequence.
        """
        last_cycle_seq_samples = None
        for item in self.nodes_info_list:
            if item.node_id == addr:
                last_cycle_seq_samples = item.get_nodes_energy_cycle_seq(
                    cycle_seq)
        if last_cycle_seq_samples is None:
            return
        # Get the last of the cycle sequence samples
        last_timestamp = 0
        latest_energy_sample = 0
        for item in last_cycle_seq_samples:
            if item.timestamp > last_timestamp:
                last_timestamp = item.timestamp
                latest_energy_sample = item.ewma_energy
        return latest_energy_sample

    def get_delay_cycle_seq(self, addr, cycle_seq):
        """
        Get the last average delay of the given node in the cycle sequence.

        Args:
            addr (str): Address of the sensor node.
            cycle_seq (int): The cycle sequence.

        Returns:
            float: The average sensor node delay on this cycle.
        """
        last_cycle_seq_samples = None
        for item in self.nodes_info_list:
            if item.node_id == addr:
                last_cycle_seq_samples = item.get_nodes_delay_cycle_seq(
                    cycle_seq)
        if last_cycle_seq_samples is None:
            return
        return last_cycle_seq_samples

    def greatest_rank(self) -> dict:
        rank = 0
        for item in self.nodes_info_list:
            if item.rank > rank:
                rank = item.rank
                info = item.to_dict()
        return info

    def get_pdr_cycle_seq(self, addr, cycle_seq):
        """
        Get the last average PDR of the given node in the cycle sequence.

        Args:
            addr (str): Address of the sensor node.
            cycle_seq (int): The cycle sequence.

        Returns:
            float: The average sensor node PDR on this cycle.
        """
        last_cycle_seq_samples = None
        for item in self.nodes_info_list:
            if item.node_id == addr:
                last_cycle_seq_samples = item.get_nodes_pdr_cycle_seq(
                    cycle_seq)
        if last_cycle_seq_samples is None:
            return
        return last_cycle_seq_samples


class ObservationsItem():
    def __init__(
        self,
        timestamp: float = 0.0,
        alpha: float = 0.0,
        beta: float = 0.0,
        delta: float = 0.0,
        power_wam: float = 0.0,
        power_mean: float = 0.0,
        power_normalized: float = 0.0,
        delay_wam: float = 0.0,
        delay_mean: float = 0.0,
        delay_normalized: float = 0.0,
        pdr_wam: float = 0.0,
        pdr_mean: float = 0.0,
        last_ts_in_schedule: int = 0,
        current_sf_len: int = 0,
        normalized_ts_in_schedule: float = 0.0,
        reward: float = 0.0
    ):
        assert isinstance(timestamp, float)
        assert isinstance(alpha, float)
        assert isinstance(beta, float)
        assert isinstance(delta, float)
        assert isinstance(power_wam, float)
        assert isinstance(power_mean, float)
        assert isinstance(power_normalized, float)
        assert isinstance(delay_wam, float)
        assert isinstance(delay_mean, float)
        assert isinstance(delay_normalized, float)
        assert isinstance(pdr_wam, float)
        assert isinstance(pdr_mean, float)
        assert isinstance(last_ts_in_schedule, int)
        assert isinstance(current_sf_len, int)
        # assert isinstance(normalized_ts_in_schedule, float)
        # assert isinstance(reward, float)
        self.__timestamp = timestamp
        self.__alpha = alpha
        self.__beta = beta
        self.__delta = delta
        self.__power_wam = power_wam
        self.__power_mean = power_mean
        self.__power_normalized = power_normalized
        self.__delay_wam = delay_wam
        self.__delay_mean = delay_mean
        self.__delay_normalized = delay_normalized
        self.__pdr_wam = pdr_wam
        self.__pdr_mean = pdr_mean
        self.__last_ts_in_schedule = last_ts_in_schedule
        self.__current_sf_len = current_sf_len
        self.__normalized_ts_in_schedule = normalized_ts_in_schedule
        self.__reward = reward

    def to_dict(self):
        data = {
            'timestamp': self.timestamp,
            'alpha': self.alpha,
            'beta': self.beta,
            'delta': self.delta,
            'power_wam': self.power_wam,
            'power_mean': self.power_mean,
            'power_normalized': self.power_normalized,
            'delay_wam': self.delay_wam,
            'delay_mean': self.delay_mean,
            'delay_normalized': self.delay_normalized,
            'pdr_wam': self.pdr_wam,
            'pdr_mean': self.pdr_mean,
            'last_ts_in_schedule': self.last_ts_in_schedule,
            'current_sf_len': self.current_sf_len,
            'normalized_ts_in_schedule': self.normalized_ts_in_schedule,
            'reward': self.reward
        }
        return data

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def alpha(self):
        return self.__alpha

    @property
    def beta(self):
        return self.__beta

    @property
    def delta(self):
        return self.__delta

    @property
    def power_wam(self):
        return self.__power_wam

    @property
    def power_mean(self):
        return self.__power_mean

    @property
    def power_normalized(self):
        return self.__power_normalized

    @property
    def delay_wam(self):
        return self.__delay_wam

    @property
    def delay_mean(self):
        return self.__delay_mean

    @property
    def delay_normalized(self):
        return self.__delay_normalized

    @property
    def pdr_wam(self):
        return self.__pdr_wam

    @property
    def pdr_mean(self):
        return self.__pdr_mean

    @property
    def last_ts_in_schedule(self):
        return self.__last_ts_in_schedule

    @property
    def current_sf_len(self):
        return self.__current_sf_len

    @property
    def normalized_ts_in_schedule(self):
        return self.__normalized_ts_in_schedule

    @property
    def reward(self):
        return self.__reward


class Observations():
    def __init__(
        self,
        observations_list: list = None
    ):
        assert isinstance(observations_list, list)
        self.__observations_list = observations_list

    @property
    def observations_list(self):
        return self.__observations_list

    @observations_list.setter
    def observations_list(self, val):
        assert isinstance(val, ObservationsItem)
        self.__observations_list.append(val)

    def export_observations(self, folder, name):
        list_obs = []
        for item in self.observations_list:
            list_obs.append(item.to_dict())
        df = pd.DataFrame(list_obs)
        df.to_csv(folder+name+'.csv')


class NoDatabase(Database):
    def __init__(self):
        self.__observations = Observations(observations_list=[])
        self.__nodes_info = NodesInfo(nodes_info_list=[])
        super().__init__()

    @property
    def observations(self):
        return self.__observations

    @property
    def nodes_info(self):
        # print("Reading from node info")
        return self.__nodes_info

    @nodes_info.setter
    def nodes_info(self, val):
        # print(f"Adding to nodes info list: {val}")
        self.__nodes_info = val

    def initialize(self):
        self.__observations = Observations(observations_list=[])
        self.__nodes_info = NodesInfo(nodes_info_list=[])

    def DATABASE(self):
        pass

    def export_collection(self, collection, simulation_name, folder):
        if collection == OBSERVATIONS:
            self.observations.export_observations(
                folder=folder, name=simulation_name)

    def delete_info_collection(self):
        self.nodes_info.delete_all()

    def save_serial_packet(self):
        pass

    def __exist(self, collection, lookup_field, val):
        for item in collection:
            data = item.to_dict()[lookup_field]
            if data == val:
                return item
        return None

    def save_energy(self, ip_pkt, na_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        # Check if this node already exist
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', ip_pkt.scrStr)
        energy_data = Energy(
            timestamp=current_time,
            cycle_seq=na_pkt.cycle_seq,
            seq=na_pkt.seq,
            ewma_energy=na_pkt.energy
        )
        if node_info is None:
            # Create a new entry
            node_info = NodesInfoItem(
                node_id=ip_pkt.scrStr,
                rank=na_pkt.rank
            )
            node_info.energy = energy_data
            self.nodes_info.nodes_info_list = node_info
        else:
            node_info.rank = na_pkt.rank
            node_info.energy = energy_data

    def save_neighbors(self, ip_pkt, na_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        # Check if this node already exist
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', ip_pkt.scrStr)
        if node_info is None:
            # Create a new entry
            node_info = NodesInfoItem(
                node_id=ip_pkt.scrStr,
                rank=na_pkt.rank
            )
            self.nodes_info.nodes_info_list = node_info
        else:
            node_info.rank = na_pkt.rank

        # Process neighbors
        blocks = len(na_pkt.payload) // SDN_NAPL_LEN
        idx_start = 0
        idx_end = 0
        for _ in range(1, blocks+1):
            idx_end += SDN_NAPL_LEN
            payload = na_pkt.payload[idx_start:idx_end]
            idx_start = idx_end
            payload_unpacked = NA_Packet_Payload.unpack(payload)
            nbr_data = Neighbor(
                timestamp=current_time,
                dst=payload_unpacked.addrStr,
                rssi=payload_unpacked.rssi,
                etx=payload_unpacked.etx
            )
            node_info.nbr = nbr_data

    def save_pdr(self, ip_pkt, data_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        # Check if this node already exist
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', ip_pkt.scrStr)
        pdr_data = PDR(
            timestamp=current_time,
            cycle_seq=data_pkt.cycle_seq,
            seq=data_pkt.seq
        )
        if node_info is None:
            # Create a new entry
            node_info = NodesInfoItem(
                node_id=ip_pkt.scrStr
            )
            node_info.pdr = pdr_data
            self.nodes_info.nodes_info_list = node_info
        else:
            node_info.pdr = pdr_data

    def save_delay(self, ip_pkt, data_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        sampled_delay = data_pkt.asn * SLOT_DURATION
        # Check if this node already exist
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', ip_pkt.scrStr)
        delay_data = Delay(
            timestamp=current_time,
            cycle_seq=data_pkt.cycle_seq,
            seq=data_pkt.seq,
            sampled_delay=sampled_delay
        )
        if node_info is None:
            # Create a new entry
            node_info = NodesInfoItem(
                node_id=ip_pkt.scrStr
            )
            node_info.delay = delay_data
            self.nodes_info.nodes_info_list = node_info
        else:
            node_info.delay = delay_data

    def get_rank(self, addr):
        if (addr == "1.0"):
            return 0
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            return
        return node_info.rank

    def greatest_rank(self):
        return self.nodes_info.greatest_rank()

    def get_last_slotframe_len(self):
        pass

    def get_last_delay(self):
        pass

    def get_last_pdr(self):
        pass

    def get_last_nbr(self, addr):
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            return None
        # Get last timestamp
        last_timestamp = node_info.nbr_timestamp

        last_nbrs = []
        for nbr in node_info.nbr:
            if nbr.timestamp == last_timestamp:
                last_nbrs.append(nbr.to_dict())

        return last_nbrs

    def get_number_of_sensors(self):
        return self.nodes_info.length()

    def get_sensor_nodes(self):
        sensor_nodes_dict = []
        for item in self.nodes_info.nodes_info_list:
            sensor_nodes_dict.append(item.to_dict())
        return sensor_nodes_dict

    def get_last_index_wsn(self):
        return self.nodes_info.get_last_index_wsn()

    def get_sensor_nodes_in_order(self):
        return self.nodes_info.get_sensor_nodes_in_order()

    def save_observations(self,
                          timestamp=None,
                          alpha=None,
                          beta=None,
                          delta=None,
                          power_wam=None,
                          power_mean=None,
                          power_normalized=None,
                          delay_wam=None,
                          delay_mean=None,
                          delay_normalized=None,
                          pdr_wam=None,
                          pdr_mean=None,
                          last_ts_in_schedule=None,
                          current_sf_len=None,
                          normalized_ts_in_schedule=None,
                          reward=None
                          ):
        obs = ObservationsItem(
            timestamp=timestamp,
            alpha=alpha,
            beta=beta,
            delta=delta,
            power_wam=power_wam,
            power_mean=power_mean,
            power_normalized=power_normalized,
            delay_wam=delay_wam,
            delay_mean=delay_mean,
            delay_normalized=delay_normalized,
            pdr_wam=pdr_wam,
            pdr_mean=pdr_mean,
            last_ts_in_schedule=last_ts_in_schedule,
            current_sf_len=current_sf_len,
            normalized_ts_in_schedule=normalized_ts_in_schedule,
            reward=reward
        )
        self.observations.observations_list = obs

    def get_last_observations(self):
        obs = self.observations.observations_list[-1]
        last_obs = {
            "alpha": obs.alpha,
            "beta": obs.beta,
            "delta": obs.delta,
            "last_ts_in_schedule": obs.last_ts_in_schedule,
            "current_sf_len": obs.current_sf_len,
            "normalized_ts_in_schedule": obs.normalized_ts_in_schedule,
            "reward": obs.reward,
        }
        return last_obs

    def get_last_power_consumption(self, addr, power_samples, cycle_seq):
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            # FIXME: 3000 should not be set here
            power_samples.append((addr, 3000))
            return
        # Get the last energy sample of the node
        energy = self.nodes_info.get_energy_cycle_seq(addr, cycle_seq)
        # Calculate the avg delay
        if energy > 0:
            power_samples.append((addr, energy))
        else:
            power_samples.append((addr, 3000))
        return

    def get_avg_delay(self, addr, delay_samples, cycle_seq):
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            # FIXME: 2500 should not be set here
            delay_samples.append((addr, 2500))
            return
        # Get the avg delay of the current cycle sequence
        last_cycle_seq_samples = self.nodes_info.get_delay_cycle_seq(
            addr, cycle_seq)
        # Calculate the average of the cycle sequence.
        # Sum of delays
        sum_delay = 0
        for item in last_cycle_seq_samples:
            sum_delay += item.sampled_delay

        if len(last_cycle_seq_samples) > 0:
            avg_delay = sum_delay/len(last_cycle_seq_samples)
        else:
            avg_delay = 2500
        delay_samples.append((addr, avg_delay))
        return avg_delay

    def get_avg_pdr(self, addr, pdr_samples, cycle_seq):
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            # FIXME: 0 should not be set here
            pdr_samples.append((addr, 0))
            return
        # Get the avg delay of the current cycle sequence
        last_cycle_seq_samples = self.nodes_info.get_pdr_cycle_seq(
            addr, cycle_seq)
        # Calculate the average of the cycle sequence.
        # Last received sequence
        seq = 0
        for item in last_cycle_seq_samples:
            if item.seq > seq:
                seq = item.seq

        # Get the average pdr for this period
        if seq > 0:
            avg_pdr = len(last_cycle_seq_samples)/seq
        else:
            avg_pdr = 0
        if avg_pdr > 1.0:
            avg_pdr = 1.0
        pdr_samples.append((addr, avg_pdr))
        return
