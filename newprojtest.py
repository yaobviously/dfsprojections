# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 19:50:52 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats
from scipy.stats import multivariate_normal
import matplotlib.pyplot as plt
import random

def correlated_non_normal(player, mindelta = 0, Salary = 5000, adjustment = 1, altskew = -0.1):
    df_ = players21[players21['Player'] == player][['GameFP/36', 'MIN']]      
    df_ = df_.fillna(1)
    corr_ = df_.corr()
    corr = (corr_.iloc[0,1] * 0.5) + (0.15 * 0.5)     
       
    
    padding = pd.Series([30.6, 30.6, 30.6])
    gamefp = df_['GameFP/36']
    gamefp = gamefp.append(padding)

    
    cov = [[1.0, corr], [corr, 1.0]]
    
    mv_sample = stats.multivariate_normal.rvs((0,0), cov, 1000)
    uniformed_mv_sample = stats.norm.cdf(mv_sample)
    
    uniformed_fp = uniformed_mv_sample[:,0]
    uniformed_min = uniformed_mv_sample[:,1]
    
    skew, loc, scale = stats.skewnorm.fit(gamefp)
    minskew, minloc, minscale = stats.skewnorm.fit(df_['MIN'])
    
           
    if mindelta >= 5:
        comp_adj = 0.90
    else:
        comp_adj = 1
    
    fp36_sample = stats.skewnorm.rvs(skew, loc, scale, 500)
    
    min_sample = stats.skewnorm.rvs(altskew, minloc, minscale, 500)
    
    
    sample_correlated = np.quantile(fp36_sample, q = uniformed_fp)
    sample_correlated = sample_correlated * adjustment * comp_adj
    minutes_correlated = np.quantile(min_sample, q = uniformed_min)
    minutes_correlated = minutes_correlated + mindelta
    
    fp_values = (fp36_sample/36) * min_sample
    correlated_values = (sample_correlated/36) * minutes_correlated
    
    
    salaryexp = (Salary * 5 / 1000)
    boom = correlated_values[correlated_values >= salaryexp + 9]
    bust = correlated_values[correlated_values < salaryexp]    
    
       
    
    return correlated_values.mean(), len(bust)/len(correlated_values), len(boom)/len(correlated_values), np.quantile(correlated_values, q = 0.9)
    
correlated_non_normal('Derrick White', mindelta = 1, Salary = 8800, adjustment = 1, altskew = 1)



todaysplayers = {player: (mindelta, salary, newadj, minskew) for player, mindelta, salary, newadj, minskew in zip(fctoday.Player, fctoday.MinDelta, fctoday.Salary, fctoday.newadj, fctoday.adjpred_skew)}


simoutput = dict.fromkeys(todaysplayers)



# FC Proj Minutes Output

for player, details in todaysplayers.items():
    try: 
        simoutput[player] = correlated_non_normal(player, details[0], details[1], details[2], details[3])
    except:
        pass
    

ordinaryproj = pd.DataFrame.from_dict(simoutput, orient = 'index', columns = ['my proj', 'bust', 'boom', '90_perc' ])

ordinaryproj = round(ordinaryproj, 2)

ordinaryproj[['bust', 'boom', '90_perc']].sort_values(by = 'boom', ascending=False).head(30)

ordinaryproj.to_csv(r'C:\Users\yaobv\Downloads\projtoday.csv')


todaysplayers['Nikola Vucevic'] = (-0.55, 9100, 0.9, -0.57)
todaysplayers['Zach LaVine'] = (-0.12, 8600, 0.93, -0.62)
todaysplayers['Lauri Markkanen'] = (-5.8, 4300, -0.86, -0.18)
todaysplayers['Cory Joseph'] = (0.8, 4400, 1.2, 0.05)
