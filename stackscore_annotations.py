#!/usr/bin/env python
"""
Add StackScore usage data as annotations.

Timing:
  10s to read 2.3M stackscores into dict
   8s to parse 1430 sample records and write annotations
  => expect ~12h to write annotations for 8M records

"""

import glob
import gzip
import os.path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, RDF
import re

def split_multiext(filename):
    """Wrapper around os.path.splitext to remove potentially multiple extensions."""
    all_ext = ''
    while True:
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
    print("Reading StackScores from %s..." % (filename))
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
    print("Read %d StackScores"%(len(scores)))
    return scores

def bind_namespace(ns_mgr, prefix, namespace):
    ns = Namespace(namespace)
    ns_mgr.bind(prefix, ns, override=False)
    return ns

cornell_prefix = 'http://draft.ld4l.org/cornell'
namespace_manager = NamespaceManager(Graph())
cnt = bind_namespace(namespace_manager, 'cnt', 'http://www.w3.org/2011/content#')
oa = bind_namespace(namespace_manager, 'oa', 'http://www.w3.org/ns/oa#')
ld4l = bind_namespace(namespace_manager, 'ld4l', 'http://ld4l.org/ontology/bib/')

# Build URIRefs we'll need ahead for speed...
ld4l_hasAnnotation = ld4l['hasAnnotation']
oa_hasTarget = oa['hasTarget']
oa_Annotation = oa['Annotation']
oa_hasBody = oa['hasBody']
oa_motivatedBy = oa['motivatedBy']
ld4l_stackViewScoring = ld4l['stackViewScoring']
cnt_ContentAsText = cnt['ContentAsText']
cnt_chars = cnt['chars']

def add_score(g, instance, score):
    """Add to graph g the StackScore score as annotation on instance."""
    istr = str(instance) # base ss-anno and ss-body URIs in instance URI
    annotation = URIRef('%s/ss-anno' % (istr))
    body = URIRef('%s/ss-body' % (istr))
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
        self.sink = StoreSink()

    def open(self, filename):
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
            print("Warning - ignored %d bad lines" % (self.bad_lines))

g = Graph()
g.namespace_manager = namespace_manager

ss_file = 'stackscores.dat.gz'
scores = read_stackscores(ss_file)

rdf_type = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
ld4l_instance = URIRef('http://ld4l.org/ontology/bib/Instance')

# Iterate from bib_files looking for Cornell ld4l:Instances to annotate with StackScores.
# For each input file, create an output file in the local directory but with a 
# similar name to the input file that contains the annotations.
bib_files = glob.glob('/cul/data/ld4l/2015-12-09_sample_records/ld4l/cornell*')
#bib_files = glob.glob('/cul/data/ld4l/cornell_rdf/*.nt.gz')
nts = NTriplesStreamer()
for bib_file in bib_files:
    ss_anno_file = split_multiext(os.path.basename(bib_file))[0] + "-ss-anno.nt.gz"
    ss_anno_fh = gzip.open(ss_anno_file,'w')
    print("Parsing %s, writing %s" % (bib_file,ss_anno_file))
    for (s,p,o) in nts.parse_generator(bib_file):
        # Look for triples: s rdf:type ld4l:instance
        if (p == rdf_type and o == ld4l_instance):
            # bibid is number at end of bf:Work URI
            m = re.match(r'''http://draft.ld4l.org/cornell/(individual/)?(\d+)instance(\d+)$''',str(s))
            if (m):
                bibid = int(m.group(2))
                add_score(g,s,scores.get(bibid,1)) #score=1 if no value stored
            else:
                raise Exception("Unexpected instance id in: %s %s %s" % (s,p,o))
    ss_anno_fh.write(g.serialize(format='nt'))
    ss_anno_fh.close()

