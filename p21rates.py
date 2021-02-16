# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 15:42:51 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb
import datetime

# Loading the daily file


players21 = pd.read_csv(r'C:\Users\yaobv\Downloads\02-14-2021-nba-season-player-feed - NBA-PLAYER-FEED.csv')
fctoday = pd.read_csv(r'C:\Users\yaobv\Downloads\draftkings_NBA_2021-02-15_players (2).csv')

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

# Dictionary and its reversal 

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

# computing player fantasy points from box score totals

players21['bonus'] = 0
dbldbl = (players21[['PTS', 'A', 'TOT']] >=10).astype(int)
dbldbl['tot'] = dbldbl.sum(axis=1)


players21['bonus'].loc[dbldbl['tot'] >=2] = dbldbl['tot']
players21['bonus']
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

players21['rollingMin'] = players21.groupby('Player')['MIN'].transform(lambda x: x.rolling(5, 2).mean().round(1))


oppadj = players21.groupby(['Opponent', 'Position']).agg({'delta': sum,
                                                'MIN': sum}).reset_index()

oppadj['deltapermin'] = (oppadj['delta'] / oppadj['MIN']).round(2)
oppadj['Opponent'] = oppadj['Opponent'].map(fcteamdictr)
oppadj = oppadj.rename(columns = {'Opponent' : 'Opp'})
oppadj = oppadj[['Opp', 'Position', 'deltapermin']]


players21.round(1).to_csv(r'C:\Learning to Code\code\DailyFantasyCSV\boxscoreappdata.csv', index=False)


# converting each player's total stats to per 36 minute rates. 
# when computing the standard deviation i am assuming a poisson, which may need
# to be reconsidered - negative binomial?

playsmall = players21[['Player', 'MPG', 'Position', 'FPperMIN']].drop_duplicates()


fctoday = fctoday[['Player', 'Team', 'Opp', 'Salary','Proj Mins', 'Own', 'My Proj']]


fctoday['Own'] = fctoday['Own'].apply(lambda x: x.rstrip('%'))
fctoday['Own'] = fctoday['Own'].astype(float)
fctoday['Opp'] = fctoday['Opp'].apply(lambda x: x.lstrip('@'))
fctoday['Opp'] = fctoday['Opp'].apply(lambda x: x.lstrip('vs '))


fctodayc = pd.merge(fctodayb, playsmall, how= 'left', on= 'Player')
fctodayd = pd.merge(fctodayc, oppadj, how='left', on = ['Opp', 'Position'])

fctodayd['newadj'] = (0.8 * 1) + (0.2 * ((fctodayd['FPperMIN'] + fctodayd['deltapermin']) / fctodayd['FPperMIN'])).round(2)
fctodayd['MinDelta'] = fctodayd['Proj Mins'] - fctodayd['MPG'] 


fctodayf.loc[fctodayf['Player'] == 'Joel Embiid']

fctodayf = fctodayd.fillna(0)

fctodayf.to_csv(r'C:\Users\yaobv\Downloads\fctodayoutput.csv')

