DFS Projections

A function that samples from a multivariate normal distribution with Fantasy Production Rate and Minutes Played as the marginals to generate each player's Fantasy Points distribution. The estimated parameters of each player's distribution (a random sample is used because it's faster and pretty good) are then entered into a "Boom" and "Bust" function that calculates the likelihood each player will: 1. Boom: exceed a value defined by their salary. 2. Bust: fail to exceed a value defined by their salary.

These projections are not especially good unless each team's player projections are scaled using their total predicted team points. It was built primarily to learn some skills!
