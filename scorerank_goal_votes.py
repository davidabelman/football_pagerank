# Scorerank model for premier league 2013-2014

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

	def __init__(self, leak=0.2):
		self.nodes = {}
		self.size = 0
		self.leak = leak

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
		for team in self.nodes:
			# Calculate 'out' scorerank
			node = self.nodes[team]
			if node.outgoing_number == 0:
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
			node.scorerank += (self.leak) * 1.0    # i.e. random hop
			node.scorerank_updating = 0

		if debug:
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
	Given a networkx graph and scoreranks and teamnames, plots circular graph. A bit hacky.
	"""
	# Circular layout
	pos = nx.circular_layout(networkx_graph)
	# List of node sizes & colours  (NB exponential to highlight differences visually)
	node_sizes = [(x**2.9)*1200 for x in scoreranks]
	node_colors = [(0.5,(x*(1.0/max(node_sizes)))**0.3,0.5) for x in node_sizes]
	# Draw nodes and labels
	nx.draw_networkx_nodes(networkx_graph, pos, nodelist=teamnames, node_size=node_sizes, node_color=node_colors)
	nx.draw_networkx_labels(networkx_graph, pos, nodelist=teamnames, font_size=8, font_family='sans-serif')
	# List of edges to draw (of different weights)
	e7=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] >= 7]
	e6=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 6]
	e5=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 5]
	e4=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 4]
	e3=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 3]
	e2=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 2]
	e1=[(u,v) for (u,v,d) in networkx_graph.edges(data=True) if d['weight'] == 1]
	# Draw the edges (each with different thickness/colour/alpha settings)
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


def calculate_table(df):
	"""
	Return points table as pd.Series given input dataframe of results
	"""
	final_table = {}
	results = df['FTR']
	for i in results.index:
		match_row = df.ix[i]
		result = results.ix[i]
		points_given = []
		if result == 'H':
			points_given.append((match_row['HomeTeam'],3))
		if result == 'A':
			points_given.append((match_row['AwayTeam'],3))
		if result == 'D':
			points_given.append((match_row['HomeTeam'],1))
			points_given.append((match_row['AwayTeam'],1))
		for team,points in points_given:
			final_table[team] = final_table.get(team, 0) + points
	return pd.Series(final_table)


if __name__ == '__main__':

	# Debug mode?
	debug = False
	plotting = True

	# Load CSV files into dataframe
	years = range(2014, 2015)  # Just 2014.csv for now
	if debug:
		years = range(0, 1)  # 0.csv for testing purposes
	csv_list = ['{}.csv'.format(year) for year in years]
	df = open_and_combine_csvs(csv_list)

	# Create graph
	g = Graph(leak=0.2)
	for i in df.index:
		# Iterate through each match, pulling out Home/Away teams and goals scored
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
		# Add edges for each team's goals
		g.add_edge(team_from = home_team, team_to = away_team, weight = int(away_score))
		g.add_edge(team_from = away_team, team_to = home_team, weight = int(home_score))		

	# Set each scorerank to 1 to start with
	g.redistribute_scoreranks()

	# Run scorerank iterations and save results
	scoreranks_df = pd.DataFrame()
	for iteration_no in range(10):
		# Record current scoreranks	in a dataframe (for plotting purposes)
		S = g.get_scoreranks()  # Tuples of [(team, scorerank), (team, scorerank)...]
		scoreranks = [x[1] for x in S]
		teamnames = [x[0] for x in S]
		scoreranks_df_temp = pd.DataFrame(scoreranks, 
			index = teamnames,
			columns=[iteration_no])  # Creates 1 column dataframe with latest scorerank
		scoreranks_df = pd.concat([scoreranks_df, scoreranks_df_temp], axis=1)
		# Iterate the scorerank calculation
		g.iterate_scoreranks()

	# Plot scorerank values over iterations
	if plotting:
		fig1 = plt.figure()
		print "Plotting scorerank values over each iteration performed..."
		ax = scoreranks_df.sort([iteration_no], ascending=False).ix[:,:].T.plot(lw=2)
		ax.set_xlabel('Iteration number')
		ax.set_ylabel('Scorerank')
		ax.set_title('How many iterations of scorerank until convergence?')
		ax.legend(loc='right')

	# Plot overall graph using networkx
	if plotting:
		fig2 = plt.figure()
		import networkx as nx
		networkx_graph = convert_to_networkx(g)
		plot_networkx_graph(networkx_graph, scoreranks, teamnames)

	# Plot scorerank vs. premier league table as scatter chart
	if plotting:
		pl_table_points_series = calculate_table(df)
		scoreranks_series = pd.Series(dict(g.get_scoreranks()))
		combined = pd.concat([pl_table_points_series, scoreranks_series], axis=1)
		ranks = combined.rank()
		fig3 = plt.figure()
		plt.scatter(ranks[0], ranks[1], s=30)
		plt.title('Comparing scorerank with final Premier League (2014) table')
		plt.xlabel('Premier league ranking (high=top)')
		plt.ylabel('Scorerank position (high=top)')
		plt.xlim(0,21)
		plt.ylim(0,21)
		for label, x, y in zip(ranks.index, ranks[0], ranks[1]):
		    plt.annotate(
		            label, 
		            xy = (x, y), xytext = (20, 5),
		            textcoords = 'offset points', ha = 'right', va = 'bottom')

	
plt.show()



