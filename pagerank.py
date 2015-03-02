import pandas as pd
import matplotlib.pyplot as plt

plt.close()

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
		self.leak = leak

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

	def get_node(self, team_name):
		"""
		Return node with team name
		"""
		return self.nodes[team_name]

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
			node.scorerank = (1-self.leak) * node.scorerank_updating   # i.e. actual scorerank assigned
			node.scorerank += (self.leak) * 1.0/self.size    # i.e. random hop
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
		self.outgoing_number += weight
		self.outgoing[team_to] = self.outgoing.get(team_to, 0) + weight

	def add_incoming(self, team_from, weight=1):
		self.incoming_number += weight
		self.incoming[team_from] = self.incoming.get(team_from, 0) + weight

	def __repr__(self):
		return "Team: {}, Scorerank: {}, Out: {}, In: {}".format(
			self.team, self.scorerank, self.outgoing_number, self.incoming_number
			)

def convert_to_networkx(graph):
	"""
	Convert my graph to networkx graph for plotting purposes
	"""
	G=nx.DiGraph()
	# Get nodes in order of scorerank
	S = graph.get_scoreranks()
	teamnames = [x[0] for x in S]
	# Add all nodes
	for team in teamnames:
		G.add_node(team)
	for node_name in graph:
		node = graph.nodes[node_name]
		for nbr_name in node.outgoing:
			weight = node.outgoing[nbr_name]
			G.add_edge(node_name, nbr_name.team, weight=weight)
	return G

def plot_networkx_graph(networkx_graph, scoreranks, teamnames):
	"""
	Given a networkx graph and scoreranks and teamnames, plots circular graph 
	"""
	pos = nx.circular_layout(networkx_graph)
	node_sizes = [(x**3)*11000000 for x in scoreranks]
	node_colors = [(0.5,(x*(1.0/max(node_sizes)))**0.3,0.5) for x in node_sizes]
	nx.draw_networkx_nodes(networkx_graph, pos, nodelist=teamnames, node_size=node_sizes, node_color=node_colors)
	nx.draw_networkx_labels(networkx_graph, pos, nodelist=teamnames, font_size=8, font_family='sans-serif')
	e7=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] >= 7]
	e6=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 6]
	e5=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 5]
	e4=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 4]
	e3=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 3]
	e2=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 2]
	e1=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 1]
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e1,
                    width=1, alpha=0.2 ,edge_color='#9999dd')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e2,
                    width=1.5, alpha=0.3, edge_color='#7788bb')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e3,
                    width=2, alpha=0.4, edge_color='#6666aa')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e4,
                    width=2.5, alpha=0.5, edge_color='#336699')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e5,
                    width=3, alpha=0.6, edge_color='#225577')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e6,
                    width=3, alpha=0.65, edge_color='#113355')
	nx.draw_networkx_edges(networkx_graph, pos, edgelist=e7,
                    width=3.5, alpha=0.65, edge_color='#111111')



if __name__ == '__main__':

	# Debug mode?
	debug = False
	plotting = False

	# Load CSV files into dataframe
	years = range(2014, 2015)
	if debug:
		years = range(0, 1)
	csv_list = ['{}.csv'.format(year) for year in years]
	df = open_and_combine_csvs(csv_list)

	# Create graph
	g = Graph(leak=0.2)
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

	# Run scorerank iterations and save results
	scoreranks_df = pd.DataFrame()
	for iteration_no in range(7):		
		S = g.get_scoreranks()  # Tuples of [(team, scorerank), (team, scorerank)...]
		scoreranks = [x[1] for x in S]
		teamnames = [x[0] for x in S]
		scoreranks_df_temp = pd.DataFrame(scoreranks, 
			index = teamnames,
			columns=[iteration_no])  # Creates 1 column dataframe with latest scorerank
		scoreranks_df = pd.concat([scoreranks_df, scoreranks_df_temp], axis=1)
		g.iterate_scoreranks()

	# Plot scoreranks over iterations
	if plotting:
		print "Plotting scorerank values over each iteration performed..."
		ax = scoreranks_df.sort([iteration_no], ascending=False).ix[:,:].T.plot(lw=2)
		ax.set_xlabel('Iteration number')
		ax.set_ylabel('Scorerank')
		ax.set_title('How many iterations of scorerank until convergence?')
		ax.legend(loc='right')

	# Plot graph using networkx
	import networkx as nx
	networkx_graph = convert_to_networkx(g)
	plot_networkx_graph(networkx_graph, scoreranks, teamnames)


plt.show()
