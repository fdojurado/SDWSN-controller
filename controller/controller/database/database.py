import pymongo


class Database(object):
    URI = "mongodb://127.0.0.1:27017"
    DATABASE = None

    @staticmethod
    def initialise():
        client = pymongo.MongoClient(Database.URI)
        client.drop_database('SDN')
        Database.DATABASE = client["SDN"]
        for db in client.list_databases():
            print(db)

    @staticmethod
    def insert(collection, data):
        return Database.DATABASE[collection].insert(data)

    @staticmethod
    def exist(collection, addr):
        return Database.DATABASE[collection].find({"_id": addr}).count() > 0

    @staticmethod
    def push_doc(collection, addr, field, data):
        Database.DATABASE[collection].update(
            {"_id": addr},
            {"$push": {field: data}}
        )

    @staticmethod
    def update_energy(collection, addr, data):
        Database.DATABASE[collection].update(
            {"_id": addr},
            {"$set": {"time": data['time'],
                      "energy": data['energy']}}
        )

    @staticmethod
    def update_pdr(collection, addr, data):
        Database.DATABASE[collection].update(
            {"_id": addr},
            {"$set": {"time": data['time'],
                      "pdr": data['pdr']}}
        )

    @staticmethod
    def find(collection, query):
        return Database.DATABASE[collection].find(query)

    @staticmethod
    def print_documents(collection):
        for document in Database.DATABASE[collection].find({}):
            print(document)

    @staticmethod
    def find_one(collection, query):
        return Database.DATABASE[collection].find_one(query)

    @staticmethod
    def list_collections():
        for collection in Database.DATABASE.list_collections():
            print(collection)
