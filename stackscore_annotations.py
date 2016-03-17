#!/usr/bin/env python
"""
Add StackScore usage data as annotations.

Timing:
  10s to read 2.3M stackscores into dict
  150min to parse 2M records from Cornell LD4L RDF and write annotations
  => expect 600min = 10h to write annotations for 8M records
"""

import glob
import gzip
import logging
import optparse
import os.path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, RDF
import re
import time

def split_multiext(filename, max=2):
    """Wrapper around os.path.splitext to remove potentially multiple extensions."""
    all_ext = ''
    n = 0
    while (n < max):
        n += 1
        (filename,ext) = os.path.splitext(filename)
        if (ext):
            all_ext = ext + all_ext
        else:
            break
    return(filename,all_ext)

def read_stackscores(filename):
    """Read StackScores from filename.

    Each line is simply bibid and stackscore
    """
    logging.info("Reading StackScores from %s..." % (filename))
    fh = gzip.open(filename,'r')
    scores = {}
    n = 0
    for line in fh:
        n+=1
        if (re.match(r'''\s*#''',line)):
            continue
        (bibid,score) = line.split()
        bibid = int(bibid)
        score = int(score)
        scores[bibid]=score
    logging.info("Read %d StackScores"%(len(scores)))
    return scores

def bind_namespace(ns_mgr, prefix, namespace):
    """Bind prefix to namespace in the NamespaceManager ns_mgr."""
    ns = Namespace(namespace)
    ns_mgr.bind(prefix, ns, override=False)
    return ns

cornell_prefix = 'http://draft.ld4l.org/cornell'
namespace_manager = NamespaceManager(Graph())
cnt = bind_namespace(namespace_manager, 'cnt', 'http://www.w3.org/2011/content#')
oa = bind_namespace(namespace_manager, 'oa', 'http://www.w3.org/ns/oa#')
ld4l = bind_namespace(namespace_manager, 'ld4l', 'http://bib.ld4l.org/ontology/')
rdf = bind_namespace(namespace_manager, 'rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

# Build URIRefs we'll need ahead for speed...
oa_hasTarget = oa['hasTarget']
oa_Annotation = oa['Annotation']
oa_hasBody = oa['hasBody']
oa_motivatedBy = oa['motivatedBy']
ld4l_Instance = ld4l['Instance']
ld4l_identifiedBy = ld4l['identifiedBy']
ld4l_LocalIlsIdentifier = ld4l['LocalIlsIdentifier']
ld4l_hasAnnotation = ld4l['hasAnnotation']
ld4l_stackViewScoring = ld4l['stackViewScoring']
cnt_ContentAsText = cnt['ContentAsText']
cnt_chars = cnt['chars']
rdf_type = rdf['type']
rdf_value = rdf['value']

def add_score(g, instance, score):
    """Add to graph g the StackScore score as annotation on instance."""
    istr = str(instance) # base ss-anno and ss-body URIs in instance URI
    annotation = URIRef('%s-ss-anno' % (istr))
    body = URIRef('%s-ss-body' % (istr))
    score = Literal(str(score))
    g.add( (instance, ld4l_hasAnnotation, annotation) )
    g.add( (annotation, oa_hasTarget, instance) )
    g.add( (annotation, RDF.type, oa_Annotation) )
    g.add( (annotation, oa_hasBody, body) )
    g.add( (annotation, oa_motivatedBy, ld4l_stackViewScoring) )
    g.add( (body, RDF.type, cnt_ContentAsText) )
    g.add( (body, cnt_chars, score) )

from rdflib.term import URIRef as URI
from rdflib.plugins.parsers.ntriples import NTriplesParser, unquote, uriquote, ParseError
import codecs

class StoreSink(object):
    """Trivial triple sink that stores one triple."""

    def __init__(self):
        """Initialize with empty store."""
        self.triple()

    def triple(self, s=None, p=None, o=None):
        """Store new triple."""
        self.s = s
        self.p = p
        self.o = o

    def last(self):
        """Return last triple else ValueError if none or has been read."""
        if (self.s is not None):
            s = self.s
            self.s = None
            return(s,self.p,self.o)
        else:
            raise ValueError()

class NTriplesStreamer(NTriplesParser):
    """Modification of NTriplesParse to provide iterator over triples."""

    def __init__(self, filename=None):
        """Initialize with an empty sink that we will use to yield the last triple."""
        self.sink = StoreSink()

    def open(self, filename):
        """Open that handles plain of gzipped files based on extension typing."""
        if (filename.endswith('.gz')):
            self.file = gzip.open(filename,'r')
        else:
            self.file = open(filename,'r')
        # since N-Triples 1.1 files can and should be utf-8 encoded
        self.file = codecs.getreader('utf-8')(self.file)

    def parse_generator(self,filename):
        """Parse f as an N-Triples file yielding triples.

        Modified version of rdflib.plugins.parsers.ntriples.NTriplesParser.parse(...)
        that works as a generator. 
        """
        self.open(filename)
        self.buffer = ''
        self.bad_lines = 0
        while True:
            self.line = self.readline()
            if self.line is None:
                break
            try:
                self.parseline()
                yield(self.sink.last())
            except ParseError:
                self.bad_lines += 1
                #raise ParseError("Invalid line: %r" % self.line)
            except ValueError:
                # no new data, just keep going
                pass
        if (self.bad_lines):
            logging.warn("Warning - ignored %d bad lines" % (self.bad_lines))

def process_file(bib_file, namespace_manager):
    """Process one file producing one annotation file.

    In each file look for Cornell ld4l:Instances to annotate with StackScores 
    based on extracting the bibid from ld4l:LocalIlsIdentifier triples. Data
    pattern is:

    instance? rdf:type ld4l:Instance .
    instance? ld4l:identifiedBy ils_id? .
    ild_id? rdf:type ld4l:LocalIlsIdentifier .
    ils_id? rdf:value literal_value? .

    For each input file, create an output file in the local directory but with a 
    similar name to the input file that contains the annotations.
    """
    # Start new greph for this file
    g = Graph()
    g.namespace_manager = namespace_manager
    nts = NTriplesStreamer()
    # Work out output file name
    ss_anno_file = split_multiext(os.path.basename(bib_file))[0] + "-ss-anno.nt.gz"
    ss_anno_fh = gzip.open(ss_anno_file,'w')
    logging.info("Parsing %s, writing %s" % (bib_file,ss_anno_file))
    # Read the file pulling out four types of triple we need and
    # stashing the results in in-memory data structures:
    instances = set()
    id_by = {}
    ils_ids = set()
    rdf_val = {}
    n = 0
    for (s,p,o) in nts.parse_generator(bib_file):
        n += 1
        try:
            if (p == rdf_type):
                if (o == ld4l_Instance):
                    # instance? rdf:type ld4l:instance --> instances
                    instances.add(str(s))
                elif (o == ld4l_LocalIlsIdentifier):
                    ils_ids.add(str(s))
            elif (p == ld4l_identifiedBy):
                # instance? ld4l:identifiedBy ils_id? .
                ss = str(s)
                if (ss not in id_by):
                    id_by[ss] = []
                id_by[ss].append(str(o))
            elif (p == rdf_value):
                # ils_id? rdf:value literal_value? . --- ASSUMING UNIQUE BY ILS_ID
                ss = str(s)
                if (ss not in rdf_val):
                    rdf_val[ss] = []
                rdf_val[ss].append(str(o))
        except Exception as e:
            logging.warn("%s - skipping triple (%r,%r,%r)", str(e), s, p, o)
    logging.info("-- read %d triples, extracted %d instances, %d ils_ids" % (n, len(instances), len(ils_ids)))
    # Go through all instances seeing whether we find a bibid
    n = 0
    for instance in instances:
        try:
            by_id = None
            if (instance not in id_by):
                continue # an instance with no bf:identifiedBy
            for by in id_by[instance]:
                if by in ils_ids:
                    by_id = by
                    break
            if (by_id is None or by_id not in rdf_val):
                continue # Non-ILS id, skip silently
            bibids = rdf_val[by_id]
            if (len(bibids)!=1):
                raise Exception("Expected one bibid for ILS id %s, got %d", by_id, len(bibids))
            add_score(g, URIRef(instance), scores.get(int(bibids[0]),1)) #score=1 if no value stored
            n += 1
        except Exception as e:
            if (e != None):
                logging.warn("%r - skipping instance %r", e, instance)
    # Write out
    try:
        ss_anno_fh.write(g.serialize(format='nt'))
        ss_anno_fh.close()
        logging.info("-- wrote %d scores" % (n))
    except Exception as e: 
        logging.warn("Writing %s failed: %s", bib_file, str(e))
    return(n)

p = optparse.OptionParser(description='Stackscore RDF generation for LD4L',
                          usage="%0 [[input-files.nt]]")
p.add_option('--stackscores', action='store', default='stackscores.dat.gz',
             help="Input file of stackscores, format is 'bibid stackscore', "
                  "one per line. Bibids without an entry will get an annotation "
                  "of stackscore 1.")
p.add_option('--logfile', action='store', default=None,
             help="Write logging output to file instead of STDOUT")
(opts, bib_files) = p.parse_args()

extra = {'filename': opts.logfile } if opts.logfile else {}
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO, **extra)

scores = read_stackscores(opts.stackscores)

# Iterate from bib_files treating each one separately because we know
# that they conatin complete LD4L models for a number of MARC records.
# 
start_time = time.time()
records = 0
for bib_glob in bib_files:
    for bib_file in glob.glob(bib_glob):
        records += process_file(bib_file, namespace_manager)
        elapsed = (time.time() - start_time)
        logging.info("-- %.1fs elapsed, %d records, overall rate %.2frecords/s" % (elapsed,records,records/elapsed))
logging.info("Done")

