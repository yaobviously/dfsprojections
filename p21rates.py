# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 15:42:51 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb
from statsmodels.regression.linear_model import OLSResults
import datetime


# loading the model
results = OLSResults.load("teamfp.pickle")

# Loading the daily file
today = pd.to_datetime('today')
datethreshold = today - pd.Timedelta(days=5)


players21 = pd.read_csv(r'C:\Users\yaobv\Downloads\02-19-2021-nba-season-player-feed - NBA-PLAYER-FEED.csv')
fctoday = pd.read_csv(r'C:\Users\yaobv\Downloads\todaysslatefeb20.csv')
fctoday = fctoday.loc[fctoday['Proj Mins'] > 0.5]

teampace = pd.read_csv(r'C:\Users\yaobv\Downloads\teampace - nbateamdata.csv')

players21 = players21.rename(columns={'BIGDATABALL\nDATASET' : 'GameType',
                                      'GAME-ID' : 'GameID',
                                      'DATE' : 'Date',
                                      'PLAYER-ID' : 'PlayerID',
                                      'PLAYER \nFULL NAME' : 'Player',
                                      'POSITION' : 'Position',
                                      'OWN \nTEAM' : 'Team', 
                                      'OPPONENT \nTEAM' : 'Opponent',
                                      'VENUE\n(R/H)' : 'Venue',
                                      'STARTER\n(Y/N)' : 'Starter',
                                      'USAGE \nRATE (%)' : 'Usage',
                                      'DAYS\nREST' : 'Rest'})

# A dictionary for team names  

fcteamdict = {'ATL' : 'Atlanta', 'BOS':'Boston', 'BKN': 'Brooklyn', 'CHA' : 'Charlotte',
                   'WAS' : 'Washington', 'POR':'Portland', 'CHI':'Chicago',
                   'HOU' : 'Houston', 'DET':'Detroit', 'CLE':'Cleveland',
                   'DEN':'Denver', 'DAL':'Dallas', 'IND':'Indiana', 
                   'MEM':'Memphis', 'MIA':'Miami', 'MIL':'Milwaukee',
                   'NOP':'New Orleans', 'NYK':'New York', 'ORL':'Orlando',
                   'PHI':'Philadelphia', 'PHX': 'Phoenix', 'SAS':'San Antonio',
                   'TOR':'Toronto', 'UTA':'Utah', 'SAC':'Sacramento',
                   'MIN':'Minnesota', 'OKC':'Oklahoma City', 'GSW':'Golden State', 
                   'LAL': 'LA Lakers', 'LAC' : 'LA Clippers'}


fcteamdictreversal = {value:key for (key, value) in fcteamdict.items()}

starterdict = {'Y' : 1, 'N' : 0}

players21['Starter'] = players21['Starter'].map(starterdict)

# Using the playerdict ensure the names on today's list of players match the 
# names used in the main DataFrame

fctoday['Player'] = fctoday['Player'].map(playerdict).fillna(fctoday['Player'])


# A dictionary for player names

playerdict = {'Guillermo Hernangomez' : 'Willy Hernangomez', 'J.J. Redick' : 'JJ Redick',
              'James Ennis' : 'James Ennis III', 'Robert Williams' : 'Robert Williams III',
              'Marcus Morris' : 'Marcus Morris Sr.', 'DeAndre Bembry' : "DeAndre' Bembry",
              'PJ Washington' : 'P.J. Washington', 'Raulzinho Neto' : 'Raul Neto',
              }

playerdictreversal = {value:key for (key, value) in playerdict.items()}


players21['Date'] = pd.to_datetime(players21['Date'])

# Computing player fantasy points from box score totals

# Assigning the bonus points for double-doubles and triple-doubles

players21['bonus'] = 0
dbldbl = (players21[['PTS', 'A', 'TOT', 'ST', 'BL', 'A']] >=10).astype(int)
dbldbl['tot'] = dbldbl.sum(axis=1)

players21['bonus'].loc[dbldbl['tot'] ==2] = 1.5
players21['bonus'].loc[dbldbl['tot'] ==3] = 4.5


players21['PlayerFP'] = players21['PTS'] + players21['A'] * 1.5 + players21['TOT'] * 1.25 + players21['ST'] * 2 + players21['BL'] * 2 + players21['3P'] * 0.5 + players21['TO'] * -0.5 + players21['bonus']
players21['GameFP/36']= (players21['PlayerFP'] / players21['MIN'] * 36).round(1)
players21['TeamFP'] = players21.groupby(['GameID','Team'])['PlayerFP'].transform(sum)
players21['Status'] = (players21.groupby('Player')['Starter'].transform('mean')).round(2)
players21['GP'] = players21.groupby('Player')['GameID'].transform('count')
players21['TOTfp'] = players21.groupby('Player')['PlayerFP'].transform('sum')
players21['TOTmin'] = players21.groupby('Player')['MIN'].transform('sum')
players21['FPperMIN'] = (players21['TOTfp'] / players21['TOTmin']).round(2)
players21['expFP'] = (players21['FPperMIN'] * players21['MIN']).round(1)
players21['delta'] = (players21['PlayerFP'] - players21['expFP'])
players21['MPG'] = (players21['TOTmin'] / players21['GP']).round(1)

players21['teamperc'] = players21['PlayerFP'] / players21['TeamFP']
players21['percavg'] = players21.groupby('Player')['teamperc'].rolling(15, 3).mean().reset_index(0,drop=True)

players21['rollingMin'] = players21.groupby('Player')['MIN'].transform(lambda x: x.rolling(5, 3).mean().round(1))


# Calculating how much each team depresses FP output versus expectation for 
# every position. This isn't used in the projection model, but it's handy to
# know for 'on the fly' adjustments.

oppadj = players21.groupby(['Opponent', 'Position']).agg({'delta': sum,
                                                'MIN': sum}).reset_index()

oppadj['deltapermin'] = (oppadj['delta'] / oppadj['MIN']).round(2)
oppadj['Opponent'] = oppadj['Opponent'].map(fcteamdictreversal)
oppadj = oppadj.rename(columns = {'Opponent' : 'Opp'})
oppadj = oppadj[['Opp', 'Position', 'deltapermin']]
oppadj['Opp'] = oppadj['Opp'].map(fcteamdict)

# Calculating each team's FP per game. It is used as an input to the TeamFP 
# model. 

teamfp = players21[['GameID', 'Team', 'TeamFP']].drop_duplicates()
newteamfp = teamfp.groupby('Team').agg({'GameID': 'count',
                                        'TeamFP': sum}).reset_index()

newteamfp['TeamFPavg'] = newteamfp['TeamFP'] / newteamfp['GameID']
teamfpavg = newteamfp[['Team', 'TeamFPavg']] 


# Calculating FP allowed per 48 minutes. It is used as an input to the
# TeamFP model

totmin = (players21.groupby('Opponent')['MIN'].sum()).reset_index()
nodupes = players21[['GameID', 'Opponent', 'TeamFP']].drop_duplicates()
totfp = (nodupes.groupby('Opponent')['TeamFP'].sum()).reset_index()
oppper = pd.merge(totmin, totfp, how='left', on='Opponent')
oppper['Oppper48'] = ((oppper['TeamFP'] / oppper['MIN']) * 240).round(1)
oppper = oppper[['Opponent', 'Oppper48']]


# Computing each player's MinDelta that will be used in the Projection

mpg = players21[['Player', 'MPG']].drop_duplicates()

fctoday = fctoday[['Player', 'Team', 'Opp', 'VegasPts', 'Salary','Proj Mins', 'Own', 'FC Proj', 'My Proj']]

fctoday = pd.merge(fctoday, mpg, how='left', on='Player')
fctoday['MinDelta'] = fctoday['Proj Mins'] - fctoday['MPG']




# Creating a small DataFrame with each team's VegasPts in order to merge it 
# back onto fctoday DataFrame with Opp so I can calculate ClosingSpread for
# the TeamFP model.

teamvegas = fctoday[['Team', 'VegasPts']].drop_duplicates()
teamvegas['Team'] = teamvegas['Team'].map(fcteamdict)

# Modifying several columns to make them more amenable to analysis

fctoday['Own'] = fctoday['Own'].apply(lambda x: x.rstrip('%'))
fctoday['Own'] = fctoday['Own'].astype(float)
fctoday['Opp'] = fctoday['Opp'].apply(lambda x: x.lstrip('@'))
fctoday['Opp'] = fctoday['Opp'].apply(lambda x: x.lstrip('vs '))
fctoday['Team'] = fctoday['Team'].map(fcteamdict)
fctoday['Opp'] = fctoday['Opp'].map(fcteamdict)
fctoday = fctoday.rename(columns = {'VegasPts': 'TeamVegas'})

# Merging the TeamPace DataFrame in order to calculate each game's expected
# pace, which is used as an input variable in the TeamFP model.

fctoday = pd.merge(fctoday, teampace, how='left', on='Team')
fctoday = pd.merge(fctoday, teampace, how = 'left', left_on = 'Opp', right_on = 'Team')
fctoday = fctoday.rename(columns = {'Team_x' : 'Team', 'Pace_x' : 'TeamPace', 
                                    'Pace_y' : 'OppPace'})
fctoday = fctoday.drop(columns = 'Team_y')
fctoday['Pace'] = (fctoday['TeamPace'] * fctoday['OppPace'])/ 100.3


fctoday = pd.merge(fctoday, teamvegas, left_on = 'Opp', right_on = 'Team')
fctoday = fctoday.drop(columns = {'Team_y'})
fctoday['ClosingSpread'] = fctoday['TeamVegas'] - fctoday['VegasPts']

fctoday = pd.merge(fctoday, oppper, how='left', left_on = 'Opp', right_on = 'Opponent')
fctoday = pd.merge(fctoday, teamfpavg, how='left', left_on = 'Team_x', right_on = 'Team')
fctoday = fctoday.drop(columns = 'Team')

# Predicting team fantasy points using a simple model. 

fctoday['predTeamFP'] = results.predict(fctoday).round(1)

fctoday[['Team_x', 'Opp', 'Oppper48', 'TeamFPavg', 'predTeamFP']].drop_duplicates()


