import pandas as pd

def open_and_combine_csvs(csv_list):
	"""
	Pass a list of csv filenames, all imported into one pandas dataframe
	"""
	first_file = True
	for filename in csv_list:
		if first_file:
			df_final = pd.read_csv(filename)
			first_file = False
		else:
			df_temp = pd.read_csv(filename)
			print df_temp
			df_final = pd.concat([df_final, df_temp])
	return df_final


class Graph:
	"""
	Class with teams as nodes, scores as edges

	Team strength distributed around the graph via scores
	"""

	def __init__(self, leak=0.8):
		self.nodes = {}
		self.size = 0
		self.L = leak

	def add_node(self, team, redistribute = False):
		new_node = Vertex(team)
		if team not in self.nodes:
			self.size+=1
			self.nodes[team] = new_node
		if redistribute:
			self.redistribute_scoreranks()

	def add_edge(self, team_from, team_to, weight):
		if team_from not in self.nodes:
			self.add_node(team_from)
			if debug:
				print "Added node {}".format(team_from)
		v_from = self.nodes[team_from]

		if team_to not in self.nodes:
			self.add_node(team_to)
			if debug:
				print "Added node {}".format(team_to)
		v_to = self.nodes[team_to]			

		v_from.add_outgoing(v_to, weight)
		v_to.add_incoming(v_from, weight)

		if debug:
			print "Added edge from {} to {} with weight {}".format(team_from, team_to, weight)

	def print_scoreranks(self):
		scoreranks = []
		for team in self.nodes:
			scoreranks.append((team, self.nodes[team].scorerank))
		scoreranks.sort(key=lambda x: x[1], reverse=True)
		for p in scoreranks:
			print p
		print

	def iterate_scoreranks(self):
		"""
		Update all scoreranks by 1 iteration
		"""
		sink_nodes = []
		for team in self.nodes:
			# Calculate 'out' scorerank
			node = self.nodes[team]
			if node.outgoing_number == 0:
				sink_nodes.append(team)
				continue
			out_scorerank = (node.scorerank * 1.0 / node.outgoing_number)
			if debug:
				print "We have a node --> {}".format(node); print "Its scorerank outgoing is {}".format(out_scorerank)
				pass
			# Send it to its 'out' nodes (to temp slot)
			for nbr in node.outgoing:
				send_score = out_scorerank * node.outgoing[nbr]
				nbr.scorerank_updating += send_score
				if debug:
					print "   Sending to node --> {}".format(nbr); print "   Score sent is {}".format(send_score)
					pass		

		for team in self.nodes:
			# Add all incoming with random hop value and redistribution factor
			node = self.nodes[team]
			node.scorerank = self.L * node.scorerank_updating   # i.e. actual scorerank assigned
			node.scorerank += (1-self.L) * 1.0/self.size    # i.e. random hop
			node.scorerank_updating = 0

		if debug:
			print "Total scorerank after iterations: {}".format(self.total_scorerank())

		

	def redistribute_scoreranks(self):
		"""
		Initialise all scoreranks as 100%/self.size
		"""
		scorerank_for_all = 1.0 / self.size
		for team in self.nodes:
			self.nodes[team].scorerank = scorerank_for_all

	def iterate_scoreranks_n(self, N):
		"""
		Run scorerank iteration N times.
		"""
		for _ in range(N):
			self.iterate_scoreranks()

	def total_scorerank(self):
		total = 0
		for node in self.nodes:
			total += self.nodes[node].scorerank
		return total

	def __iter__(self):
		return __iter__(self.nodes)



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
		self.outgoing_number += weight
		self.outgoing[team_to] = self.outgoing.get(team_to, 0) + weight

	def add_incoming(self, team_from, weight=1):
		self.incoming_number += weight
		self.incoming[team_from] = self.incoming.get(team_from, 0) + weight

	def __repr__(self):
		return "Team: {}, Scorerank: {}, Out: {}, In: {}".format(
			self.team, self.scorerank, self.outgoing_number, self.incoming_number
			)



if __name__ == '__main__':

	# Debug mode?
	debug = False

	# Load CSV files into dataframe
	years = range(2012, 2013)
	if debug:
		years = range(0, 1)
	csv_list = ['{}.csv'.format(year) for year in years]
	df = open_and_combine_csvs(csv_list)

	# Create graph
	g = Graph(leak=0.5)
	for i in df.index:
		match_row = df.ix[i]
		home_team, away_team, home_score, away_score = match_row[[
			'HomeTeam',
			'AwayTeam',
			'FTHG',
			'FTAG'
		]]		
		if debug:
			print "Match number {}".format(i)
			print "{} vs {}, score {}:{}".format(home_team, away_team, home_score, away_score)
		g.add_edge(team_from = home_team, team_to = away_team, weight = int(away_score))
		g.add_edge(team_from = away_team, team_to = home_team, weight = int(home_score))
		
	g.redistribute_scoreranks()
	g.iterate_scoreranks_n(5)
	g.print_scoreranks()
