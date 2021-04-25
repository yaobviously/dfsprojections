# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 14:32:01 2021

@author: yaobv
"""
import pandas as pd
import numpy as np
from scipy.stats import binom
from scipy.stats import beta

boxscores = r'C:\Users\yaobv\Downloads\04-24-2021-nba-season-player-feed - NBA-PLAYER-FEED.csv'
GMMlabels = pd.read_csv(r'C:\Learning to Code\code\DFS Projections\GMMclassifierlabels.csv')

def wrangle(url):
    df = pd.read_csv(url,
                     parse_dates = ['DATE'],
                     index_col = 'DATE')
    
    df = df.rename(columns={'BIGDATABALL\nDATASET' : 'game_type',
                            'GAME-ID' : 'gameid',                            
                            'PLAYER-ID' : 'playerid',
                            'PLAYER \nFULL NAME' : 'player',
                            'POSITION' : 'position',
                            'OWN \nTEAM' : 'team', 
                            'OPPONENT \nTEAM' : 'opponent',
                            'VENUE\n(R/H)' : 'venue',
                            'STARTER\n(Y/N)' : 'starter',
                            'USAGE \nRATE (%)' : 'usage',
                            'DAYS\nREST' : 'rest',
                            'TOT' : 'totreb'})
    
    df.columns = df.columns.str.lower()
    
    df['starter'] = [1 if start == 'Y' else 0 for start in df['starter']]
    df['venue'] = df.venue.map({'H' : 1, 'R' : 0})
    
    # computing bonus points for double-doubles and triple-doubles
    
    df['dbl_digits'] = (df[['pts', 'a', 'totreb', 'st', 'bl']] >= 10).astype(int).sum(axis=1)    
    df['bonus'] = 0
    df['bonus'].loc[df['dbl_digits'] == 2] = 1.5    
    df['bonus'].loc[df['dbl_digits'] == 3] = 4.5
    
    # computing player fantasy points
    df['playerfp'] = (df['pts'] + \
                      df['a'] * 1.5 + \
                      df['totreb'] * 1.25 + \
                      df['st'] * 2 + \
                      df['bl'] * 2 + \
                      df['3p'] * 0.5 + \
                      df['to'] * -0.5 + \
                      df['bonus']
                      )
    
    # computing team fantasy points
    df['teamfp'] = df.groupby(['gameid', 'team'])['playerfp'].transform(sum)
        
    # computing player game stats
    df['fp36'] = ((df['playerfp'] / df['min']) * 36).round(1)
    
    # computing running and rolling averages
    df['totmin'] = df.groupby('player')['min'].transform(lambda x: x.cumsum().shift())
    df['totfp'] = df.groupby('player')['playerfp'].transform(lambda x: x.cumsum().shift())
    df['fppm'] = (df['totfp'] / df['totmin']).round(2)
    df['ptsseason'] = df.groupby('player')['pts'].transform(lambda x: x.expanding().sum().shift())
    df['ftaseas'] = df.groupby('player')['fta'].transform(lambda x: x.expanding().sum().shift())
    df['fgaseas'] = df.groupby('player')['fga'].transform(lambda x: x.expanding().sum().shift())
    
    df['ts_season'] = (df['ptsseason'] / (2 * (df['fgaseas'] + (df['ftaseas'] * 0.44)))).round(3)
    
    df['mpg'] = df.groupby('player')['min'].transform(lambda x: x.expanding().mean().shift())
    df['rollingmpg'] = df.groupby('player')['min'].transform(lambda x:
                                                             x.rolling(10, min_periods = 2)
                                                             .mean()
                                                             .shift())
    
    df['avgusage'] = df.groupby('player')['usage'].transform(lambda x:
                                                             x.expanding()
                                                             .mean()
                                                             .shift())
    df['rollingusage'] = df.groupby('player')['usage'].transform(lambda x:
                                                                 x.rolling(5)
                                                                 .mean()
                                                                 .shift())    
    
    col_drop = ['dbl_digits', 'playerid', 'ptsseason', 'ftaseas','fgaseas']
    
    GMMlabels.columns = GMMlabels.columns.str.lower()
    df = pd.merge(df, GMMlabels, how = 'left', on = 'player')
    df['gmmlabel'] = df['gmmlabel'].fillna(2.0).astype(int)
    
    df.drop(col_drop, axis = 1, inplace = True)
    
    return df


df = wrangle(boxscores)

df.to_csv(r'C:\Learning to Code\code\DFS Projections\cleanedbox.csv', index = False)
