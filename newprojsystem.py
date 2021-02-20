# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 22:30:05 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
import seaborn as sb
from scipy.stats import multivariate_normal
from scipy.stats import norm
import scipy.stats as stats


# A simple function that simulates a player's output by combining correlated 
# draws from their fantasy pts per minute per game & minutes 
# distributions. Players getting a MinDelta boost (Starting) receive a penalty to
# their rate (line 31) and are assigned prespecified minutes variance (because 
# bench players, conditional on starting, have much lower minutes variance.)
# The FPmean and MinMean variances are adjusted (line 29) because conditional
# variance is always lower than unconditional variance. I assume a fairly low
# r (0.3) for both when computing remaining variance.

def playersim(name, mindelta=0, adj=1):
    player = players21.loc[(players21['Player'] == name) & (players21['GameFP/36'] <=100)][['GameFP/36', 'MIN']]
    player['rollingfp'] = player['GameFP/36'].rolling(10, min_periods=3).mean()
    fpmean = player['GameFP/36'].mean() * adj
    minmean = player['MIN'].mean() + mindelta
    fp36sd = (player['GameFP/36'].max() - player['GameFP/36'].min())/4
    minsd = (player['MIN'].max() - player['MIN'].min())/4
    cov = np.array([[0,0], [0,0]])
    cov[0,0], cov[0,1], cov[1,0], cov[1,1] = (0.9 * fp36sd **2), -10, -10, (0.95 * minsd**2)
    
    
    if mindelta >= 8:
        fpmean = fpmean * 0.935
        cov[1,1] = 12
        cov[0,0] = 0.8 * cov[0,0]
        
    else:
        mindelta = mindelta
        cov[1,1] = cov[1,1]
        cov[0,0] = cov[0,0]
     

    distribution = pd.DataFrame(multivariate_normal.rvs(mean = [fpmean, minmean], cov=cov, size=1000))
    distribution['total'] = distribution[0]/36 * distribution[1]
    return (distribution['total'].mean(), distribution['total'].std())

playersim("P.J. Washington", 8, 1)

# Creating a dictionary from today's player pool with Players as Keys and Expected 
# Minutes Boost & Opponent Positional Adjustment as Values 

fiftry = dict([(i, a) for i, a in zip(fctoday.Player, fctoday.MinDelta)])
fiftry['P.J. Washington']
# This is a dictonary of today's players that will receive the output of the 
# PlayerSim function

sendhere = dict.fromkeys(fctoday.Player)

# Because the PlayerSim function returns errors for 0s I created a checklist 
# and for loop to remove players who appear in today's player pool but not in 
# this year's box # scores. They don't appear because names differ. I will
# create a dictionary to map names to fix this.
  

checklist = (players21['Player'].unique()).tolist()


for key in list(fiftry.keys()):
    if key not in checklist:
        del fiftry[key]

# A for loop to send today's player's to the function

for key, value in fiftry.items():
    sendhere[key] = playersim(key, value)
    

# A transposed DataFrame from the sendhere dict

projections = pd.DataFrame(sendhere).T.reset_index()
projections = projections.rename(columns={'index': 'Player', 0: 'matchupProj', 1:'ProjSTDV'})


condense = pd.merge(fctoday, projections, how='left', on='Player')
condense = condense.fillna(1)



def calculateboom(row):
    if row['Salary'] <= 4000:
        boom = 26
    
    else:
        boom = (row['Salary'] * 5 / 1000) * 1.25
        
    return (1-stats.norm.cdf(boom, row['matchupProj'], row['ProjSTDV'])).round(2)

def calculatebust(row):
    bust = (row['Salary'] * 5 / 1000)
    return stats.norm.cdf(bust, row['matchupProj'], row['ProjSTDV']).round(2)

boom = condense.apply(calculateboom, axis=1)
bust = condense.apply(calculatebust, axis=1)
condense['boom'] = boom
condense['bust'] = bust

condense = condense[['Player', 'matchupProj', 'ProjSTDV', 'boom', 'bust']]
fctoday = pd.merge(fctoday, condense, how='left', on='Player')
fctoday['TeammatchupProj'] = fctoday.groupby('Team_x').transform(sum)['matchupProj']
fctoday['scaledproj'] = ((fctoday['matchupProj'] / fctoday['TeammatchupProj']) * fctoday['predTeamFP']).astype(float).round(1)
fctoday['ProjSTDV'] = fctoday['ProjSTDV'].astype(float).round(1)

fctoday = fctoday.fillna(0.1)
fctoday['Player'] = fctoday['Player'].map(playerdictreversal).fillna(fctoday['Player'])

fctoday.to_csv(r'C:\Users\yaobv\Downloads\tcagain.csv')

fctoday[['Player', 'boom']].sort_values(by='boom', ascending=False).head(30)
