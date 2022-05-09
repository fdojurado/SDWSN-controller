import pymongo


PACKETS = "packets"
NODES_INFO = "nodes_info"
FEATURES = "features"
SLOTFRAME_LEN = "slotframe_len"
ROUTING_PATHS = "routing_paths"
SCHEDULES = "schedules"

class Database(object):
    URI = "mongodb://127.0.0.1:27017"
    DATABASE = None

    @staticmethod
    def initialise():
        client = pymongo.MongoClient(Database.URI)
        client.drop_database('SDN')
        Database.DATABASE = client["SDN"]
        # for db in client.list_databases():
        #     print(db)

    @staticmethod
    def insert(collection, data):
        return Database.DATABASE[collection].insert_one(data)

    @staticmethod
    def exist(collection, addr):
        return Database.DATABASE[collection].count_documents({"_id": addr}, limit=1) > 0

    @staticmethod
    def push_doc(collection, addr, field, data):
        Database.DATABASE[collection].update_one(
            {"_id": addr},
            {"$push": {field: data}},
            upsert=True
        )

    @staticmethod
    def push_links(collection, data):
        Database.DATABASE[collection].update_one(
            {
                "$or": [
                    {"$and": [{"scr": data['scr']},
                              {"dst": data['dst']}]},
                    {"$and": [{"scr": data['dst']}, {"dst": data['scr']}]}
                ]
            },
            {"$set": {"time": data['time'],
                      "scr": data['scr'],
                      "dst": data['dst'],
                      "rssi": data['rssi']}},
            upsert=True
        )

    @staticmethod
    def update_energy(collection, addr, data):
        Database.DATABASE[collection].update_one(
            {"_id": addr},
            {"$set": {"time": data['time'],
                      "energy": data['energy']}}
        )

    @staticmethod
    def update_pdr(collection, addr, data):
        Database.DATABASE[collection].update_one(
            {"_id": addr},
            {"$set": {"time": data['time'],
                      "pdr": data['pdr']}}
        )

    @staticmethod
    def update_one(collection, filter, update, upsert, arrayFilters):
        return Database.DATABASE[collection].update_one(filter, update, upsert=upsert, array_filters=arrayFilters)

    @staticmethod
    def aggregate(collection, pipeline):
        return Database.DATABASE[collection].aggregate(pipeline)

    @staticmethod
    def find(collection, query):
        return Database.DATABASE[collection].find(query)

    @staticmethod
    def delete_one(collection, query):
        return Database.DATABASE[collection].delete_one(query)

    @staticmethod
    def distinct(collection, query):
        return Database.DATABASE[collection].distinct(query)

    @staticmethod
    def print_documents(collection):
        for document in Database.DATABASE[collection].find_one({}):
            print(document)

    @staticmethod
    def find_one(collection, query, sort=None):
        return Database.DATABASE[collection].find_one(query, sort=sort)

    @staticmethod
    def delete_collection(collection):
        return Database.DATABASE[collection].drop()

    @staticmethod
    def list_collections():
        for collection in Database.DATABASE.list_collections():
            print(collection)
