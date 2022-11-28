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
from sdwsn_controller.database.database import Database
from sdwsn_controller.packet.packet import SDN_NAPL_LEN, NA_Packet_Payload

import time

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

    def __repr__(self) -> str:
        return "PDR(timestamp: {}, cycle seq: {}, seq: {})".format(
            self.__timestamp,
            self.__cycle_seq,
            self.__seq)


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

    def __repr__(self) -> str:
        return "Delay(timestamp: {}, cycle seq: {}, seq: {}, sampled delay: {})".format(
            self.__timestamp,
            self.__cycle_seq,
            self.__seq,
            self.__sampled_delay)


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

    # def get(self):
    #     data = {
    #         'timestamp': self.__timestamp,
    #         'cycle_seq': self.__cycle_seq,
    #         'seq': self.__seq,
    #         'ewma_energy': self.__ewma_energy
    #     }
    #     return data

    def __repr__(self) -> str:
        return "Energy(timestamp: {}, cycle seq: {}, seq: {}, ewma energy: {})".format(
            self.__timestamp,
            self.__cycle_seq,
            self.__seq,
            self.__ewma_energy
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

    # def get(self):
    #     data = {
    #         'timestamp': self.__timestamp,
    #         'dst': self.__dst,
    #         'rssi': self.__rssi,
    #         'etx': self.__etx
    #     }
    #     return data

    def __repr__(self) -> str:
        return "Neighbor(timestamp: {}, dst: {}, rssi: {}, etx: {})".format(
            self.__timestamp,
            self.__dst,
            self.__rssi,
            self.__etx
        )


class NodesInfoItem():
    def __init__(
        self,
        node_id: str = None,
        # pdr: list = None,
        # delay: list = None,
        # energy: list = None,
        # neighbors: list = None
        rank: int = 0
    ):
        assert isinstance(node_id, str)
        # assert isinstance(pdr, list)
        # assert isinstance(delay, list)
        # assert isinstance(energy, list)
        # assert isinstance(neighbors, str)
        assert isinstance(rank, int)
        self.__node_id = node_id
        self.__pdr = []
        self.__delay = []
        self.__energy = []
        self.__neighbors = []
        self.__neighbors_timestamp = 0
        self.__rank = rank

    def get(self):
        data = {
            'node_id': self.node_id,
            'pdr': self.pdr,
            'delay': self.delay,
            'energy': self.energy,
            'rank': self.rank,
            'neighbors': self.nbr,
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
        self.last_timestamp = val.timestamp

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

    def get_last_index_wsn(self):
        """
        Gets the greater node id of all WSN. The last index is
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
        return max_node_id

    def get_sensor_nodes_in_order(self):
        index_array = []
        for item in self.nodes_info_list:
            for nbr in item.nbr:
                node_id = item.node_id
                index_array.append(float(node_id))
                index_array.append(float(nbr.dst))
        unique_node_ids = self.unique(index_array)
        return unique_node_ids.sort()


class ObservationsItem():
    def __init__(
        self,
        timestamp: float = 0.0,
        alpha: float = 0.0,
        beta: float = 0.0,
        delta: float = 0.0,
        power_wam: float = 0.0,
        power_avg: float = 0.0,
        power_normalized: float = 0.0,
        delay_wam: float = 0.0,
        delay_avg: float = 0.0,
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
        assert isinstance(power_avg, float)
        assert isinstance(power_normalized, float)
        assert isinstance(delay_wam, float)
        assert isinstance(delay_avg, float)
        assert isinstance(delay_normalized, float)
        assert isinstance(pdr_wam, float)
        assert isinstance(pdr_mean, float)
        assert isinstance(last_ts_in_schedule, int)
        assert isinstance(current_sf_len, int)
        assert isinstance(normalized_ts_in_schedule, float)
        assert isinstance(reward, float)
        self.__timestamp = timestamp
        self.__alpha = alpha
        self.__beta = beta
        self.__delta = delta
        self.__power_wam = power_wam
        self.__power_avg = power_avg
        self.__power_normalized = power_normalized
        self.__delay_wam = delay_wam
        self.__delay_avg = delay_avg
        self.__delay_normalized = delay_normalized
        self.__pdr_wam = pdr_wam
        self.__pdr_mean = pdr_mean
        self.__last_ts_in_schedule = last_ts_in_schedule
        self.__current_sf_len = current_sf_len
        self.__normalized_ts_in_schedule = normalized_ts_in_schedule
        self.__reward = reward

    def get(self):
        data = {
            'timestamp': self.timestamp,
            'alpha': self.alpha,
            'beta': self.beta,
            'delta': self.delta,
            'power_wam': self.power_wam,
            'power_avg': self.power_avg,
            'power_normalized': self.power_normalized,
            'delay_wam': self.delay_wam,
            'delay_avg': self.delay_avg,
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
    def power_avg(self):
        return self.__power_avg

    @property
    def power_normalized(self):
        return self.__power_normalized

    @property
    def delay_wam(self):
        return self.__delay_wam

    @property
    def delay_avg(self):
        return self.__delay_avg

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

    def export_collection(self):
        pass

    def save_serial_packet(self):
        pass

    def __exist(self, collection, lookup_field, val):
        for item in collection:
            data = item.get()[lookup_field]
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
        print(f"asking for rank of node {addr}")
        if (addr == "1.0"):
            return 0
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            return
        print(f"rank: {node_info['rank']}")
        return node_info['rank']

    def get_last_slotframe_len(self):
        pass

    def get_last_delay(self):
        pass

    def get_last_pdr(self):
        pass

    def get_last_timestamp(self, collection, field, addr):
        pass

    def get_last_nbr(self, addr):
        node_info = self.__exist(
            self.nodes_info.nodes_info_list, 'node_id', addr)
        if node_info is None:
            return None
        # Get last timestamp
        last_timestamp = node_info.nbr_timestamp()

        print(f"last timestamp: {last_timestamp}")
        print(f"item: {node_info}")

        last_nbrs = []
        for nbr in node_info.nbr:
            if nbr.timestamp == last_timestamp:
                last_nbrs.append(nbr)

        print(f"last nbrs:{last_nbrs}")

        return last_nbrs

    def get_number_of_sensors(self):
        return self.nodes_info.length()

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

    def get_last_power_consumption(self):
        obs = self.observations.observations_list[-1]
        energy = obs.

    def get_avg_delay(self):
        pass

    def get_avg_pdr(self):
        pass
