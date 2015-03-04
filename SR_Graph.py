class Graph:
	"""
	Class with teams as nodes, scores as edges

	Team strength distributed around the graph via scores
	"""

	def __init__(self, leak=0.2):
		self.nodes = {}
		self.size = 0
		self.leak = leak
		self.debug = False

	def add_node(self, team, redistribute = False):
		"""
		Add a node to the graph
		"""
		new_node = Vertex(team)
		if team not in self.nodes:
			self.size+=1
			self.nodes[team] = new_node
		if redistribute:
			self.redistribute_scoreranks()

	def add_edge(self, team_from, team_to, weight):
		"""
		Add an edge between two teams, with an associated weight (adds teams if not already present)
		"""
		if team_from not in self.nodes:
			self.add_node(team_from)
			if self.debug:
				print "Added node {}".format(team_from)
		v_from = self.nodes[team_from]

		if team_to not in self.nodes:
			self.add_node(team_to)
			if self.debug:
				print "Added node {}".format(team_to)
		v_to = self.nodes[team_to]			

		v_from.add_outgoing(v_to, weight)
		v_to.add_incoming(v_from, weight)

		if self.debug:
			print "Added edge from {} to {} with weight {}".format(team_from, team_to, weight)

	def get_node(self, team_name):
		"""
		Return node with team name
		"""
		return self.nodes[team_name]

	def get_scorerank(self, team_name):
		"""
		Return scorerank of team
		"""
		team_node = self.get_node(team_name)
		return team_node.scorerank

	def get_scoreranks(self):
		scoreranks = []
		for team in self.nodes:
			scoreranks.append((team, self.nodes[team].scorerank))
		scoreranks.sort(key=lambda x: x[1], reverse=True)
		return scoreranks

	def iterate_scoreranks(self):
		"""
		Update all scoreranks by 1 iteration
		"""
		for team in self.nodes:
			# Calculate 'out' scorerank
			node = self.nodes[team]
			if node.outgoing_number == 0:
				continue
			out_scorerank = (node.scorerank * 1.0 / node.outgoing_number)
			if self.debug:
				print "We have a node --> {}".format(node); print "Its scorerank outgoing is {}".format(out_scorerank)
				pass
			# Send it to its 'out' nodes (to temp slot)
			for nbr in node.outgoing:
				send_score = out_scorerank * node.outgoing[nbr]
				nbr.scorerank_updating += send_score
				if self.debug:
					print "   Sending to node --> {}".format(nbr); print "   Score sent is {}".format(send_score)
					pass		

		for team in self.nodes:
			# Add all incoming with random hop value and redistribution factor
			node = self.nodes[team]
			node.scorerank = (1-self.leak) * node.scorerank_updating   # i.e. actual scorerank assigned
			node.scorerank += (self.leak) * 1.0    # i.e. random hop
			node.scorerank_updating = 0

		if self.debug:
			print "Total scorerank after iterations: {}".format(self.total_scorerank())		

	def redistribute_scoreranks(self):
		"""
		Initialise all scoreranks as 1
		"""
		scorerank_for_all = 1.0
		for team in self.nodes:
			self.nodes[team].scorerank = scorerank_for_all

	def iterate_scoreranks_n(self, N):
		"""
		Run scorerank iteration N times
		"""
		for _ in range(N):
			self.iterate_scoreranks()

	def total_scorerank(self):
		"""
		Returns the sum of all scoreranks in the graph
		"""
		total = 0
		for node in self.nodes:
			total += self.nodes[node].scorerank
		return total

	def print_graph(self):
		"""
		Prints all nodes and connections in the graph
		"""
		for node in self.nodes:
			print self.nodes[node]
			print "  Out:"
			for subnode in self.nodes[node].outgoing:				
				print "  - {} ({})".format(subnode.team, self.nodes[node].outgoing[subnode])
			print "  In:"
			for subnode in self.nodes[node].incoming:					
				print "  - {} ({})".format(subnode.team, self.nodes[node].incoming[subnode])

	def __repr__(self):
		return "Graph with {} nodes".format(self.size)

	def __iter__(self):
		return iter(self.nodes)



class Vertex:

	def __init__(self, team):
		self.team = team
		self.scorerank = None
		self.scorerank_updating = 0
		self.outgoing = {}
		self.incoming = {}
		self.outgoing_number = 0
		self.incoming_number = 0

	def add_outgoing(self, team_to, weight=1):
		"""
		Add an outoing connection from node with a weight
		"""
		self.outgoing_number += weight
		self.outgoing[team_to] = self.outgoing.get(team_to, 0) + weight

	def add_incoming(self, team_from, weight=1):
		"""
		Add an incoming connection from node with a weight
		"""
		self.incoming_number += weight
		self.incoming[team_from] = self.incoming.get(team_from, 0) + weight

	def __repr__(self):
		return "Team: {}, Scorerank: {}, Out: {}, In: {}".format(
			self.team, self.scorerank, self.outgoing_number, self.incoming_number
			)
