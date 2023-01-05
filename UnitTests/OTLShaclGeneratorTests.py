import os
from pathlib import Path
from unittest import TestCase

from OTLShaclGenerator import OTLShaclGenerator
from SQLDbReader import SQLDbReader

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate


class OTLShaclGeneratorTests(TestCase):
    def test_create_without_subset(self):
        with self.assertRaises(FileNotFoundError):
            OTLShaclGenerator.generate_shacl_from_otl(Path(''), shacl_path=Path())

    def test_generate_subset_and_test_data(self):
        shacl = OTLShaclGenerator.generate_shacl_from_otl(subset_path=Path('OTL_AllCasesTestClass.db'),
                                                          shacl_path=Path('generated_shacl.ttl'))
        data_g = Graph()
        asset_ref = URIRef('https://data.awvvlaanderen.be/id/asset/0000')
        data_g.add((asset_ref, RDF.type,
                    URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass')))

        with self.subTest('using correct boolean value'):
            good_boolean_graph = (asset_ref,
                                  URIRef(
                                      'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testBooleanField'),
                                  Literal(True))
            data_g.add(good_boolean_graph)
            r = validate(data_g,
                         shacl_graph=shacl,
                         allow_infos=True,
                         allow_warnings=True)
            conforms, results_graph, results_text = r
            self.assertTrue(conforms)
            data_g.remove(good_boolean_graph)

        with self.subTest('using incorrect boolean value'):
            bad_boolean_graph = (asset_ref,
                                 URIRef(
                                     'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testBooleanField'),
                                 Literal(1))
            data_g.add(bad_boolean_graph)
            r = validate(data_g,
                         shacl_graph=shacl,
                         allow_infos=True,
                         allow_warnings=True)
            conforms, results_graph, results_text = r
            self.assertFalse(conforms)
            data_g.remove(bad_boolean_graph)

        with self.subTest('using boolean value in inherited attribute'):
            inherited_boolean_graph = (asset_ref,
                                       URIRef(
                                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMDBStatus.isActief'),
                                       Literal(True))
            data_g.add(inherited_boolean_graph)
            r = validate(data_g,
                         shacl_graph=shacl,
                         allow_infos=True,
                         allow_warnings=True)
            conforms, results_graph, results_text = r
            self.assertTrue(conforms)
            data_g.remove(inherited_boolean_graph)

        with self.subTest('using incorrect boolean value in inherited attribute'):
            bad_boolean_graph = (asset_ref,
                                 URIRef(
                                     'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMDBStatus.isActief'),
                                 Literal(1))
            data_g.add(bad_boolean_graph)

            inheritance_graph1 = (URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject'),
                                  RDFS.subClassOf,
                                  URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMDBStatus'))
            inheritance_graph2 = (URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass'),
                                  RDFS.subClassOf,
                                  URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject'))
            data_g.add(inheritance_graph1)
            data_g.add(inheritance_graph2)

            # https://gist.github.com/ashleysommer/ee6e4ee48f15c4244cbc79963aae82a5
            # https://github.com/RDFLib/pySHACL/issues/148

            for s, p, o in data_g:
                print(f'{s} {p} {o}')

            r = validate(data_g,
                         shacl_graph=shacl,
                         allow_infos=True,
                         allow_warnings=True)
            conforms, results_graph, results_text = r
            print(results_text)
            self.assertFalse(conforms)
            data_g.remove(bad_boolean_graph)
            data_g.remove(inheritance_graph1)
            data_g.remove(inheritance_graph2)

        os.unlink(Path('generated_shacl.ttl'))

    def test_read_classes_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_classes_from_reader(reader)
        self.assertEqual(11, len(rows))

    def test_add_classes_to_graph(self):
        rows = [('All Cases TestClass', 'AllCasesTestClass',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass',
                 'Testclass containing all possible datatypes and combinations', '', 0, 'deprecated since OTL 2.3')]
        g = Graph()
        g = OTLShaclGenerator.add_classes_to_graph(g, rows)

        shape_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClassShape')

        self.assertTrue((shape_ref, RDF.type, SH.NodeShape) in g)
        self.assertTrue((shape_ref, SH.targetClass,
                         URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass')) in g)
        self.assertTrue((shape_ref, RDFS.label, Literal('All Cases TestClass')) in g)
        self.assertTrue((shape_ref, OWL.deprecated, Literal(True)) in g)

    def test_read_properties_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_properties_from_reader(reader)
        self.assertEqual(36, len(rows))

    def test_add_properties_to_graph_boolean(self):
        rows = [('testBooleanField', 'Test BooleanField', 'Test attribuut voor BooleanField',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '2',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testBooleanField',
                 'http://www.w3.org/2001/XMLSchema#boolean', 0, '', 0, '', 'deprecated since OTL 2.3',
                 'OSLODatatypePrimitive')]
        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, rows)

        class_ref = URIRef(rows[0][3] + 'Shape')
        shape_ref = URIRef(rows[0][6] + 'Shape')
        path_ref = URIRef(rows[0][6])

        self.assertTrue((class_ref, SH.property, shape_ref) in g)
        self.assertTrue((shape_ref, RDF.type, SH.PropertyShape) in g)
        self.assertTrue((shape_ref, SH.datatype, URIRef(rows[0][7])) in g)
        self.assertTrue((shape_ref, SH.path, path_ref) in g)
        self.assertTrue((shape_ref, SH.name, Literal('testBooleanField')) in g)
        self.assertTrue((shape_ref, RDFS.label, Literal('Test BooleanField')) in g)
        self.assertTrue((shape_ref, SH.nodeKind, SH.Literal) in g)
        self.assertTrue((shape_ref, SH.maxCount, Literal(2)) in g)
        self.assertTrue((shape_ref, OWL.deprecated, Literal(True)) in g)

    def test_read_inheritances_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_inheritances_from_reader(reader)
        self.assertEqual(10, len(rows))

    def test_add_inheritances_to_graph(self):
        rows = [('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMToestand',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject', '')]
        g = Graph()
        g = OTLShaclGenerator.add_inheritances_to_graph(g, rows)

        self.assertTrue((URIRef(rows[0][1]), RDFS.subClassOf, URIRef(rows[0][0])) in g)
