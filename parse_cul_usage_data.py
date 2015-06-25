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
        """Read next line else raise exception describing problem"""
        self.readline()
        try:
            (item_id,bib_id,charges,browses) = self.line.split()
            bib_id = int(bib_id)
            charges = int(charges)
            if (charges>10000):
                raise Exception("excessive charge count: %d for bib_id=%d" % (charges,bib_id)) 
            browses = int(browses)
            if (browses>10000):
                raise Exception("excessive browse count: %d for bib_id=%d" % (browses,bib_id)) 
            return (bib_id,charges,browses)
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


def write_dist(data,file,all_bib_ids=0):
    """Write summary of distribution of data to file
    
    data is a dict[bib_id] with some counts a values
    """
    total_bib_ids = 0
    total_counts = 0
    num_bib_ids = {} #inverted: number of bib_ids with given count
    example_bib_id = {}
    for bib_id in data:
        count = data[bib_id]
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
    if (all_bib_ids==0):
        all_bib_ids=total_bib_ids
    logging.info("Writing %s..." % file)
    fh = open(file, 'w')
    fh.write("# Distribution %s\n" % file)
    fh.write("#\n# total bib_ids with non-zero counts = %d\n" % total_bib_ids)
    fh.write("# total bib_ids with any usage data = %d\n" % all_bib_ids)
    fh.write("# total of all counts = %d\n" % total_counts)
    fh.write("#\n# col1 = count\n# col2 = num_bib_ids\n")
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

def compute_stackscore(opt):
    """Read in usage data and compute StackScores"""

    scores = {}
    charge_weight = 3
    browse_weight = 1
    circ_weight = 5

    for (bib_id,charges,browses) in CULChargeAndBrowse(opt.charge_and_browse):
        #print "%d %d %d" % (bib_id,charges,browses)
        scores[bib_id] = scores.get(bib_id,0) + charges*charge_weight + browses*browse_weight
    
    for (bib_id,date) in CULCircTrans(opt.circ_trans):
        #print "%d %s" % (bib_id,str(date))
        scores[bib_id] = scores.get(bib_id,0) + circ_weight

    write_dist(scores, 'raw_scores_dist.dat')

    # Now normalize on a scale of 2-100 inclusive. The score of 1 will be reserved 
    # for all items that have no usage data as is done for the Harvard StackScore.
    counts = {}
    for bib_id in scores:
        score = scores[bib_id]
        counts[score] = counts.get(score,0) + 1
    # Determine StackScore for each score using the same algoritm as Harvard
    # where will collect together approx the same number of distinct raw scores
    # in each bin
    num_scores = len(counts)
    scores_per_stackscore = num_scores/98.99
    stackscore_by_score = {}
    stackscore_counts = {}
    n = 0
    for score in reversed(sorted(counts.keys())):
        n += 1
        ss = 100 - int(n/scores_per_stackscore)
        stackscore_by_score[score] = ss
        stackscore_counts[ss] = stackscore_counts.get(ss,0) + counts[score]
    # write table to compare with Harvard distribution
    fh = open('cornell_stackscore_distribution.dat','w')
    total_items = 8000000
    num_with_score = len(scores)
    stackscore_counts[1] = total_items - num_with_score
    fh.write("record_count    stackscore      fraction_of_records\n")
    for ss in sorted(stackscore_counts.keys()):
        fh.write("%d\t%d\t%.7f\n" % (stackscore_counts[ss],ss,float(stackscore_counts[ss])/total_items))
    fh.close()
    # Now we have lookup table, make set of stackscores...
    stackscore={}
    for bib_id in scores:
        stackscore[bib_id]=stackscore_by_score[scores[bib_id]]
    write_dist(stackscore, 'stackscore_dist.dat')

##################################################################

# Options and arguments
p = optparse.OptionParser(description='Parser for CUL usage data',
                          usage='usage: %prog [[opts]] [file1] .. [fileN]')
p.add_option('--charge-and-browse', action='store', default='testdata/subset-charge-and-browse-counts.tsv.gz',
             help="Charge and browse num_bib_ids, gzipped input file (default %default)")
p.add_option('--circ-trans', action='store', default='testdata/subset-circ-trans.tsv.gz',
             help="Circulation transactions, gzipped input file (default %default)")
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
    compute_stackscore(opt)
logging.info("FINISHED at %s" % (datetime.datetime.now()))


