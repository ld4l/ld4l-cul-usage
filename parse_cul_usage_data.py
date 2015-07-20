#!/usr/bin/env python
#
# Code to parse CUL usage data, do some analysis, and generate
# a StackScore. See README.md.
#
import datetime
import gzip
import logging
import optparse
import os
from random import SystemRandom
import re
import sys
import math
import numpy

class SkipLine(Exception):
    """Exception to indicate skipping certain types of line without adding to bad count or flagging"""
    pass

class LineIterator(object):
    """
    Class to encapsulate iteration over lines with up to max_bad ignored before error
    """
    def __init__(self, file, data=''):
        self.linenum = 0
        self.max_bad = 10;
        self.fh = gzip.open(file,'rb')
        logging.info("Reading %sfrom %s" % (data,file))
        self.bib_ids = set()
        self.item_ids = set()

    @property
    def num_bib_ids(self):
        return len(self.bib_ids)

    @property
    def num_item_ids(self):
        return len(self.item_ids)

    def __iter__(self):
        return self

    def readline(self, keep_comment=False):
        """Wrap self.fh.readline() with line counter, and StopIteration at EOF"""
        self.line = self.fh.readline()
        if (self.line == ''):
            raise StopIteration
        self.linenum += 1
        self.line = self.line.strip()
        if (self.line.startswith('#') and not keep_comment):
            raise SkipLine
        return(self.line)

    def next(self):
        """Call self.next_time() up to self.max_bad times before aborting"""
        attempt = 0
        while (attempt < self.max_bad):
            try:
                return self.next_line()
            except StopIteration as si:
                raise si
            except SkipLine:
                # don't increment count of bad lines
                pass
            except Exception as e:
                logging.warning(str(e))
                attempt += 1
        raise Exception('[%s line %d] Too many bad lines!' % (self.fh.name,self.linenum))


class CULChargeAndBrowse(LineIterator):
    """
    Class providing iterator over change and browse data. Format of data 
    file is:

    # CHARGE AND BROWSE COUNTS
    #
    # other comment lines
    # ITEM_ID BIB_ID  HISTORICAL_CHARGES      HISTORICAL_BROWSES
    47      86706   3       0
    4672    44857   8       5
    9001938 246202  0       0
    """

    def __init__(self, file):
        super(CULChargeAndBrowse, self).__init__(file,'charge and browse counts ')
        first_line = self.readline(keep_comment=True)
        if (first_line != '# CHARGE AND BROWSE COUNTS'):
            raise Exception("Bad format for circ data in %s, bad first line '%s'" % (file,first_line))
 
    def next_line(self):
        """Read next line else raise exception describing problem

        The data includes lines where the change and browse counts are both
        zero and should be skipped.
        """
        self.readline()
        try:
            (item_id,bib_id,charges,browses) = self.line.split()
            bib_id = int(bib_id)
            charges = int(charges)
            self.bib_ids.add(bib_id)
            self.item_ids.add(int(item_id))
            if (charges>10000):
                raise Exception("excessive charge count: %d for bib_id=%d" % (charges,bib_id)) 
            browses = int(browses)
            if (browses>10000):
                raise Exception("excessive browse count: %d for bib_id=%d" % (browses,bib_id)) 
            if (charges==0 and browses==0):
                raise SkipLine()
            return (bib_id,charges,browses)
        except SkipLine as sl:
            raise sl
        except Exception as e:
            # provide file ane line num details in msg
            raise Exception('[%s line %d] Ignoring "%s"] %s' % (self.fh.name,self.linenum,self.line,str(e)))


class CULCircTrans(LineIterator):
    """
    Class providing iterator over circulation transaction data. Format of data 
    file is as follows and included lines with no item_id or bib_id which should
    be ignored:
    
    # CIRCULATION TRANSACTIONS
    #
    # other comments...
    #           TRANS_ID   ITEM_ID         BIB_ID       DATE
                143        3087926         1538011      15-JAN-00
                144        5123416         3111111      22-FEB-00
                145        1133333          511222      26-SEP-00
                146                                     15-SEP-96
                147        489988          2926664      20-DEC-99
                148                                     09-JUL-00
    """
                
    def __init__(self, file):
        super(CULCircTrans,self).__init__(file,'circulation transactions ')
        first_line = self.readline(keep_comment=True)
        if (first_line != '# CIRCULATION TRANSACTIONS'):
            raise Exception("Bad format for circ data in %s, bad first line '%s'" % (file,first_line))

    def next_line(self):
        """Read next line else raise exception describing problem"""
        self.readline()
        try:
            # first look for lines without item_id,bib_id, ie num-spaces-date, and skip
            if (re.match(r'\d+\s+\d\d\-',self.line)):
                raise SkipLine()
            # else try to parse for real
            (trans_id,item_id,bib_id,date) = self.line.split()
            bib_id = int(bib_id)
            self.bib_ids.add(bib_id)
            self.item_ids.add(int(item_id))
            date = datetime.datetime.strptime(date, "%d-%b-%y").date()
            return (bib_id,date)
        except SkipLine as sl:
            raise sl
        except Exception as e:
            # provide file ane line num details in msg
            raise Exception('[%s line %d] Ignoring "%s"] %s' % (self.fh.name,self.linenum,self.line,str(e)))

        """Read next line else raise exception describing problem"""
        raise StopIteration

def make_randomized_subset(opt):
    """Make a subset dataset for fraction of the bib-ids"""
    bib_ids = {}

    fraction = opt.subset_fraction
    r = SystemRandom() # a non-reporoducible random generator

    logging.warning("Writing subset charge and browse to %s..." % opt.subset_charge_and_browse )
    cab_fh = gzip.open( opt.subset_charge_and_browse, 'w')
    cab_fh.write("# CHARGE AND BROWSE COUNTS\n")
    cab_fh.write("# (randomized subset data, item_id=0)\n")
    fake_bib_ids = set()
    for (bib_id,charges,browses) in CULChargeAndBrowse(opt.charge_and_browse):
        if (r.random()<=fraction):
            # generate fake bib_id that we haven't used before, record and dump data
            fake_bib_id = 1234567
            while (fake_bib_id in fake_bib_ids):
                fake_bib_id = r.randint(1,10000000)
            bib_ids[bib_id] = fake_bib_id
            fake_bib_ids.add(fake_bib_id)
            # write, just use 0 for item_id as we don't use that at all
            cab_fh.write("%d\t%d\t%d\t%d\n" % (0,fake_bib_id,charges,browses) )
    cab_fh.close()

    logging.warning("Writing subset circ trans to %s..." % opt.subset_circ_trans )
    ct_fh = gzip.open( opt.subset_circ_trans, 'w')
    ct_fh.write("# CIRCULATION TRANSACTIONS\n")
    ct_fh.write("# (randomized subset data, trans_id=0, item_id=0)\n")
    for (bib_id,date) in CULCircTrans(opt.circ_trans):
        # select subset based on whether the bib_id was picked before
        if (bib_id in bib_ids):
            fake_bib_id = bib_ids[bib_id]
            # an just for belt-and-brances, randomise the date by a year or so
            fake_dt = datetime.datetime.combine(date,datetime.time.min) + datetime.timedelta(days=r.randint(-400,400))
            fake_date = fake_dt.date().strftime('%d-%b-%y').upper()
            # write, use 0 for trans_id and item_id as we don't use these at all
            ct_fh.write("   %d\t%d\t%d\t%s\n" % (0,0,fake_bib_id,fake_date) )
    ct_fh.close()

    logging.info("Done subset")


def write_float_dist(data,file):
    """Write summary of distribution of floats to file"""
    hist, bin_edges = numpy.histogram(data.values(), bins=100)
    total_bib_ids = len(data)
    logging.info("Writing summary distribution to %s..." % file)
    fh = open(file, 'w')
    fh.write("# Binned distribution %s\n#\n" % file)
    fh.write("# total bib_ids = %d\n#\n" % total_bib_ids)
    fh.write("#start\tend\tcount\tfraction\n")
    for j, val in enumerate(hist):
        fh.write("%.1f\t%.1f\t%d\t%.7f\n" % (bin_edges[j],bin_edges[j+1],val,float(val)/total_bib_ids))
    fh.close()


def write_dist(data,file,all_bib_ids=0,extra_score_one=0):
    """Write summary of distribution of data to file
    
    data is a dict[bib_id] with some counts a values, the integer value of the count
    is taken
    """
    total_bib_ids = 0
    total_counts = 0
    num_bib_ids = {} #inverted: number of bib_ids with given count
    example_bib_id = {}
    for bib_id in data:
        count = int(data[bib_id])
        if (count>0):
            total_bib_ids += 1
            total_counts += count
            if (count in num_bib_ids):
                num_bib_ids[count] = num_bib_ids[count] + 1
            else:
                num_bib_ids[count] = 1
                if (opt.examples):
                    example_bib_id[count] = bib_id
                else:
                    # default not to include specific example bib_id for individual data sources
                    example_bib_id[count] = '-'
    if (extra_score_one>0):
        num_bib_ids[1] = num_bib_ids.get(1,0) + extra_score_one
        if (1 not in example_bib_id):
            example_bib_id[1] = '-'
    if (all_bib_ids==0):
        all_bib_ids = total_bib_ids + extra_score_one
    logging.info("Writing distribution to %s..." % file)
    fh = open(file, 'w')
    fh.write("# Distribution %s\n" % file)
    fh.write("#\n# total bib_ids with non-zero counts = %d\n" % total_bib_ids)
    if (extra_score_one>0):
        fh.write("# extra bib_ids with score one = %d\n" % extra_score_one)
    fh.write("# total bib_ids with usage data + extras = %d\n" % all_bib_ids)
    fh.write("# sum of all counts = %d\n" % total_counts)
    fh.write("#\n# col1 = int(count)\n# col2 = num_bib_ids\n")
    fh.write("# col3 = fraction of total bib_ids with non-zero counts for this metric\n")
    fh.write("# col4 = fraction of all bib_ids with any usage data\n")
    fh.write("# col5 = example bib_id (prepend: https://newcatalog.library.cornell.edu/catalog/)\n")
    for count in sorted(num_bib_ids.keys()):
        fh.write("%d\t%d\t%.7f\t%.7f\t%s\n" % 
                 (count,num_bib_ids[count],
                  float(num_bib_ids[count])/total_bib_ids,
                  float(num_bib_ids[count])/all_bib_ids,
                  example_bib_id[count]))
    fh.close()


def write_stackscores(scores,file):
    """Write individual StackScores to gzipped file

    Note that this data will include only bib_ids mentioned in the usage data. It 
    will not include extra bib_ids that are assigned StackScore 1.
    """
    logging.info("Writing StackScores to %s..." % file)
    fh = gzip.open(file, 'w')
    fh.write("# StackScores by bib_id, %s\n#\n" % file)
    fh.write("# total bib_ids = %d\n#\n" % len(scores))
    fh.write("#bib_id\tStackScore\n")
    for bib_id in sorted(scores.keys()):
        fh.write("%d\t%d\n" % (bib_id,scores[bib_id]))
    fh.close()


def analyze_distributions(opt):
    """Analyze distributions of source data""" 

    all_bib_ids = {}
    charge = {}
    browse = {}
    bits = {}
    for (bib_id,charges,browses) in CULChargeAndBrowse(opt.charge_and_browse):
        charge[bib_id] = charge.get(bib_id,0) + charges
        if (charges>0):
            bits[bib_id] = bits.get(bib_id,0) | 1
            all_bib_ids[bib_id] = 1
        browse[bib_id] = browse.get(bib_id,0) + browses
        if (browses>0):
            bits[bib_id] = bits.get(bib_id,0) | 2
            all_bib_ids[bib_id] = 1
    circ = {}
    for (bib_id,date) in CULCircTrans(opt.circ_trans):
        circ[bib_id] = circ.get(bib_id,0) + 1
        bits[bib_id] = bits.get(bib_id,0) | 4
        all_bib_ids[bib_id] = 1

    num_bib_ids = len(all_bib_ids)
    write_dist(charge,'charge_dist.dat',num_bib_ids)
    write_dist(browse,'browse_dist.dat',num_bib_ids)
    write_dist(circ,'circ_dist.dat',num_bib_ids)

    # Look at overlaps between groups from bitwise
    exc_totals = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
    inc_totals = {1:0,2:0,4:0}
    for bib_id in bits:
        exc_totals[bits[bib_id]] += 1
        for b in (1,2,4):
            if (bits[bib_id] & b):
                inc_totals[b] += 1
    file = 'usage_venn.dat'
    logging.info("Writing %s..." % file)
    fh = open(file,'w')
    fh.write("# Overlaps in different types of usage data:\n");
    just = 'just '
    for n in range(1,8):
        desc = []
        if (n & 1):
            desc.append('browse')
        if (n & 2):
            desc.append('charge')
        if (n & 4):
            desc.append('circ')
        if (n==7):
            just = ''
        out_of = ''
        if (n in (1,2,4)):
            out_of = ' (out of %d items with this data)' % inc_totals[n]
        fh.write("%7d items have %s%s data%s\n" % (exc_totals[n],just,'+'.join(desc),out_of))
    fh.close()


def compute_raw_scores(opt):
    """Read in usage data and compute StackScores

    Score is calculated according to:

    score = charges * charge_weight +
            browses * browse_weight +
            sum_over_all_circ_trans( circ_weight + 0.5 ^ (circ_trans_age / circ_halflife) )

    because recent circulation transactions are also reflected in the charge counts, this 
    means that a circulation that happens today will score (charge_weight+circ_weight) whereas
    on the happened circ_halflife ago will score (charge_weight+0.5*circ_weight). An old 
    circulation event that is recored only in the charge counts will score just charge_weight.
    """
    scores = {}
    charge_weight = 2
    browse_weight = 1
    circ_weight = 2
    circ_halflife =  5.0 * 365.0 # number of days back that circ trans has half circ_weight

    cab = CULChargeAndBrowse(opt.charge_and_browse)
    for (bib_id,charges,browses) in cab:
        #print "%d %d %d" % (bib_id,charges,browses)
        scores[bib_id] = scores.get(bib_id,0) + charges*charge_weight + browses*browse_weight
    logging.info("Found %d bib_ids in charge and browse data" % (cab.num_bib_ids))
    
    today = datetime.datetime.now().date()
    ct = CULCircTrans(opt.circ_trans)
    for (bib_id,date) in ct:
        age = (today - date).days # age in years since circ transaction
        score = circ_weight * math.pow(0.5, age/circ_halflife )
        #print "%d %s %.3f %.3f" % (bib_id,str(date),age,score)
        scores[bib_id] = scores.get(bib_id,0) + score
    logging.info("Found %d bib_ids in circulation and transaction data" % (ct.num_bib_ids))
    write_float_dist(scores, opt.raw_scores_dist)
    return(scores)


def read_reference_dist(file):
    """Read reference distribution from file

    File format has # for comment linesm then data:

    #stackscore fraction
    100 0.00001013
    99 0.00001013
    98 0.00003045
    ...
    """
    logging.info("Reading reference distribution from %s..." % (file))
    fh = open(file,'r')
    dist = {}
    total = 0.0
    for line in fh:
        if (re.match('^#',line)):
            continue
        (stackscore, fraction)= line.split()
        fraction = float(fraction)
        dist[int(stackscore)] = fraction
        total += fraction
        #print "%d %f" % (stackscore,fraction)
    if (abs(1.0-total)>0.000001):
        logging.warning("Expected distribution from %s to sum to 1.0, got %f" % (file,total))
    return dist


def compute_stackscore(scores, dist, opt):
    """Compute StackScores on a scale of 1-100 to match reference distribution

    The score of 1 will be reserved for all items that have no usage data as is done for 
    the Harvard StackScore. The reference distribution is suppied in dist and is assumed to
    sum be over the range 1 to 100 and sum to 1.0.

    We do not expect the the scores data to include all bib_ids, the total number of items
    is taken from the input parameter opt.total_bib_ids if specified (!=0) and thus there 
    will be at least (opt.total_bib_ids - len(scores)) items that will get score 1.
    """
    if (opt.total_bib_ids):
        total_items = opt.total_bib_ids
        if (len(scores)>total_items):
            raise Exception("Sanity check failed: more scores (%d) than total_bib_ids (%d)!" % (len(scores),total_bib_ids))
        extra_items_with_score_one = (total_items-len(scores))
    else:
        total_items = len(scores)
        extra_items_with_score_one = 0
    # Get counts of items for each raw score (which may be a float)
    counts = {}
    for bib_id in scores:
        score = scores[bib_id]
        counts[score] = counts.get(score,0) + 1
    # Determine StackScore for each score by matching to the reference distribution in
    # dist. We do this starting from StackScore 100 and adding extra raw scores in
    # to meet the cumulative total most closely.
    num_scores = len(counts)
    logging.info("Have %d distinct raw scores from %d items" % (num_scores,len(scores)))
    count = 0
    stackscore_by_score = {}
    stackscore_counts = {}
    n = 0
    ss = 100
    ss_frac = dist[ss] # cumulative fraction we want to get to for this StackScore
    for score in reversed(sorted(counts.keys())):
        # do we add to this StackScore or the next lower?
        n = counts[score]
        ss_count = int(ss_frac*total_items) # integer cumulative count
        if ((count+n > ss_count) and ((count+n)-ss_count) > (ss_count-count) and ss>1):
            # should add to next lower StackScore
            ss -= 1
            ss_frac += dist[ss]
        count += n
        stackscore_by_score[score] = ss
        stackscore_counts[ss] = stackscore_counts.get(ss,0) + n
    # add in extra counts for score 1
    if (ss!=1 and ss!=2):
        logging.warning("Distribution seems odd: expected to have ss==1 or ss==2 after normalizing, got ss=%d" % (ss))
    stackscore_counts[1] = stackscore_counts.get(1,0) + extra_items_with_score_one
    # write table comparing with reference distribution
    fh = open(opt.stackscore_comp,'w')
    fh.write("# Comparison of StackScore distribution with reference distribution\n#\n")
    fh.write("#score\trecords\tfraction\treference_fraction\n")
    for ss in range(1,101):
        fh.write("%d\t%d\t%.7f\t%.7f\n" % (ss,stackscore_counts.get(ss,0),float(stackscore_counts.get(ss,0))/total_items,dist.get(ss,0)))
    fh.close()
    # now we have lookup table of score->StackScore, make set of StackScores, dump
    # them and write out the distribution
    stackscore={}
    for bib_id in scores:
        stackscore[bib_id]=stackscore_by_score[scores[bib_id]]
    if (opt.stackscores):
        write_stackscores(stackscore, opt.stackscores)
    write_dist(stackscore, opt.stackscore_dist, extra_score_one=extra_items_with_score_one)

##################################################################

# Options and arguments
p = optparse.OptionParser(description='Parser for CUL usage data',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]')
p.add_option('--charge-and-browse', action='store', default='testdata/subset-charge-and-browse-counts.tsv.gz',
             help="Charge and browse num_bib_ids, gzipped input file (default %default)")
p.add_option('--circ-trans', action='store', default='testdata/subset-circ-trans.tsv.gz',
             help="Circulation transactions, gzipped input file (default %default)")
p.add_option('--total-bib-ids', action='store', type='int', default=0,
             help="Total number of bib_ids in the catalog (omit to use only input data)")
p.add_option('--reference-dist', action='store', default='reference_dist.dat',
             help="Reference distribution over the range 1..100 to match to (default %default)")
p.add_option('--raw-scores-dist', action='store', default='raw_scores_dist.dat',
             help="Distribution of raw scores (default %default)")
p.add_option('--stackscores', action='store',
             help="StackScores output file (not written by default, will be gzipped)")
p.add_option('--stackscore_dist', action='store', default='stackscore_dist.dat',
             help="StackScore distribution output file (default %default)")
p.add_option('--stackscore_comp', action='store', default='stackscore_dist_comp.dat',
             help="StackScore distribution comparison with reference (default %default)")
p.add_option('--logfile', action='store',
             help="Send log output to specified file")
p.add_option('--examples', action='store_true',
             help="Include example bib_id in distribution outputs")
p.add_option('--verbose', '-v', action='store_true',
             help="verbose, show additional informational messages")

p.add_option('--analyze', action='store_true',
             help="Do analysis of input distributions")

p.add_option('--make-randomized-subset', action='store_true',
             help="Make a smaller subset of the input data and write out again")
p.add_option('--subset-fraction', action='store', type='float', default=0.01,
             help="Fraction of data to include in subset (0.0<=fraction<=1.0, default %default)")
p.add_option('--subset-charge-and-browse', action='store', default='subset-charge-and-browse-counts.tsv.gz',
             help="Name of output file for subset charge and browse counts (default %default)")
p.add_option('--subset-circ-trans', action='store', default='subset-circ-trans.tsv.gz',
             help="Name of output file for subset circulation transactions (default %default)")

(opt, args) = p.parse_args()

level = logging.INFO if opt.verbose else logging.WARN
if (opt.logfile):
    logging.basicConfig(filename=opt.logfile, level=level)
else:
    logging.basicConfig(level=level)

logging.info("STARTED at %s" % (datetime.datetime.now()))
if (opt.make_randomized_subset):
    make_randomized_subset(opt)
elif (opt.analyze):
    analyze_distributions(opt)
else:
    scores = compute_raw_scores(opt)
    dist = read_reference_dist(opt.reference_dist)
    compute_stackscore(scores, dist, opt)
logging.info("FINISHED at %s" % (datetime.datetime.now()))


