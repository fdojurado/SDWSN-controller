from audioop import add
import pymongo
from pymongo.collation import Collation
from abc import ABC, abstractmethod


PACKETS = "packets"
NODES_INFO = "nodes_info"
FEATURES = "features"
SLOTFRAME_LEN = "slotframe_len"
ROUTING_PATHS = "routing_paths"
SCHEDULES = "schedules"
USER_REQUIREMENTS = "user_requirements"
OBSERVATIONS = "observations"


class Database(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def initialize(self):
        pass

    @property
    @abstractmethod
    def DATABASE(self):
        pass

    @abstractmethod
    def save_serial_packet(self):
        pass

    @abstractmethod
    def save_energy(self):
        pass

    @abstractmethod
    def save_neighbors(self):
        pass

    @abstractmethod
    def save_pdr(self):
        pass

    @abstractmethod
    def save_delay(self):
        pass

    @abstractmethod
    def save_observations(self):
        pass

    @abstractmethod
    def get_last_observations(self):
        pass

    def insert_one(self, collection, data):
        return self.DATABASE[collection].insert_one(data)

    def update_one(self, collection, filter, update, upsert, arrayFilters):
        return self.DATABASE[collection].update_one(filter, update, upsert=upsert, array_filters=arrayFilters)

    def aggregate(self, collection, pipeline):
        return self.DATABASE[collection].aggregate(pipeline)

    def find(self, collection, query):
        return self.DATABASE[collection].find(query)

    def delete_one(self, collection, query):
        return self.DATABASE[collection].delete_one(query)

    def distinct(self, collection, query):
        return self.DATABASE[collection].distinct(query)

    def print_documents(self, collection):
        for document in self.DATABASE[collection].find_one({}):
            print(document)

    def find_one(self, collection, query, sort=None):
        return self.DATABASE[collection].find_one(query, sort=sort)

    def delete_collection(self, collection):
        return self.DATABASE[collection].drop()

    def list_collections(self):
        for collection in self.DATABASE.list_collections():
            print(collection)

    # def exist(self, collection, addr):
    #     return self.DATABASE[collection].count_documents({"_id": addr}, limit=1) > 0

    # def push_doc(self, collection, addr, field, data):
    #     self.DATABASE[collection].update_one(
    #         {"_id": addr},
    #         {"$push": {field: data}},
    #         upsert=True
    #     )

    # def push_links(self, collection, data):
    #     self.DATABASE[collection].update_one(
    #         {
    #             "$or": [
    #                 {"$and": [{"scr": data['scr']},
    #                           {"dst": data['dst']}]},
    #                 {"$and": [{"scr": data['dst']}, {"dst": data['scr']}]}
    #             ]
    #         },
    #         {"$set": {"time": data['time'],
    #                   "scr": data['scr'],
    #                   "dst": data['dst'],
    #                   "rssi": data['rssi']}},
    #         upsert=True
    #     )

    # def update_energy(self, collection, addr, data):
    #     self.DATABASE[collection].update_one(
    #         {"_id": addr},
    #         {"$set": {"time": data['time'],
    #                   "energy": data['energy']}}
    #     )

    # def update_pdr(self, collection, addr, data):
    #     self.DATABASE[collection].update_one(
    #         {"_id": addr},
    #         {"$set": {"time": data['time'],
    #                   "pdr": data['pdr']}}
    #     )
