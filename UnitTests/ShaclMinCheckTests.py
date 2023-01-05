from unittest import TestCase

from pyshacl import validate
from rdflib import Graph, URIRef, RDF, Literal, BNode


class ShaclCheckTests(TestCase):
    def test_minimal_failing_example_complex_literal(self):
        shacl_graph = Graph()
        shacl_graph.parse('shacl_min.ttl')

        data_graph = Graph()
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'), RDF.type,
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#MinimalClass')))
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'),
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#MinimalClass.simpleBooleanValue'),
                        Literal(True)))
        asset_id_node = BNode()
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'),
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject.assetId'),
                        asset_id_node))
        data_graph.add((asset_id_node,
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.identificator'),
                        Literal('https://data.awvvlaanderen.be/id/asset/0000')))
        data_graph.add((URIRef('https://data.awvvlaanderen.be/id/asset/0000'),
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#MinimalClass.simpleKeuzelijstValue'),
                        URIRef('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlTestKeuzelijst/waarde-1')))

        r = validate(data_graph,
                     shacl_graph=shacl_graph,
                     allow_infos=True,
                     allow_warnings=True)
        conforms, results_graph, results_text = r

        # for s, p, o in shacl_graph:
        #     print(f'{s} {p} {o}')

        print(results_text)
        self.assertTrue(conforms)
