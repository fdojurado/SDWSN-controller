# This file contains the up-to-date information of the routes currently
# deployed at the WSN.

import pandas as pd
import json
from datetime import datetime
from abc import ABC, abstractmethod
from rich.table import Table
from rich.console import Console
from rich.text import Text
import logging

logger = logging.getLogger(__name__)


class Routes(ABC):
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
        logger.info(self.routes.to_string())

    def print_routes_table(self):
        table = Table(title="Routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for _, row in self.routes.iterrows():
            table.add_row(row['scr'],
                          row['dst'], row['via'])

        def log_table(rich_table):
            """Generate an ascii formatted presentation of a Rich table
            Eliminates any column styling
            """
            console = Console(width=150)
            with console.capture() as capture:
                console.print(rich_table)
            return Text.from_ansi(capture.get())

        logger.info(f"Routing table\n{log_table(table)}")

        

    def remove_route(self, scr, dst, via):
        df = self.routes
        idx = df.index[df['scr'] == scr & df['dst']
                       == dst & df['via'] == via]
        # Check that the index is not empty. Which means we find the target row.
        if(idx.empty):
            logger.info('route/index not found')
            return
        self.routes = df.drop(idx)
        self.print_routes()

    def clear_routes(self):
        self.routes.drop(self.routes.index, inplace=True)

    # def routes_toJSON(self):
    #     # Build the routing job in a JSON format to be shared with the NC class
    #     # Hop limit sets the maximum of hops to bc this message. 255 means all.
    #     # {
    #     #   "job_type": "Routing",
    #     #   "routes":[
    #     #               {
    #     #                   "scr": row['scr'],
    #     #                   "dst": row['dst'],
    #     #                   "via": row['via']
    #     #                },
    #     #               {
    #     #                   "scr": row['scr'],
    #     #                   "dst": row['dst'],
    #     #                   "via": row['via']
    #     #                }
    #     #       ],
    #     #   "hop_limit": "255"
    #     # }
    #     json_message_format = '{"job_type": ' + \
    #         str(job_type.ROUTING)+', "routes":[]}'
    #     # parsing JSON string:
    #     json_message = json.loads(json_message_format)
    #     # self.print_routes()
    #     # hop_limit = 0
    #     for _, row in self.routes.iterrows():
    #         data = {"scr": row['scr'], "dst": row['dst'], "via": row['via']}
    #         json_message["routes"].append(data)
    #         # rank = get_rank(row['scr'])
    #         # if (rank > hop_limit):
    #         #     hop_limit = rank
    #     json_message["hop_limit"] = 255
    #     json_dump = json.dumps(json_message, indent=4, sort_keys=True)
    #     logger.info(json_dump)
    #     return json_dump
