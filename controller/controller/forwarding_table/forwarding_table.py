""" This class manages the forwading table of the entire SDWSN. It maintains the forwading paths
according to the deployed routes.

The structure of the database is as follows.

node_id:{
    "routes":{
        time:
        scr:
        dst:
        via:
        deployed:
    }
} """

from controller.database.database import Database
import pandas as pd
from datetime import datetime
import networkx as nx
import json

FORWARDING_TABLE = "fwd_table"
MAX_TABLE_SIZE = 10


class FWD_TABLE(object):

    @staticmethod
    def fwd_get_table():
        # Loads the fwd_table collection into a DF
        return pd.DataFrame(list(Database.find(FORWARDING_TABLE, {})))

    @staticmethod
    def fwd_num_elements(df):
        return df.shape[0]

    @staticmethod
    def fwd_get_graph(source, target, attribute):
        db = Database.find_one(FORWARDING_TABLE, {})
        df = pd.DataFrame()
        Graph = nx.Graph()
        if(db is None):
            return df, Graph
        df = pd.DataFrame(list(Database.find(FORWARDING_TABLE, {})))
        stdf = df['routes']
        df = pd.DataFrame(stdf.tolist()[0])
        Graph = nx.from_pandas_edgelist(
            df, source=source, target=target, edge_attr=attribute)
        return df, Graph

    @staticmethod
    def fwd_insert_item(scr, dst, via, deployed):
        print("inserting item: ", scr, "-", dst, " via:",
              via, " (deployed: ", deployed, ")")
        time = datetime.now().timestamp() * 1000.0
        data = {
            'time': time,
            'scr': scr,
            'dst': dst,
            'via': via,
            'deployed': deployed
        }
        filter = {"_id": scr}
        update = {"$push": {'routes': data}}
        Database.update_one(
            FORWARDING_TABLE, filter, update, True, None)

    @staticmethod
    def fwd_get_item(scr, dst, via):
        query = {"$and": [
            {"_id": scr},
            {"routes.scr": scr},
            {"routes.dst": dst},
            {"routes.via": via},
        ]}
        db = Database.find_one(FORWARDING_TABLE, query)
        if(db is None):
            print("item does not exist in ", FORWARDING_TABLE)
        return db

    @staticmethod
    def fwd_delete_destination(node, dst):
        query = {"$and": [
            {"_id": node},
            {"routes.dst": dst},
        ]}
        Database.remove(FORWARDING_TABLE, query, True)

    @staticmethod
    def fwd_add_entry(scr, dst, via, deployed):
        print("attempt to add: ", scr, "-", dst, " via:",
              via, " (deployed: ", deployed, ")")
        # Update df
        fwd_df = FWD_TABLE.fwd_get_table()
        # Continue if df is not empty
        if(not fwd_df.empty):
            # Lets filter the table by node id
            df = fwd_df[(fwd_df["_id"] == scr)]
            print("printing df of add entry for specific node")
            print(df.to_string())
            if(df.empty):
                FWD_TABLE.fwd_insert_item(scr, dst, via, deployed)
                return
            # Get the routes field
            stdf = df['routes']
            df = pd.DataFrame(stdf.tolist()[0])
            print(df.to_string())
            # Check if the route already exist
            if ((df['scr'] == scr) & (df['dst'] == dst) & (df['via'] == via)).any():
                print("route already exists")
                return
            # check if destination exist. May be the via changed.
            if(df['dst'] == dst).any():
                print("We are changing the via")
                # Then, we delete the old route and insert the new one
                FWD_TABLE.fwd_delete_destination(scr, dst)
            # Check if we still have room for another entry
            if(FWD_TABLE.fwd_num_elements(df) > MAX_TABLE_SIZE):
                # Delete old entry
                last_route = df.iloc[-1]
                FWD_TABLE.fwd_delete_destination(scr, last_route['dst'])
            FWD_TABLE.fwd_insert_item(scr, dst, via, deployed)
        else:
            FWD_TABLE.fwd_insert_item(scr, dst, via, deployed)
