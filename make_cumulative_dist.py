#!/usr/bin/env python
""" Make cumulative distribution counting down from stackscore 100 to 1

Usage:

simeon@RottenApple ld4l-cul-usage>./make_cumulative_dist.py analysis/harvard_stackscore_distribution.dat  > cumulative_dist.dat
simeon@RottenApple ld4l-cul-usage>head cumulative_dist.dat 
# Cumulative distribution counting down from stackscore 100
# (derived from distribution in analysis/harvard_stackscore_distribution.dat)
#
#stackscore cumulative_fraction
100 0.00001013
99 0.00002032
98 0.00003045
97 0.00004065
96 0.00005077
95 0.00006126  
"""
import sys

def read_dist(file):
    """Read in a distribution

    # Distribution of StackScore values at Harvard, 2015-06-24
    #
    #record_count     stackscore        fraction_of_records
    13560805        1       0.98078307
    76281   2       0.00551701
    48500   3       0.00350775
    24538   4       0.00177471
    ...
    140     100     0.00001013
    """
    fh = open(file, 'r')
    dist = {}
    total = 0
    for line in fh.readlines():
        if (line.startswith('#')):
            continue
        (count,stackscore,frac) = line.split()
        count = int(count)
        stackscore = int(stackscore)
        if (stackscore<1 or stackscore>100):
            raise Exception("Stackscore out of range in: %s" % line)
        dist[stackscore] = count
        total += count
    return(dist,total)


dfile = sys.argv[1]
(dist,total) = read_dist(dfile)
cumulative = 0
print "# Cumulative distribution counting down from stackscore 100"
print "# (derived from distribution in %s)" % (dfile)
print "#\n#stackscore cumulative_fraction"
for ss in xrange(100,0,-1):
    cumulative += dist[ss]
    print "%d %.8f" % (ss,float(cumulative)/total)


