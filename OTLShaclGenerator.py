import os
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS

from SQLDbReader import SQLDbReader


class OTLShaclGenerator:
    @staticmethod
    def generate_shacl_from_otl(subset_path: Path, shacl_path: Path, ont_path: Path) -> (Graph, Graph):
        if subset_path is None or str(subset_path) == '':
            raise FileNotFoundError(str(subset_path) + " is not a valid path. File does not exist.")
        if shacl_path is None or str(shacl_path) == '':
            raise ValueError(str(shacl_path) + " is not a valid path. Can not create shacl file.")
        if ont_path is None or str(ont_path) == '':
            raise ValueError(str(ont_path) + " is not a valid path. Can not create ontology file.")
        reader = SQLDbReader(subset_path)

        g = OTLShaclGenerator.get_initial_graph()

        # classes
        class_rows = OTLShaclGenerator.read_classes_from_reader(reader=reader)
        g = OTLShaclGenerator.add_classes_to_graph(g=g, rows=class_rows)

        # inheritances
        h = OTLShaclGenerator.get_initial_graph()
        inheritance_rows = OTLShaclGenerator.read_inheritances_from_reader(reader=reader)
        h = OTLShaclGenerator.add_owl_classes_to_graph(g=h, rows=class_rows)
        h = OTLShaclGenerator.add_inheritances_to_graph(g=h, rows=inheritance_rows)

        # properties
        property_rows = OTLShaclGenerator.read_properties_from_reader(reader=reader)
        g = OTLShaclGenerator.add_properties_to_graph(g=g, rows=property_rows)

        # complex attributes
        complex_attr_rows = OTLShaclGenerator.read_complex_attributes_from_reader(reader=reader)
        g = OTLShaclGenerator.add_complex_attributes_to_graph(g=g, rows=complex_attr_rows)

        # enums
        enum_rows = OTLShaclGenerator.read_enums_from_reader(reader=reader)
        g = OTLShaclGenerator.add_enums_to_graph(g=g, rows=enum_rows)

        # primitive attributes
        primitive_attr_rows = OTLShaclGenerator.read_primitive_attributes_from_reader(reader=reader)
        g = OTLShaclGenerator.add_primitive_attributes_to_graph(g=g, rows=primitive_attr_rows)

        g.serialize(format='turtle', destination=shacl_path)
        h.serialize(format='turtle', destination=ont_path)

        return g, h

    @staticmethod
    def get_initial_graph() -> Graph:
        g = Graph()
        g.bind('sh', SH)
        g.bind('owl', OWL)
        g.bind('rdf', RDF)
        g.bind('rdfs', RDFS)
        g.bind('xsd', Namespace('http://www.w3.org/2001/XMLSchema#'))
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

        g.bind('asset', 'https://data.awvvlaanderen.be/id/asset/')
        g.bind('imel', 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#')
        g.bind('onderdeel', 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#')
        g.bind('abs', 'https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#')
        g.bind('kl', 'https://wegenenverkeer.data.vlaanderen.be/id/concept/')

        return g

    @staticmethod
    def read_classes_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''SELECT label_nl, name, uri, definition_nl, usagenote_nl, abstract, deprecated_version FROM OSLOClass''',
            params={})

    @staticmethod
    def add_classes_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for row in rows:
            g.add((URIRef(row[2] + 'Shape'), RDF.type, SH.NodeShape))
            g.add((URIRef(row[2] + 'Shape'), SH.targetClass, URIRef(row[2])))
            g.add((URIRef(row[2] + 'Shape'), RDFS.label, Literal(row[0])))
            if row[6] != '':
                g.add((URIRef(row[2] + 'Shape'), OWL.deprecated, Literal(True)))
        return g

    @staticmethod
    def add_owl_classes_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for row in rows:
            g.add((URIRef(row[2]), RDF.type, OWL.Class))
        return g

    @staticmethod
    def read_properties_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''SELECT name, label_nl, definition_nl, class_uri, kardinaliteit_min, kardinaliteit_max, uri, type, 
                    overerving, constraints, readonly, usagenote_nl, OSLOAttributen.deprecated_version, 
                    TypeLinkTabel.item_tabel 
                FROM OSLOAttributen 
                    LEFT JOIN TypeLinkTabel ON OSLOAttributen."type" = TypeLinkTabel.item_uri
                WHERE overerving = 0;''', params={})

    @staticmethod
    def add_properties_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for row in rows:
            class_ref = URIRef(row[3] + 'Shape')
            shape_ref = URIRef(row[6] + 'Shape')

            g.add((class_ref, SH.property, shape_ref))
            g.add((shape_ref, RDF.type, SH.PropertyShape))
            g.add((shape_ref, SH.path, URIRef(row[6])))
            g.add((shape_ref, SH.name, Literal(row[0])))
            g.add((shape_ref, RDFS.label, Literal(row[1])))

            if row[7] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[7]:
                g.add((shape_ref, SH.nodeKind, SH.Literal))
                g.add((shape_ref, SH.datatype, URIRef(row[7])))
            elif row[13] == 'OSLOEnumeration':
                g.add((shape_ref, SH.nodeKind, SH.IRI))
                g.add((shape_ref, RDFS.comment, URIRef(row[7])))
            else:
                g.add((shape_ref, SH.nodeKind, SH.BlankNode))
                g.add((shape_ref, RDFS.comment, URIRef(row[7])))

            g.add((shape_ref, SH.minCount, Literal(0)))  # TODO can't enforce kardinaliteit_min = 1
            if row[5] != '*':
                g.add((shape_ref, SH.maxCount, Literal(int(row[5]))))
            if row[12] != '':
                g.add((shape_ref, OWL.deprecated, Literal(True)))
        return g

    @staticmethod
    def read_inheritances_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''SELECT base_uri, class_uri, deprecated_version FROM InternalBaseClass''',
            params={})

    @staticmethod
    def add_inheritances_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for row in rows:
            g.add((URIRef(row[1]), RDFS.subClassOf, URIRef(row[0])))
        return g

    @staticmethod
    def read_complex_attributes_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''SELECT dtc.name, dtc.uri, dtc.label_nl, dtc.deprecated_version, dtca.name, dtca.label_nl, dtca.class_uri, 
                dtca.kardinaliteit_min, dtca.kardinaliteit_max, dtca.uri, dtca.type, dtca.deprecated_version, 
                dtca.constraints, TypeLinkTabel.item_tabel  
            FROM OSLODatatypeComplex dtc 
                LEFT JOIN OSLODatatypeComplexAttributen dtca ON dtc.uri = dtca.class_uri
                LEFT JOIN TypeLinkTabel ON dtca."type" = TypeLinkTabel.item_uri
            ORDER BY dtc.uri;''', params={})

    @staticmethod
    def add_attributes_to_graph(g: Graph, rows: [tuple], attribute_type: str) -> Graph:
        for row in rows:
            attribute_node_ref = URIRef(row[9] + 'Shape')

            g.add((attribute_node_ref, RDF.type, SH.PropertyShape))
            g.add((attribute_node_ref, SH.name, Literal(row[4])))
            g.add((attribute_node_ref, SH.path, URIRef(row[9])))
            g.add((attribute_node_ref, RDFS.label, Literal(row[5])))

            if row[10] == str(RDFS.Literal) or 'http://www.w3.org/2001/XMLSchema' in row[10]:
                g.add((attribute_node_ref, SH.nodeKind, SH.Literal))
                g.add((attribute_node_ref, SH.datatype, URIRef(row[10])))
            elif row[13] == 'OSLOEnumeration':
                g.add((attribute_node_ref, SH.nodeKind, SH.IRI))
                g.add((attribute_node_ref, RDFS.comment, URIRef(row[10])))
            else:
                g.add((attribute_node_ref, SH.nodeKind, SH.BlankNode))
                g.add((attribute_node_ref, RDFS.comment, URIRef(row[10])))

            if row[11] != '':
                g.add((attribute_node_ref, OWL.deprecated, Literal(True)))
            g.add((attribute_node_ref, SH.minCount, Literal(0)))  # can't enforce kardinaliteit_min = 1
            if row[8] != '*':
                g.add((attribute_node_ref, SH.maxCount, Literal(int(row[8]))))

            if attribute_type == 'primitive':
                if row[10] == str(RDFS.Literal):
                    if '"^^cdt:ucumunit' in row[12]:
                        unit = row[12].split('"')[1]
                        g.add((attribute_node_ref, SH.equals, Literal(unit)))


        # do this after creating the shapes to avoid missing attributes in complex datatypes (nested)
        for row in rows:
            subjects = g.subjects(predicate=RDFS.comment, object=URIRef(row[1]))
            for subj in subjects:
                g.add((subj, SH.property, URIRef(row[9] + 'Shape')))

        return g

    @staticmethod
    def add_complex_attributes_to_graph(g: Graph, rows: [tuple]) -> Graph:
        return OTLShaclGenerator.add_attributes_to_graph(g, rows, 'complex')

    @staticmethod
    def get_enum_values_from_graph(keuzelijstnaam):
        g = Graph()
        keuzelijst_link = f"https://raw.githubusercontent.com/Informatievlaanderen/OSLOthema-wegenenverkeer/master/codelijsten/{keuzelijstnaam}.ttl"

        if 'KlTestKeuzelijst' in keuzelijstnaam:
            base_dir = os.path.dirname(os.path.realpath(__file__))
            keuzelijst_link = Path(f'{base_dir}/UnitTests/KlTestKeuzelijst.ttl')
            g.parse(keuzelijst_link, format="turtle")
        else:
            try:
                g.parse(keuzelijst_link, format="turtle")
            except:
                print('failed getting the ttl')

        return g.subjects(predicate=RDF.type, object=SKOS.Concept)

    @staticmethod
    def read_enums_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''SELECT name, uri, label_nl, codelist, deprecated_version FROM OSLOEnumeration;''', params={})

    @staticmethod
    def add_enums_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for enum_row in rows:
            subjects = g.subjects(predicate=RDFS.comment, object=URIRef(enum_row[1]))
            for subj in subjects:
                enum_values = OTLShaclGenerator.get_enum_values_from_graph(enum_row[0])
                if enum_values is not None:
                    enum_node_list = []
                    for enum_value in enum_values:
                        list_item_node = BNode()
                        enum_node_list.append(list_item_node)
                        g.add((list_item_node, RDF.first, enum_value))
                    for index, node in enumerate(enum_node_list[0:-1]):
                        g.add((enum_node_list[index], RDF.rest, enum_node_list[index + 1]))
                    g.add((enum_node_list[-1], RDF.rest, RDF.nil))
                    g.add((subj, URIRef('http://www.w3.org/ns/shacl#in'), enum_node_list[0]))

        return g

    @staticmethod
    def read_primitive_attributes_from_reader(reader) -> [tuple]:
        return reader.perform_read_query(
            '''
            SELECT dtp.name, dtp.uri, dtp.label_nl, dtp.deprecated_version, dtpa.name, dtpa.label_nl, dtpa.class_uri, 
                dtpa.kardinaliteit_min, dtpa.kardinaliteit_max, dtpa.uri, dtpa.type, dtpa.deprecated_version, 
                dtpa.constraints, TypeLinkTabel.item_tabel 
            FROM OSLODatatypePrimitive dtp 
                LEFT JOIN OSLODatatypePrimitiveAttributen dtpa ON dtp.uri = dtpa.class_uri
                LEFT JOIN TypeLinkTabel ON dtpa."type" = TypeLinkTabel.item_uri
            ORDER BY dtp.uri;''', params={})

    @staticmethod
    def add_primitive_attributes_to_graph(g: Graph, rows: [tuple]) -> Graph:
        for row in rows:
            if row[1] == 'http://www.w3.org/2000/01/rdf-schema#Literal' or 'http://www.w3.org/2001/XMLSchema' in row[1]:
                continue

            attribute_node_ref = URIRef(row[9] + 'Shape')

            subjects = g.subjects(predicate=RDFS.comment, object=URIRef(row[1]))
            for subj in subjects:
                g.add((subj, SH.property, attribute_node_ref))

            g.add((attribute_node_ref, RDF.type, SH.PropertyShape))
            g.add((attribute_node_ref, SH.name, Literal(row[4])))
            g.add((attribute_node_ref, SH.path, URIRef(row[9])))
            g.add((attribute_node_ref, RDFS.label, Literal(row[5])))

            g.add((attribute_node_ref, SH.nodeKind, SH.Literal))
            g.add((attribute_node_ref, SH.datatype, URIRef(row[10])))

            if row[11] != '':
                g.add((attribute_node_ref, OWL.deprecated, Literal(True)))
            g.add((attribute_node_ref, SH.minCount, Literal(0)))  # can't enforce kardinaliteit_min = 1
            if row[8] != '*':
                g.add((attribute_node_ref, SH.maxCount, Literal(int(row[8]))))

            if row[10] == str(RDFS.Literal):
                if '"^^cdt:ucumunit' in row[12]:
                    unit = row[12].split('"')[1]
                    g.add((attribute_node_ref, SH.equals, Literal(unit)))

        return g

