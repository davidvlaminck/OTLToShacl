# resources:
# https://www.ida.liu.se/~robke04/SHACLTutorial/Introduction%20to%20SHACL.pdf
# https://shacl.org/playground/
# http://www.validatingrdf.com/
# https://15926.org/topics/SHACL/index.htm
import concurrent.futures
import os

import time
from os.path import abspath
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate

from SQLDbReader import SQLDbReader


def get_values_from_graph(keuzelijstnaam):
    g = Graph()
    keuzelijst_link = f"https://raw.githubusercontent.com/Informatievlaanderen/OSLOthema-wegenenverkeer/master/codelijsten/{keuzelijstnaam}.ttl"

    # return ['value1', 'value2']
    # parse the turtle file hosted on github
    try:
        try:
            g.parse(keuzelijst_link, format="turtle")
        except Exception as exc:
            if 'KlTestKeuzelijst' in keuzelijstnaam:
                base_dir = os.path.dirname(os.path.realpath(__file__))
                keuzelijst_link = abspath(f'{base_dir}/UnitTests/KlTestKeuzelijst.ttl')
                g.parse(keuzelijst_link, format="turtle")
        return g.subjects(predicate=RDF.type, object=SKOS.Concept)

    except:
        print('failed getting the ttl')


def process_enum_row(enum_row):
    enum_node = URIRef(enum_row[1])
    g.add((enum_node, RDF.type, SH.PropertyShape))
    g.add((enum_node, SH.path, URIRef(enum_row[1])))
    g.add((enum_node, SH.name, Literal(enum_row[0])))
    g.add((enum_node, SH.nodeKind, SH.IRI))
    g.add((enum_node, RDFS.label, Literal(enum_row[2])))
    if enum_row[4] != '':
        g.add((enum_node, OWL.deprecated, Literal(True)))

    enum_values = get_values_from_graph(enum_row[0])
    if enum_values is not None:
        enum_node_list = []
        for enum_value in enum_values:
            list_item_node = BNode()
            enum_node_list.append(list_item_node)
            g.add((list_item_node, RDF.first, enum_value))
        for index, node in enumerate(enum_node_list[0:-1]):
            g.add((enum_node_list[index], RDF.rest, enum_node_list[index + 1]))
        g.add((enum_node, URIRef('http://www.w3.org/ns/shacl#in'), enum_node_list[0]))


            #g.add((enum_node, SH.InConstraintComponent, enum_value))  # TODO ?? Shacl LIST?

    print('finished creating shacl for enum_row[1]')


if __name__ == '__main__':
    g = Graph()
    g.bind("sh", SH)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", Namespace("http://www.w3.org/2001/XMLSchema#"))
    g.add((URIRef('https://wegenenverkeer.data.vlaanderen.be'), RDF.type, OWL.Ontology))
    g.add((URIRef('https://wegenenverkeer.data.vlaanderen.be'), RDFS.comment, Literal(
        '''Met het programma Open Standaarden voor Linkende Organisaties (OSLO) zet de Vlaamse overheid in op een 
        éénduidige standaard voor de uitwisseling van informatie. De objecttypenbibliotheek (OTL) specificeert een 
        implementatiemodel voor de data-uitwisseling gedurende de volledige levenscyclus van onderdelen en installaties 
        die in brede zin verband houden met wegen en verkeer zoals gespecificeerd in de verschillende 
        Standaardbestekken 250, 260 en 270.''')))
    b = BNode()
    g.add((URIRef('https://wegenenverkeer.data.vlaanderen.be'), SH.declare, b))
    g.add((b, SH.prefix, Literal('awv')))  # TODO ??
    g.add((b, SH.namespace, URIRef('https://wegenenverkeer.data.vlaanderen.be')))

    reader = SQLDbReader(Path('UnitTests/OTL_AllCasesTestClass.db'))

    # classes
    for row in reader.perform_read_query(
            '''SELECT label_nl, name, uri, definition_nl, usagenote_nl, abstract, deprecated_version 
            FROM OSLOClass''',
            params={}):
        g.add((URIRef(row[2] + 'Shape'), RDF.type, SH.NodeShape))
        g.add((URIRef(row[2] + 'Shape'), SH.targetClass, URIRef(row[2])))
        g.add((URIRef(row[2] + 'Shape'), RDFS.label, Literal(row[0])))
        g.add(
            (URIRef(row[2] + 'Shape'), RDFS.comment, Literal(row[3])))  # TODO  definition but no usagenote as comment?
        if row[6] != '':
            g.add((URIRef(row[2] + 'Shape'), OWL.deprecated, Literal(True)))

    # inheritances
    for row in reader.perform_read_query(
            '''SELECT base_uri, class_uri, deprecated_version FROM InternalBaseClass''',
            params={}):
        g.add((URIRef(row[1]), RDFS.subClassOf, URIRef(row[0])))

    # add properties
    for row in reader.perform_read_query(
            '''SELECT name, label_nl, definition_nl, class_uri, kardinaliteit_min, kardinaliteit_max, uri, type, 
            overerving, constraints, readonly, usagenote_nl, OSLOAttributen.deprecated_version, TypeLinkTabel.item_tabel 
        FROM OSLOAttributen 
            LEFT JOIN TypeLinkTabel ON OSLOAttributen."type" = TypeLinkTabel.item_uri
        WHERE overerving = 0;''',
            params={}):
        property_node = URIRef(row[6] + 'Shape')
        g.add((URIRef(row[3] + 'Shape'), SH.property, property_node))
        g.add((property_node, RDF.type, SH.PropertyShape))
        g.add((property_node, SH.datatype, URIRef(row[7])))
        g.add((property_node, SH.path, URIRef(row[6])))
        g.add((property_node, SH.name, Literal(row[0])))
        if row[7] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[7]:
            g.add((property_node, SH.nodeKind, SH.Literal))
        elif row[13] == 'OSLOEnumeration':
            g.add((property_node, SH.nodeKind, SH.IRI))
        else:
            g.add((property_node, SH.nodeKind, SH.BlankNode))
        # g.add((property_node, RDFS.comment, Literal(row[2]))) # not needed...
        g.add((property_node, RDFS.label, Literal(row[1])))
        g.add((property_node, SH.minCount, Literal(0)))  # TODO can't enforce kardinaliteit_min = 1
        if row[5] != '*':
            g.add((property_node, SH.maxCount, Literal(int(row[5]))))
        if row[12] != '':
            g.add((property_node, OWL.deprecated, Literal(True)))

    # add complex properties
    last_created_prop_ref = None
    for row in reader.perform_read_query(
            '''SELECT dtc.name, dtc.uri, dtc.label_nl, dtc.deprecated_version, dtca.name, dtca.label_nl, 
            dtca.class_uri, dtca.kardinaliteit_min, dtca.kardinaliteit_max, dtca.uri, dtca.type, dtca.deprecated_version 
            FROM OSLODatatypeComplex dtc 
                LEFT JOIN OSLODatatypeComplexAttributen dtca ON dtc.uri = dtca.class_uri
            ORDER BY dtc.uri;''',
            params={}):
        property_node_ref = URIRef(row[1])
        if last_created_prop_ref != property_node_ref:
            last_created_prop_ref = property_node_ref
            g.add((property_node_ref, RDF.type, SH.PropertyShape))
            g.add((property_node_ref, SH.name, Literal(row[0])))
            g.add((property_node_ref, SH.path, URIRef(row[1])))
            g.add((property_node_ref, RDFS.label, Literal(row[2])))
            if row[3] != '':
                g.add((property_node_ref, OWL.deprecated, Literal(True)))

        attribute_node_ref = URIRef(row[9] + 'Shape')
        g.add((property_node_ref, SH.property, attribute_node_ref))
        g.add((attribute_node_ref, RDF.type, SH.PropertyShape))
        g.add((attribute_node_ref, SH.name, Literal(row[4])))
        g.add((attribute_node_ref, SH.path, URIRef(row[9])))
        g.add((attribute_node_ref, RDFS.label, Literal(row[5])))
        g.add((attribute_node_ref, SH.datatype, URIRef(row[10])))
        if row[11] != '':
            g.add((attribute_node_ref, OWL.deprecated, Literal(True)))
        g.add((attribute_node_ref, SH.minCount, Literal(0)))
        if row[8] != '*':
            g.add((attribute_node_ref, SH.maxCount, Literal(int(row[8]))))

    # add primitive properties
    last_created_prop_ref = None
    for row in reader.perform_read_query(
            '''SELECT dtp.name, dtp.uri, dtp.label_nl, dtp.deprecated_version, dtpa.name, dtpa.label_nl, 
            dtpa.class_uri, dtpa.kardinaliteit_min, dtpa.kardinaliteit_max, dtpa.uri, dtpa.type, dtpa.deprecated_version, 
            dtpa.constraints
            FROM OSLODatatypePrimitive dtp 
                LEFT JOIN OSLODatatypePrimitiveAttributen dtpa ON dtp.uri = dtpa.class_uri
            ORDER BY dtp.uri;''',
            params={}):
        property_node_ref = URIRef(row[1])
        if last_created_prop_ref != property_node_ref:
            last_created_prop_ref = property_node_ref
            if row[1] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[1]:
                continue
            g.add((property_node_ref, RDF.type, SH.PropertyShape))
            g.add((property_node_ref, SH.name, Literal(row[0])))
            g.add((property_node_ref, SH.path, URIRef(row[1])))
            g.add((property_node_ref, RDFS.label, Literal(row[2])))
            g.add((property_node_ref, SH.nodeKind, SH.BlankNode))
            if row[3] != '':
                g.add((property_node_ref, OWL.deprecated, Literal(True)))

        if row[1] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[1]:
            continue
        attribute_node_ref = URIRef(row[9] + 'Shape')
        g.add((property_node_ref, SH.property, attribute_node_ref))
        g.add((attribute_node_ref, RDF.type, SH.PropertyShape))
        g.add((attribute_node_ref, SH.name, Literal(row[4])))
        g.add((attribute_node_ref, SH.path, URIRef(row[9])))
        g.add((attribute_node_ref, RDFS.label, Literal(row[5])))
        g.add((attribute_node_ref, SH.datatype, URIRef(row[10])))
        if row[10] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[10]:
            g.add((attribute_node_ref, SH.nodeKind, SH.Literal))
        if row[11] != '':
            g.add((attribute_node_ref, OWL.deprecated, Literal(True)))
        g.add((attribute_node_ref, SH.minCount, Literal(0)))
        if row[8] != '*':
            g.add((attribute_node_ref, SH.maxCount, Literal(int(row[8]))))
        if row[10] == 'http://www.w3.org/2000/01/rdf-schema#Literal':
            if '"^^cdt:ucumunit' in row[12]:
                unit = row[12].split('"')[1]
                g.add((attribute_node_ref, SH.hasValue, Literal(unit)))

    # add union properties
    last_created_prop_ref = None
    for row in reader.perform_read_query(
            '''SELECT dtu.name, dtu.uri, dtu.label_nl, dtu.deprecated_version, dtua.name, dtua.label_nl, 
            dtua.class_uri, dtua.kardinaliteit_min, dtua.kardinaliteit_max, dtua.uri, dtua.type, dtua.deprecated_version 
            FROM OSLODatatypeComplex dtu 
                LEFT JOIN OSLODatatypeComplexAttributen dtua ON dtu.uri = dtua.class_uri
            ORDER BY dtu.uri;''',
            params={}):
        property_node_ref = URIRef(row[1])
        if last_created_prop_ref != property_node_ref:
            last_created_prop_ref = property_node_ref
            g.add((property_node_ref, RDF.type, SH.PropertyShape))
            g.add((property_node_ref, SH.name, Literal(row[0])))
            g.add((property_node_ref, SH.path, URIRef(row[1])))
            g.add((property_node_ref, RDFS.label, Literal(row[2])))
            if row[3] != '':
                g.add((property_node_ref, OWL.deprecated, Literal(True)))
            # TODO add union type constraint (max 1 of its properties can have data)

        attribute_node_ref = URIRef(row[9] + 'Shape')
        g.add((property_node_ref, SH.property, attribute_node_ref))
        g.add((attribute_node_ref, RDF.type, SH.PropertyShape))
        g.add((attribute_node_ref, SH.name, Literal(row[4])))
        g.add((attribute_node_ref, SH.path, URIRef(row[9])))
        g.add((attribute_node_ref, RDFS.label, Literal(row[5])))
        g.add((attribute_node_ref, SH.datatype, URIRef(row[10])))
        if row[11] != '':
            g.add((attribute_node_ref, OWL.deprecated, Literal(True)))
        g.add((attribute_node_ref, SH.minCount, Literal(0)))
        if row[8] != '*':
            g.add((attribute_node_ref, SH.maxCount, Literal(int(row[8]))))


    # add enum types
    enum_rows = reader.perform_read_query(
        '''SELECT name, uri, label_nl, codelist, deprecated_version FROM OSLOEnumeration;''',
        params={})
    # use multithreading
    executor = concurrent.futures.ThreadPoolExecutor()
    futures = [executor.submit(process_enum_row, enum_row=enum_row) for enum_row in enum_rows]
    concurrent.futures.wait(futures)

    print(g.serialize(format='turtle'))



    h = Graph()
    start = time.time()
    h.parse('testclass.ttl')
    end = time.time()
    print(f'Loaded {len(h)} objects in {round(end - start, 2)} seconds')

    start = time.time()
    r = validate(h,
                 shacl_graph=g,
                 allow_infos=True,
                 allow_warnings=True)
    conforms, results_graph, results_text = r
    end = time.time()
    print(f'Validation done in {round(end - start, 2)} seconds')
    print(results_text)
