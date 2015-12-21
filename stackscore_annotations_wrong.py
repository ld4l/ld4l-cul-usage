#!/usr/bin/env python
"""
A WRONG implementation of adding usage data as annotations.

This is WRONG because it adds annotations to the bf:Work resources created
for each catalog record. The annotations should instead be added to the
bf:Instance resources. However, it is not possible to calculate the bf:Instance
URIs from the the bibid, whereas it is possible to calculate the bf:Work
URIs... hence this first experiment.

2015-12-18 runtimes:
  10k chunk - 5s
  100k chunk - 6.149s
  1M chunk - 9m25.631s
  output is 7x as many triples
"""

import gzip
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, RDF
import re

def bind_namespace(ns_mgr, prefix, namespace):
    ns = Namespace(namespace)
    ns_mgr.bind(prefix, ns, override=False)
    return ns

cornell_prefix = 'http://draft.ld4l.org/cornell'
namespace_manager = NamespaceManager(Graph())
cnt = bind_namespace(namespace_manager, 'cnt', 'http://www.w3.org/2011/content#')
oa = bind_namespace(namespace_manager, 'oa', 'http://www.w3.org/ns/oa#')
ld4l = bind_namespace(namespace_manager, 'ld4l', 'http://ld4l.org/ontology/bib/')

def add_score(g, bibid, score):
    """Add score for bibid to g."""
    instance = URIRef('%s/individual/%d' % (cornell_prefix,bibid))
    annotation = URIRef('%s/individual/%d/ss-anno' % (cornell_prefix,bibid))
    body = URIRef('%s/individual/%s/ss-body' % (cornell_prefix,bibid))
    score = Literal(str(score))
    g.add( (instance, ld4l['hasAnnotation'], annotation) )
    g.add( (annotation, oa['hasTarget'], instance) )
    g.add( (annotation, RDF.type, oa['Annotation']) )
    g.add( (annotation, oa['hasBody'], body) )
    g.add( (annotation, oa['motivatedBy'], ld4l['stackViewScoring']) )
    g.add( (body, RDF.type, cnt['ContentAsText']) )
    g.add( (body, cnt['chars'], score) )

g = Graph()
g.namespace_manager = namespace_manager

file = 'stackscores.dat.gz'
fh = gzip.open(file,'r')

n = 0
for line in fh:
    n+=1
    if (re.match(r'''\s*#''',line)):
        continue
    (bibid,score) = line.split()
    bibid = int(bibid)
    score = int(score)
    add_score(g,bibid,score)
    if (n>1000000):
        break

print g.serialize(format='nt')
