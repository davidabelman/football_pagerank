# Python script to correlate bookmaker's odds with simple results of PageRank algorithm
# As described on https://davidabelman.wordpress.com/2015/03/04/146/

import pandas as pd
import SR_Graph
import matplotlib.pyplot as plt
import math
reload(SR_Graph)

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
			df_final = pd.concat([df_final, df_temp], ignore_index=True)
	return df_final

def create_scorerank_graph(matches_to_use, option = None):
	"""
	Create a scorerank graph
	"""
	G = SR_Graph.Graph(leak=0.2)
	for i in matches_to_use.index:
		# Iterate through each match, pulling out Home/Away teams and goals scored
		match_row = matches_to_use.ix[i]
		home_team, away_team, home_score, away_score = match_row[[
			'HomeTeam',
			'AwayTeam',
			'FTHG',
			'FTAG'
		]]		
		# Add edges for each team's goals
		G.add_edge(team_from = home_team, team_to = away_team, weight = int(away_score))
		G.add_edge(team_from = away_team, team_to = home_team, weight = int(home_score))		

	# Set each scorerank to 1 to start with and iterate
	G.redistribute_scoreranks()
	G.iterate_scoreranks_n(5)
	return G

def bookie_calculator(home_odds, draw_odds, away_odds, fn=None):
	"""
	Given a bookie's odds for home/draw/away, outputs a number from -1 to 1

	-1 indicates 100% certain away win, +1 is 100% certain home win
	"""
	# Calculate percentage odds
	h_pc = 1.0/home_odds
	d_pc = 1.0/draw_odds
	a_pc = 1.0/away_odds
	total_pc = h_pc + d_pc + a_pc
	result = (1*h_pc - 1*a_pc)*1.0 / total_pc
	if fn==None:
		return result
	else:
		# Could add some function here to skew results, e.g. sigmoid, squared, etc.
		return result

def to_datetime(d):
	"""
	Converts string date to datetime
	"""
	import datetime
	return datetime.datetime.strptime(d, '%d/%m/%y')

def enough_data(match_df, hometeam, awayteam):
	"""
	Returns True if both teams appear in historical matches over threshold
	"""
	hometeam_appears_number = sum(match_df['HomeTeam']==hometeam)+sum(match_df['AwayTeam']==hometeam)
	awayteam_appears_number = sum(match_df['HomeTeam']==awayteam)+sum(match_df['AwayTeam']==awayteam)
	if hometeam_appears_number >= matches_required_for_prediction:
		if awayteam_appears_number >= matches_required_for_prediction:
			return True
	return False


# Main script below:
# Will loop through all matches in loaded data
# If there is enough historical data it will build ScoreRank model on historic games
# Uses ScoreRank model to predict game outcome
# Looks at Bookie prediction (converts 3 odds into single metric)
# Compares ScoreRank vs Bookie in correlation chart once all matches analysed
# Outputs R^2 value

if __name__ == '__main__':

	# Settings
	historical_match_number = 380
	matches_required_for_prediction = 3
	debug = True
	list_to_save = []

	# Load CSV files into dataframe
	years = range(2013, 2015)  
	csv_list = ['{}.csv'.format(year) for year in years]
	df = open_and_combine_csvs(csv_list)
	if debug:
		print "Combined CVs and put into 'df' dataframe"

	# Convert dates to datetime and sort
	df['Date'] = df['Date'].apply(to_datetime)
	df.sort(['Date'], inplace=True)
	df = df.reindex(range(len(df)))
	if debug:
		print "Converted dates to datetimes"
		print df['Date'].head()

	# For each line in df
	previous_date = None
	for i in df.index:		
		match_row = df.ix[i]

		# Skip if not enough historical matches
		if i<historical_match_number:
			if debug:
				print "i = {}, < {} so skipping...".format(i, historical_match_number)
			continue
		if debug:
			print "i = {}, > {} so continuing...".format(i, historical_match_number)

		# If date not previously considered, create a new model:
		match_date = match_row['Date']		
		if match_date != previous_date:
			if debug:
				print "Match date ({}) not equal to previous, creating new model".format(match_date)
			# Find previous X matches prior to this date, create graph
			i_start = i - historical_match_number
			matches_to_use = df.ix[i_start:i]
			G = create_scorerank_graph(matches_to_use)
		previous_date = match_date

		# Make prediction using graph, if enough data
		home_team, away_team = match_row[ [ 'HomeTeam', 'AwayTeam' ] ]
		if not enough_data(matches_to_use, home_team, away_team):
			continue
		scorerank_difference = G.get_scorerank(home_team) - G.get_scorerank(away_team)

		# Make bookie prediction, use B365 only for now
		home_odds, draw_odds, away_odds = match_row[ ['B365H', 'B365D', 'B365A'] ]
		bookie_prediction = bookie_calculator(home_odds, draw_odds, away_odds)

		# Save result
		row_to_save = {'HomeTeam':home_team, 'AwayTeam':away_team, 'SR':scorerank_difference, 'Bookie':bookie_prediction}
		list_to_save.append(row_to_save)
		if debug:
			print "{} vs {}".format(home_team, away_team)
			print "Scorerank: {}  - Bookies: {}".format(scorerank_difference, bookie_prediction)
			print ""

	# Convert all of our calculations (rows = matches) to a dataframe
	final_df = pd.DataFrame(list_to_save)

	# Calculate success metric
	correlation = final_df.SR.corr(final_df.Bookie)
	print "Correlation between Bet365 and ScoreRank: {}".format(correlation**2)

	# Plot the correlation
	plt.scatter(final_df.SR, final_df.Bookie)
	plt.title('Correlation between ScoreRank model and Bet365 odds')
	plt.xlabel('Scorerank prediction (un-normalised)')
	plt.ylabel('Bet365 prediction')
	plt.show()