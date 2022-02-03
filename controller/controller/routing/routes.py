# This file contains the up-to-date information of the routes currently
# deployed at the WSN.

import pandas as pd


class Routes:
    def __init__(self):
        print("initialzing the routes")
        self.column_names = ['src', 'dst', 'via']
        self.routes = pd.DataFrame(columns=self.column_names)

    def add_route(self, src, dst, via):
        print("adding route ", src, "-", dst, " via ", via)
        # Let's firts check if the route is already in the dataframe
        if (((self.routes['src'] == src) & (self.routes['dst'] == dst) & (self.routes['via'] == via)).any() |
                ((self.routes['src'] == dst) & (self.routes['dst'] == src) & (self.routes['via'] == via)).any()):
            print("route already in dataframe")
            return
        else:
            df = pd.DataFrame([[src, dst, via]], columns=self.column_names)
            self.routes = pd.concat(
                [self.routes, df], ignore_index=True)  # adding a row
        self.print_routes()

    def print_routes(self):
        print("printing routes")
        print(self.routes.to_string())

    def remove_route(self, src, dst, via):
        print("removing route ", src, "-", dst, " via", via)
        df = self.routes
        idx = df.index[df['src'] == src & df['dst']
                       == dst & df['via'] == via]
        # Check that the index is not empty. Which means we find the target row.
        if(idx.empty):
            print('route/index not found')
            return
        print("index found")
        print(idx)
        print("route found at index")
        print(df.loc[idx])
        self.routes = df.drop(idx)
        print("route removed")
        self.print_routes()

    def clear_routes(self):
        print("clearing all routes")
        self.routes.drop(self.routes.index, inplace=True)
