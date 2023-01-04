import time
from unittest import TestCase
from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate


class ShaclCheckTests(TestCase):
    def test_verify_bool(self):
        shack_graph = Graph()
        shack_graph.parse('shacl.ttl')

        data_graph = Graph()
        start = time.time()
        data_graph.parse('testclass.ttl')
        end = time.time()
        print(f'Loaded {len(data_graph)} objects in {round(end - start, 2)} seconds')

        start = time.time()
        r = validate(data_graph,
                     shacl_graph=shack_graph,
                     allow_infos=True,
                     allow_warnings=True)
        conforms, results_graph, results_text = r
        end = time.time()
        print(f'Validation done in {round(end - start, 2)} seconds')
        print(results_text)
        self.assertTrue(conforms)
