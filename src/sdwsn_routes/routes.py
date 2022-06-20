# This file contains the up-to-date information of the routes currently
# deployed at the WSN.

import pandas as pd
import json
from datetime import datetime
from sdwsn_network_reconfiguration.network_config import job_type


class Routes:
    def __init__(self):
        self.column_names = ['scr', 'dst', 'via']
        self.routes = pd.DataFrame(columns=self.column_names)
        self.time = datetime.now().timestamp() * 1000.0

    def add_route(self, scr, dst, via):
        # Let's first check if the route is already in the dataframe
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

    # def save_historical_routes_db(self):
    #     if(not self.routes.empty):
    #         self.time = datetime.now().timestamp() * 1000.0
    #         data = {
    #             'time': self.time,
    #             'routes': self.routes.to_dict('records')
    #         }
    #         Database.insert("historical-routes", data)

    # def save_routes_db(self):
    #     # Insert all routes in the collection
    #     self.time = datetime.now().timestamp() * 1000.0
    #     for index, row in self.routes.iterrows():
    #         FWD_TABLE.fwd_add_entry(row['scr'], row['dst'], row['via'], 0)

    def routes_toJSON(self):
        # Build the routing job in a JSON format to be shared with the NC class
        # Hop limit sets the maximum of hops to bc this message. 255 means all.
        # {
        #   "job_type": "Routing",
        #   "routes":[
        #               {
        #                   "scr": row['scr'],
        #                   "dst": row['dst'],
        #                   "via": row['via']
        #                },
        #               {
        #                   "scr": row['scr'],
        #                   "dst": row['dst'],
        #                   "via": row['via']
        #                }
        #       ],
        #   "hop_limit": "255"
        # }
        json_message_format = '{"job_type": ' + \
            str(job_type.ROUTING)+', "routes":[]}'
        # parsing JSON string:
        json_message = json.loads(json_message_format)
        # self.print_routes()
        # hop_limit = 0
        for _, row in self.routes.iterrows():
            data = {"scr": row['scr'], "dst": row['dst'], "via": row['via']}
            json_message["routes"].append(data)
            # rank = get_rank(row['scr'])
            # if (rank > hop_limit):
            #     hop_limit = rank
        json_message["hop_limit"] = 255
        json_dump = json.dumps(json_message, indent=4, sort_keys=True)
        print(json_dump)
        return json_dump