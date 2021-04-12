# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 15:42:51 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.regression.linear_model import OLSResults
from statsmodels.formula.api import ols
import datetime
from scipy import stats

boxscorestodate = r'C:\Users\yaobv\Downloads\04-10-2021-nba-season-player-feed - NBA-PLAYER-FEED.csv'
fantasycruncher_today = r'C:\Users\yaobv\Downloads\draftkings_NBA_2021-04-08_players (1).csv'

# There are ways of getting many of the features calculated below, but this began as an exercise in learning
# how to use Pandas. From raw box score data I extract all sorts of useful features and use several models to 
# create other ones. 

# loading the TeamFP model
results = OLSResults.load("teamfp.pickle")

# Loading the daily file
today = pd.to_datetime('today')
datethreshold = today - pd.Timedelta(days=10)


players21 = pd.read_csv(boxscorestodate)
fctoday = pd.read_csv(fantasycruncher_today)
fctoday = fctoday.loc[fctoday['Proj Mins'] > 0.5]

teampace = pd.read_csv(r'C:\Users\yaobv\Downloads\pace2.csv')
GMMlabels = pd.read_csv(r'C:\Learning to Code\code\DFS Projections\GMMclassifierlabels.csv')

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
players21['Date'] = pd.to_datetime(players21['Date'])


# A dictionary to translate player names

playerdict = {'Guillermo Hernangomez' : 'Willy Hernangomez', 'J.J. Redick' : 'JJ Redick',
              'James Ennis' : 'James Ennis III', 'Robert Williams' : 'Robert Williams III',
              'Marcus Morris' : 'Marcus Morris Sr.', 'DeAndre Bembry' : "DeAndre' Bembry",
              'PJ Washington' : 'P.J. Washington', 'Raulzinho Neto' : 'Raul Neto', 
              'Mohamed Bamba' : 'Mo Bamba', 'Bruce Brown Jr.' : 'Bruce Brown', 
              'Danuel House' : 'Danuel House Jr.', 'Juan Hernangomez' : 'Juancho Hernangomez',
              'Patrick Mills' : 'Patty Mills', 'Kevin Knox' : 'Kevin Knox II',
              'Otto Porter' : 'Otto Porter Jr.', 'C.J. McCollum' : 'CJ McCollum', 
              'KJ Martin Jr.' : 'Kenyon Martin Jr.'
              
              }

playerdictreversal = {value:key for (key, value) in playerdict.items()}


# Using the playerdict ensure the names on today's list of players match the 
# names used in the main DataFrame

fctoday['Player'] = fctoday['Player'].map(playerdict).fillna(fctoday['Player'])


# Computing player fantasy points from box score totals

# Assigning the bonus points for double-doubles and triple-doubles

players21['bonus'] = 0
dbldbl = (players21[['PTS', 'A', 'TOT', 'ST', 'BL', 'A']] >=10).astype(int)
dbldbl['tot'] = dbldbl.sum(axis=1)

players21['bonus'].loc[dbldbl['tot'] ==2] = 1.5
players21['bonus'].loc[dbldbl['tot'] ==3] = 4.5

# Creating new columns from raw box score data 
players21['GamesPlayed'] = players21.groupby('Player')['Player'].count()
players21['2PA'] = players21['FGA'] - players21['3PA']
players21['2PM'] = players21['FG'] - players21['3P']
players21['PlayerFP'] = players21['PTS'] + players21['A'] * 1.5 + players21['TOT'] * 1.25 + players21['ST'] * 2 + players21['BL'] * 2 + players21['3P'] * 0.5 + players21['TO'] * -0.5 + players21['bonus']
players21['GameFP/36']= (players21['PlayerFP'] / players21['MIN'] * 36).round(1)
players21['TeamFP'] = players21.groupby(['GameID','Team'])['PlayerFP'].transform(sum)
players21['Status'] = (players21.groupby('Player')['Starter'].transform('mean')).round(2)
players21['GP'] = players21.groupby('Player')['GameID'].transform('count')
players21['totfp'] = players21.groupby('Player')['PlayerFP'].transform(lambda x: x.cumsum().shift())
players21['totmin'] = players21.groupby('Player')['MIN'].transform(lambda x: x.cumsum().shift())
players21['fp/minsofar'] = (players21['totfp'] / players21['totmin']).round(2)
players21['expFP'] = (players21['fp/minsofar'] * players21['MIN']).round(1)
players21['delta'] = (players21['PlayerFP'] / players21['expFP'])
players21['MPG'] = players21.groupby('Player')['MIN'].transform('mean')
players21['weightedFP36'] = players21.groupby('Player')['GameFP/36'].transform(lambda x: x.ewm(span = 10, min_periods=3).mean().shift(1))
players21['possessionsUsed'] = players21['FGA'] + players21['TO'] + (players21['FT'] * 0.44)
players21['possessionsPerGame'] = players21.groupby('Player')['possessionsUsed'].transform('mean')
players21['possessionsPer48'] = (players21['possessionsUsed'] / players21['MIN']) * 48
playerposs = players21.groupby('Player')['possessionsPer48'].mean()


players21['teamperc'] = players21['PlayerFP'] / players21['TeamFP']
players21['percavg'] = players21.groupby('Player')['teamperc'].rolling(15, 3).mean().reset_index(0,drop=True)

players21['rollingmin'] = players21.groupby('Player')['MIN'].transform(lambda x: x.rolling(5).mean().round(1))
players21['expandingmin'] = players21.groupby('Player')['MIN'].transform(lambda x: x.expanding().mean().shift())
players21['rolling_min_diff'] = players21['rollingmin'] - players21['expandingmin']
players21['stdtodate'] = players21.groupby('Player')['PlayerFP'].transform(lambda x: x.expanding().std().shift(1))
players21['rollingUsage'] = players21.groupby('Player')['Usage'].transform(lambda x: x.rolling(8, 2).mean().shift(1))
players21['FP36stderr'] = players21.groupby('Player')['GameFP/36'].transform(lambda x: x.expanding().sem().shift(1))
players21['rollingMinSkew'] = players21.groupby('Player')['MIN'].transform(lambda x: x.expanding().skew().shift(1))
players21['rollingFP36Skew'] = players21.groupby('Player')['GameFP/36'].transform(lambda x: x.expanding().skew().shift(1))


fieldgoal_adj = players21.groupby('Player').agg({'3PA' : sum,
                               '3P' : sum,
                               'FGA' : sum,
                               'FG' : sum})


fieldgoal_adj['adj3PM'] = fieldgoal_adj['3P'] + 75.1
fieldgoal_adj['adj3PA'] = fieldgoal_adj['3PA'] + 211.5
fieldgoal_adj['adj3P%'] = fieldgoal_adj['adj3PM'] / fieldgoal_adj['adj3PA']
fieldgoal_adj['3P%'] = fieldgoal_adj['3P'] / fieldgoal_adj['3PA']
fieldgoal_adj['2PA'] = (fieldgoal_adj['FGA'] - fieldgoal_adj['3PA']) + 125
fieldgoal_adj['2PM'] = (fieldgoal_adj['FG'] - fieldgoal_adj['3P']) + 64.35
fieldgoal_adj['adj2P%'] = fieldgoal_adj['2PM'] / fieldgoal_adj['2PA']

players21 = pd.merge(players21, fieldgoal_adj, how='left', left_on = 'Player', right_index=True)
players21['Adj2P'] = players21['2PA_x'] * players21['adj2P%']
players21['Adj3P'] = players21['3PA_x'] * players21['adj3P%']

players21['Adj2Ppts'] = (players21['Adj2P'] * 2) - (players21['2PM_x'] * 2) 
players21['Adj3Ppts'] = ((players21['Adj3P'] * 3) - (players21['3P_x'] * 3)) * 1.1667

players21[['Player', 'Adj3Ppts']].sort_values(by = 'Adj3Ppts', ascending=False).head(30)

players21['adjPlayerFP'] = players21['PlayerFP'] + players21['Adj2Ppts'] + players21['Adj3Ppts']
players21['adjGameFP/36']= (players21['adjPlayerFP'] / players21['MIN'] * 36).round(1)


# Applying the GMM model labels
players21 = pd.merge(players21, GMMlabels, how = 'left', on='Player')
players21['GMMlabel'] = players21['GMMlabel'].fillna(2)

GMMdefense = players21[players21['MIN'] >= 20].groupby(['Opponent', 'GMMlabel'])['delta'].mean().reset_index()

# Exporting player data and today's slate to a github repository to update a 
# simple plotting app

players21.to_csv(r'C:\Users\yaobv\Downloads\boxscoresoutfeb25.csv')
players21 = players21.sort_values(by=['GameID', 'Team', 'MIN'])

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
fctoday['Pace'] = (fctoday['TeamPace'] * fctoday['OppPace'])/ 99.4


fctoday = pd.merge(fctoday, teamvegas, left_on = 'Opp', right_on = 'Team')
fctoday = fctoday.drop(columns = {'Team_y'})
fctoday['ClosingSpread'] = fctoday['TeamVegas'] - fctoday['VegasPts']

fctoday = pd.merge(fctoday, oppper, how='left', left_on = 'Opp', right_on = 'Opponent')
fctoday = pd.merge(fctoday, teamfpavg, how='left', left_on = 'Team_x', right_on = 'Team')
fctoday = fctoday.drop(columns = 'Team')

# Predicting team fantasy points using a simple model. 

fctoday['predTeamFP'] = results.predict(fctoday).round(1)

fctoday[['Team_x', 'Opp', 'Oppper48', 'TeamFPavg', 'predTeamFP']].drop_duplicates()

# Merging on the labels for defensive adjustment
fctoday = pd.merge(fctoday, GMMlabels, how='left', on='Player')
fctoday = pd.merge(fctoday, GMMdefense, how='left', left_on=['Opp', 'GMMlabel'], right_on=['Opponent', 'GMMlabel'])
fctoday = fctoday.rename(columns = {'delta' : 'newadj'})
fctoday.groupby('GMMlabel')['newadj'].min()

fctoday['newadj'] = fctoday['newadj'].fillna(1)
fctoday['newadj'] = ((fctoday['newadj'] - 1) * 0.75) + 1

filtered = players21.loc[players21['Date'] >= datethreshold]


fctoday['rollingMin'] = 1
fctoday = pd.merge(fctoday, playerposs, left_on = 'Player', right_index = True)
fctoday['expPossUse'] = (fctoday['possessionsPer48'] / 48) * fctoday['Proj Mins']
fctoday.groupby('Team_x')['expPossUse'].sum()


for p in list(fctoday['Player']):
    try: 
        lastmin = filtered.loc[filtered['Player'] == p]['rollingMin'].iloc[-1]
        fctoday.loc[fctoday['Player'] == p, 'rollingMin'] = lastmin
    except:
        pass
    
for p in list(fctoday['Player']):
    try:
        lastWeightedFP = filtered.loc[filtered['Player'] == p]['weightedFP36'].iloc[-1]
        fctoday.loc[fctoday['Player'] == p, 'rollingFP36'] = lastWeightedFP
    except:
        pass
    
for p in list(fctoday['Player']):
    try:
        rollingusage = filtered.loc[filtered['Player'] == p]['rollingUsage'].iloc[-1]
        fctoday.loc[fctoday['Player'] == p, 'rollingUsage'] = rollingusage
    except:
        pass
    


fctoday['rollDelta'] = fctoday['rollingMin'] - fctoday['Proj Mins']

print(fctoday[['Player', 'rollDelta', 'Proj Mins']])


lastskews = players21.groupby('Player')[['Player', 'MPG', 'rollingFP36Skew', 'rollingMinSkew']].tail(1)


skewmodel = ols('rollingMinSkew ~ MPG', data = lastskews)
results = skewmodel.fit()

lastskews['pred_skew'] = results.predict(lastskews)

fctoday['MPG'] = fctoday['Proj Mins']
fctoday['pred_skew'] = results.predict(fctoday)

playerskew = lastskews[['Player', 'rollingMinSkew']]
fctoday = pd.merge(fctoday, playerskew, how = 'left', on='Player')

fctoday['adjpred_skew'] = (0.75 * fctoday['pred_skew']) + (0.25 * fctoday['rollingMinSkew'])

fctoday[['Player', 'adjpred_skew']].sort_values(by = 'adjpred_skew', ascending=True).head(30)

