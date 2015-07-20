#!/usr/bin/env python
""" Make reference distribution over the range 1 to 100

Usage:

> cumulative_dist.dat
simeon@RottenApple ld4l-cul-usage>git mv cumulative_dist.dat reference_dist.dat
simeon@RottenApple ld4l-cul-usage>./make_reference_dist.py analysis/harvard_stackscore_distribution.dat  > reference_dist.dat 
simeon@RottenApple ld4l-cul-usage>head reference_dist.dat 
# Reference distribution over StackScore 1..100
# (derived from distribution in analysis/harvard_stackscore_distribution.dat)
#
#stackscore fraction
10.98078307
20.00551701
30.00350775
40.00177471
50.00128962
60.00095700
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
print "# Reference distribution over StackScore 1..100"
print "# (derived from distribution in %s)" % (dfile)
print "#\n#stackscore fraction"
for ss in xrange(1,101):
    print "%d\t%.8f" % (ss,float(dist[ss])/total)


