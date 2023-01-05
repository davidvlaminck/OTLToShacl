import time
from pathlib import Path
from unittest import TestCase
from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate


class ShaclCheckTests(TestCase):
    def test_verify_bool(self):
        shacl_graph = Graph()
        shacl_graph.parse(Path('../otl_shacl.ttl'))

        data_graph = Graph()
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'), RDF.type,
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass')))
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'),
                        URIRef(
                            'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testBooleanField'),
                        Literal(1)))
        asset_id_node = BNode()
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'),
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject.assetId'),
                        asset_id_node))
        # data_graph.add((complex_node, RDF.type,
        #                 URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#MinimalClass.simpleBooleanValueShape')))
        data_graph.add((asset_id_node,
                        URIRef(
                            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.identificator'),
                        Literal('https://data.awvvlaanderen.be/id/asset/0000')))

        print(data_graph.serialize(format='turtle'))

        start = time.time()
        r = validate(data_graph,
                     shacl_graph=shacl_graph,
                     allow_infos=True,
                     allow_warnings=True)
        conforms, results_graph, results_text = r
        end = time.time()
        print(f'Validation done in {round(end - start, 2)} seconds')
        print(results_text)
        self.assertTrue(conforms)
