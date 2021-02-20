# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 14:23:39 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
from scipy.stats import multivariate_normal
from scipy.stats import norm
import scipy.stats as stats 

def playersimtotal(name, mindelta=0, adj=1):
    player = players21.loc[(players21['Player'] == name) & (players21['GameFP/36'] <=100)][['GameFP/36', 'MIN']]
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
    return distribution['total']



wincomparison = dict.fromkeys(fctodayf.Player)

for key, value in fiftry.items():
    wincomparison[key] = playersimtotal(key, value[0], value[1])


wincomparison
fiftry
wincomparison

wc = pd.DataFrame.from_dict(wincomparison)

rc = wc.rank(axis=1)

top10 = rc >= 216
top20 = rc >= 205
