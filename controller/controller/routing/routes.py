# This file contains the up-to-date information of the routes currently
# deployed at the WSN.

import pandas as pd
from controller.database.database import Database
from datetime import datetime


class Routes:
    def __init__(self):
        self.column_names = ['scr', 'dst', 'via']
        self.routes = pd.DataFrame(columns=self.column_names)
        self.time = datetime.now().timestamp() * 1000.0

    def add_route(self, scr, dst, via):
        # Let's firts check if the route is already in the dataframe
        if ((self.routes['scr'] == scr) & (self.routes['dst'] == dst) & (self.routes['via'] == via)).any():
            return
        else:
            df = pd.DataFrame([[scr, dst, via]], columns=self.column_names)
            self.routes = pd.concat(
                [self.routes, df], ignore_index=True)  # adding a row

    def print_routes(self):
        print(self.routes.to_string())

    def remove_route(self, scr, dst, via):
        df = self.routes
        idx = df.index[df['scr'] == scr & df['dst']
                       == dst & df['via'] == via]
        # Check that the index is not empty. Which means we find the target row.
        if(idx.empty):
            print('route/index not found')
            return
        self.routes = df.drop(idx)
        self.print_routes()

    def clear_routes(self):
        self.routes.drop(self.routes.index, inplace=True)

    def save_historical_routes_db(self):
        if(not self.routes.empty):
            self.time = datetime.now().timestamp() * 1000.0
            data = {
                'time': self.time,
                'routes': self.routes.to_dict('records')
            }
            Database.insert("historical-routes", data)

    def save_routes_db(self):
        Database.delete_collection("routes")
        # Insert all routes in the collection
        self.time = datetime.now().timestamp() * 1000.0
        for index, row in self.routes.iterrows():
            # Here, we first check if the route already exist in sensor node.
            db = Database.find_one(
                "nodes", {"$and": [
                    {"_id": row['scr']},
                    {"dst": row['dst']},
                    {"via": row['via']}
                ]
                }
            )
            deployed = 0
            if(db is not None):
                deployed = 1
            data = {
                'time': self.time,
                'scr': row['scr'],
                'dst': row['dst'],
                'via': row['via'],
                'deployed': deployed
            }
            Database.insert("routes", data)
