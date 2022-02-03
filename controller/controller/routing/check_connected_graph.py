from controller.routing.graph import Graph

''' Vertex extends the class Node and represents each vertex in the graph'''


class Connected_graph(Graph):
    def __init__(self, graph, start):
        self.graph = graph
        self.start = start
        self.intialization()

    def intialization(self):
        for node in self.graph.nodes:
            if node == self.start:
                node.visited = 0

    # DFS function
    def dfs(self, v):
        vertix = v
        # print("running dfs with source node ", vertix)
        if(vertix.visited == True):
            # print("vertix ", vertix, " already visted")
            return
        vertix.visited = True
        # print("vertix ", vertix, " marked as visited")
        for neighbour in vertix.neighbors:
            # print("processing neighbour ", neighbour, " of vertix ", vertix)
            nb = self.graph.find_node(neighbour[0].value)
            if(nb.visited == False):
                self.dfs(nb)

    def run(self):
        source = self.graph.find_node(self.start)
        self.dfs(source)
        return self.is_connected()

    def is_connected(self):
        for v in self.graph.nodes:
            if(v.visited == False):
                return False
        return True
