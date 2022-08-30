# The BaseController class is an abstract class. Some functionalities are declared
# as abstract methods, classes that inherits from the BaseController should take care
# of them. The controller has four main modules: router, tsch scheduler, packet dissector,
# and communication interface.

from abc import ABC, abstractmethod

from sdwsn_controller.database.database import NODES_INFO


class BaseController(ABC):
    def __init__(
        self,
    ):
        pass

    """ Sequence functions """

    @abstractmethod
    def increase_sequence(self):
        pass

    @abstractmethod
    def increase_cycle_sequence(self):
        pass

    @abstractmethod
    def reset_pkt_sequence(self):
        pass

    @abstractmethod
    def get_cycle_sequence(self):
        pass

    """ Database functionalities """

    # @abstractmethod
    # def init_db(self):
    #     pass

    # @property
    @abstractmethod
    def db(self):
        pass

    @abstractmethod
    def export_db(self):
        pass

    """ Packet dissector functionalities """

    @property
    @abstractmethod
    def packet_dissector(self):
        pass

    @property
    @abstractmethod
    def sequence(self):
        pass

    @sequence.setter
    def sequence(self, num):
        self.sequence = num

    @property
    @abstractmethod
    def cycle_sequence(self):
        pass

    @cycle_sequence.setter
    def cycle_sequence(self, num):
        self.cycle_sequence = num

    """ Controller primitives """

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def wait(self):
        """
        This abstract should return a value (1 successful)
        :rtype: integer
         """
        pass

    @abstractmethod
    def wait_seconds(self):
        pass

    @abstractmethod
    def send(self):
        """
        This abstract should receive a data parameter
         """
        pass

    @abstractmethod
    def reliable_send(self):
        pass

    """ Reinforcement learning functionalities """

    @abstractmethod
    def save_observations(self, **env_kwargs):
        pass
        # self.db.save_observations(**env_kwargs)

    @abstractmethod
    def get_state(self):
        pass

    # @abstractmethod
    # def get_last_observations(self):
    #     pass
        # return self.db.get_last_observations()

    @abstractmethod
    def delete_info_collection(self):
        pass
        # self.db.delete_collection(NODES_INFO)

    @abstractmethod
    def calculate_reward(self):
        pass

    @property
    @abstractmethod
    def user_requirements(self):
        pass

    @user_requirements.setter
    @abstractmethod
    def user_requirements(self):
        pass

    """ Network information methods """

    @abstractmethod
    def get_network_links(self):
        pass

    """ Communication interface """

    @abstractmethod
    def comm_interface_start(self):
        pass

    @abstractmethod
    def comm_interface_stop(self):
        pass

    @abstractmethod
    def comm_interface_read(self):
        pass

    """ TSCH scheduler/schedule functions """

    @abstractmethod
    def send_tsch_schedules(self):
        pass

    @abstractmethod
    def last_active_tsch_slot(self):
        pass

    @abstractmethod
    def compute_tsch_schedule(self):
        pass

    """ Routing functions """

    @abstractmethod
    def send_routes(self):
        pass

    @abstractmethod
    def compute_dijkstra(self, G):
        pass
