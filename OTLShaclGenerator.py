from pathlib import Path
from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS

from SQLDbReader import SQLDbReader


class OTLShaclGenerator:
    @staticmethod
    def generate_shacl_from_otl(subset_path: Path, shacl_path: Path) -> Graph:
        if subset_path is None or str(subset_path) == '':
            raise FileNotFoundError(str(subset_path) + " is not a valid path. File does not exist.")
        if shacl_path is None or str(shacl_path) == '':
            raise ValueError(str(shacl_path) + " is not a valid path. Can not create shacl file.")
        reader = SQLDbReader(subset_path)

        g = OTLShaclGenerator.get_initial_graph()

        # classes
        class_rows = OTLShaclGenerator.read_classes_from_reader(reader=reader)
        g = OTLShaclGenerator.add_classes_to_graph(g=g, rows=class_rows)

        # inheritances
        inheritance_rows = OTLShaclGenerator.read_inheritances_from_reader(reader=reader)
        g = OTLShaclGenerator.add_inheritances_to_graph(g=g, rows=inheritance_rows)

        # properties
        property_rows = OTLShaclGenerator.read_properties_from_reader(reader=reader)
        g = OTLShaclGenerator.add_properties_to_graph(g=g, rows=property_rows)

        g.serialize(format='turtle', destination=shacl_path)

        return g

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

