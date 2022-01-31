

class Connected_graph:
	def __init__(self):
		self.N = 100000
		# To keep correct and reverse direction
		self.gr1 = {}
		self.gr2 = {}

		self.vis1 = [0] * self.N
		self.vis2 = [0] * self.N

	# Function to add edges
	def add_edge(self, u, v) :

		if u not in self.gr1 :
			self.gr1[u] = []
			
		if v not in self.gr2 :
			self.gr2[v] = []
			
		self.gr1[u].append(v)
		self.gr2[v].append(u)

	# DFS function
	def dfs1(self,x) :
		self.vis1[x] = True
		if x not in self.gr1 :
			self.gr1[x] = {}
			
		for i in self.gr1[x] :
			if (not self.vis1[i]) :
				self.dfs1(i)

	# DFS function
	def dfs2(self,x) :

		self.vis2[x] = True

		if x not in self.gr2 :
			self.gr2[x] = {}
			
		for i in self.gr2[x] :
			if (not self.vis2[i]) :
				self.dfs2(i)

	def is_connected(self,n) :
		
		# Call for correct direction
		self.vis1 = [False] * len(self.vis1)
		self.dfs1(1)
		
		# Call for reverse direction
		self.vis2 = [False] * len(self.vis2)
		self.dfs2(1)
		
		for i in range(1, n + 1) :
			
			# If any vertex it not visited in any direction
			# Then graph is not connected
			if (not self.vis1[i] and not self.vis2[i]) :
				return False
				
		# If graph is connected
		return True
