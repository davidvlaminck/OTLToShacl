from pathlib import Path

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH

from SQLDbReader import SQLDbReader

if __name__ == '__main__':
    g = Graph()
    g.bind("sh", SH)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", Namespace("http://www.w3.org/2001/XMLSchema#"))

    g.parse('owl2spec.ttl')
    g.add((URIRef('https://wegenenverkeer.data.vlaanderen.be'), RDF.type, OWL.Ontology))
    g.commit()

    reader = SQLDbReader(Path('UnitTests/OTL_AllCasesTestClass.db'))

    # classes
    for row in reader.perform_read_query(
            '''SELECT label_nl, name, uri, definition_nl, usagenote_nl, abstract, deprecated_version 
            FROM OSLOClass''',
            params={}):
        g.add((URIRef(row[2]), RDF.type, OWL.Class))
        g.add((URIRef(row[2]), RDFS.label, Literal(row[0])))
        g.add((URIRef(row[2]), RDFS.comment, Literal(row[3])))  # definition but no usagenote as comment?
        if row[6] != '':
            g.add((URIRef(row[2]), OWL.deprecated, Literal(True)))

    # inheritances
    for row in reader.perform_read_query(
            '''SELECT base_uri, class_uri, deprecated_version FROM InternalBaseClass''',
            params={}):
        g.add((URIRef(row[1]), RDFS.subClassOf, URIRef(row[0])))

        print(row)
        # add class

    print(g.serialize(format='turtle'))
