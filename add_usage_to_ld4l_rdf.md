# Adding usage data to LD4L RDF

## LD4L ontology addition for StackScore

The ontology adds a [new annotation motivation](https://github.com/ld4l/ontology/blob/master/bibframe.ld4l/bibframe.ld4l.rdf#L3651-L3658) in order to express a StackScore:

```xml
<owl:NamedIndividual rdf:about="http://bibframe.ld4l.org/ontology/stackViewScoring">
        <rdf:type rdf:resource="&oa;Motivation"/>
        <rdfs:label xml:lang="en-us">stack view scoring</rdfs:label>
        <rdfs:comment xml:lang="en-us">The motivation that represents assigning a stack view score to the target resource.</rdfs:comment>
        <skos:inScheme rdf:resource="&oa;motivationScheme"/>
</owl:NamedIndividual>
```

## URIs corresponding to catalog records

Cornell ld4l data uses the prefix `http://draft.ld4l.org/cornell/` and catalog records are mapped to `bf:Works` with URIs `.../individual/_bibid_`, e.g.:

```
<http://draft.ld4l.org/cornell/individual/2>
```

for bibid 2, which corresponds with the catalog page <https://newcatalog.library.cornell.edu/catalog/2>.

From 2015-09-18 Cornell Engineering meeting:

  * LD converter makes URI like baseURI/bibidInstanceNumber from each MARC bib record, where the Number part is not predictable, this instance is linked to our bib id via:
    * a bf:systemNumber -> bf:identfiier [ bf_identifierValue -> "bibid", bf:identifierScheme -> "http://id.loc.gov/vocabulary/identifiers/systemNumber" ]
    * a bf:systemNumber -> http://www.worldcat.org/oclc/1345399 — where this is the link to the OCLCnum, but note that connecting via this would not work in cases where there is no corresponding oclc num
  * Rebecca will look at dedpuing Instances based on worldcat id, not sure whether will be any at Cornell, but there will be across institutions. Because the stackScore is done as an annotation there is no problem with loss of context when Instances are merged, the annotator gives this

From 2015-12-18 message, the ontology group decided that the StackScore data should be modeled as follows:

```
@prefix cnt:  <http://www.w3.org/2011/content#> .
@prefix oa:   <http://www.w3.org/ns/oa#> .
@prefix ld4l: <http://ld4l.org/ontology/bib> .

:some-instance ld4l:hasAnnotation :some-annotation .
:some-annotation oa:hasTarget :some-instance ;
 a oa:Annotation ; 
                 oa:hasBody :some-body ;
                 oa:motivatedBy ld4l:stackViewScoring .
:some-body a cnt:ContentAsText ;
           cnt:chars "some-literal" .
```
