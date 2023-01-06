import os
from pathlib import Path
from unittest import TestCase

from OTLShaclGenerator import OTLShaclGenerator
from SQLDbReader import SQLDbReader

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS, XSD
from pyshacl import validate


class OTLShaclGeneratorTests(TestCase):
    def test_create_without_subset(self):
        with self.assertRaises(FileNotFoundError):
            OTLShaclGenerator.generate_shacl_from_otl(Path(''), shacl_path=Path(), ont_path=Path())

    def test_generate_subset_and_test_data(self):
        shacl, ont = OTLShaclGenerator.generate_shacl_from_otl(subset_path=Path('OTL_AllCasesTestClass.db'),
                                                               shacl_path=Path('generated_shacl.ttl'),
                                                               ont_path=Path('generated_ont.ttl'))
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

            # https://gist.github.com/ashleysommer/ee6e4ee48f15c4244cbc79963aae82a5
            # https://github.com/RDFLib/pySHACL/issues/148

            # for s, p, o in data_g:
            #     print(f'{s} {p} {o}')

            r = validate(data_g,
                         shacl_graph=shacl,
                         ont_graph=ont,
                         allow_infos=True,
                         allow_warnings=True)
            conforms, results_graph, results_text = r
            print(results_text)
            self.assertFalse(conforms)
            data_g.remove(bad_boolean_graph)

        os.unlink(Path('generated_shacl.ttl'))
        os.unlink(Path('generated_ont.ttl'))

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

    def test_add_owl_classes_to_graph(self):
        rows = [('All Cases TestClass', 'AllCasesTestClass',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass',
                 'Testclass containing all possible datatypes and combinations', '', 0, 'deprecated since OTL 2.3')]
        g = Graph()
        g = OTLShaclGenerator.add_owl_classes_to_graph(g, rows)

        self.assertTrue((URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass'), RDF.type,
                         OWL.Class) in g)

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

    def test_add_properties_to_graph_complex(self):
        rows = [('testComplexType', 'Test ComplexType', 'Test attribuut voor een complexe waarde',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '1',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testComplexType',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType', 0, '', 0, '',
                 '', 'OSLODatatypeComplex')]
        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, rows)

        shape_ref = URIRef(rows[0][6] + 'Shape')

        self.assertTrue((shape_ref, RDFS.comment, URIRef(rows[0][7])) in g)
        self.assertTrue((shape_ref, SH.nodeKind, SH.BlankNode) in g)

    def test_add_properties_to_graph_enum(self):
        rows = [('testKeuzelijst', 'Test Keuzelijst', 'Test attribuut voor een keuzelijst',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '1',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKeuzelijst',
                 'https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#KlTestKeuzelijst', 0, '', 0, '', '',
                 'OSLOEnumeration')]
        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, rows)

        shape_ref = URIRef(rows[0][6] + 'Shape')

        self.assertTrue((shape_ref, RDFS.comment, URIRef(rows[0][7])) in g)
        self.assertTrue((shape_ref, SH.nodeKind, SH.IRI) in g)

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

    def test_read_complex_attributes_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_complex_attributes_from_reader(reader)
        self.assertEqual(11, len(rows))

    def test_add_complex_attributes_to_graph_functionality(self):
        property_rows = [('assetId', 'asset-id',
                          'Unieke identificatie van de asset zoals toegekend door de assetbeheerder of n.a.v. eerste aanlevering door de leverancier.',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject', '1', '1',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject.assetId',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator', 0, '',
                          0, '', '', 'OSLODatatypeComplex'),
                         ('assetId', 'asset-id',
                          'Unieke identificatie van de asset zoals toegekend door de assetbeheerder of n.a.v. eerste aanlevering door de leverancier.',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#RelatieObject', '1', '1',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#RelatieObject.assetId',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator', 0, '',
                          0, '', '', 'OSLODatatypeComplex')]
        attribute_rows = [('DtcIdentificator',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator',
                           'Identificator',
                           '', 'identificator', 'identificator',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator', '1',
                           '2',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.identificator',
                           'http://www.w3.org/2001/XMLSchema#string', 'deprecated since OTL 2.3',
                           'OSLODatatypePrimitive'),
                          ('DtcIdentificator',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator',
                           'Identificator',
                           '', 'toegekendDoor', 'toegekend door',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator', '1',
                           '1',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.toegekendDoor',
                           'http://www.w3.org/2001/XMLSchema#string', '', 'OSLODatatypePrimitive')]

        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, property_rows)
        g = OTLShaclGenerator.add_complex_attributes_to_graph(g, attribute_rows)

        aimObject_assetId_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#AIMObject.assetIdShape')
        relatieObject_assetId_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#RelatieObject.assetIdShape')
        dtc_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator')
        identificator_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.identificatorShape')
        toegekend_door_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.toegekendDoorShape')

        self.assertTrue((aimObject_assetId_ref, RDFS.comment, dtc_ref) in g)
        self.assertTrue((relatieObject_assetId_ref, RDFS.comment, dtc_ref) in g)

        self.assertTrue((aimObject_assetId_ref, SH.property, identificator_ref) in g)
        self.assertTrue((relatieObject_assetId_ref, SH.property, identificator_ref) in g)
        self.assertTrue((aimObject_assetId_ref, SH.property, toegekend_door_ref) in g)
        self.assertTrue((relatieObject_assetId_ref, SH.property, toegekend_door_ref) in g)

        self.assertTrue((identificator_ref, RDF.type, SH.PropertyShape) in g)
        self.assertTrue((identificator_ref, SH.datatype, URIRef(attribute_rows[0][10])) in g)
        self.assertTrue((identificator_ref, SH.path, URIRef(attribute_rows[0][9])) in g)
        self.assertTrue((identificator_ref, SH.name, Literal('identificator')) in g)
        self.assertTrue((identificator_ref, RDFS.label, Literal('identificator')) in g)
        self.assertTrue((identificator_ref, SH.nodeKind, SH.Literal) in g)
        self.assertTrue((identificator_ref, SH.maxCount, Literal(2)) in g)
        self.assertTrue((identificator_ref, OWL.deprecated, Literal(True)) in g)

    def test_add_complex_attributes_to_graph_nested_complex(self):
        property_rows = [('testComplexType', 'Test ComplexType', 'Test attribuut voor een complexe waarde',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '1',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testComplexType',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType', 0, '',
                          0, '', '', 'OSLODatatypeComplex')]
        attribute_rows = [('DtcTestComplexType2',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2',
                           'Test ComplexType2', '', 'testStringField', 'Test tekstveld',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2', '1',
                           '1',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2.testStringField',
                           'http://www.w3.org/2001/XMLSchema#string', '', '', 'OSLODatatypePrimitive'),
                          ('DtcTestComplexType',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType',
                           'Test ComplexType', '', 'testComplexType2', 'Test complexe waarde',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType', '1',
                           '1',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType.testComplexType2',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2', '', '',
                           'OSLODatatypeComplex')]

        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, property_rows)
        g = OTLShaclGenerator.add_complex_attributes_to_graph(g, attribute_rows)

        class_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClassShape')

        dtc_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType')
        dtc_ref2 = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2')
        attribute_c1_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testComplexTypeShape')
        attribute_c2_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType.testComplexType2Shape')
        attribute_c2_str_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcTestComplexType2.testStringFieldShape')

        self.assertTrue((attribute_c1_ref, RDFS.comment, dtc_ref) in g)
        self.assertTrue((attribute_c2_ref, RDFS.comment, dtc_ref2) in g)
        self.assertTrue((attribute_c2_str_ref, SH.datatype, XSD.string) in g)

        self.assertTrue((class_ref, SH.property, attribute_c1_ref) in g)
        self.assertTrue((attribute_c1_ref, SH.property, attribute_c2_ref) in g)
        self.assertTrue((attribute_c2_ref, SH.property, attribute_c2_str_ref) in g)

        self.assertTrue((attribute_c1_ref, SH.nodeKind, SH.BlankNode) in g)
        self.assertTrue((attribute_c2_ref, SH.nodeKind, SH.BlankNode) in g)
        self.assertTrue((attribute_c2_str_ref, SH.nodeKind, SH.Literal) in g)

    def test_read_enums_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_enums_from_reader(reader)
        self.assertEqual(2, len(rows))

    def test_add_enums_to_graph(self):
        property_rows = [
            ('testKeuzelijst', 'Test Keuzelijst', 'Test attribuut voor een keuzelijst',
             'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '1',
             'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKeuzelijst',
             'https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#KlTestKeuzelijst', 0, '', 0, '', '',
             'OSLOEnumeration'),
            ('testKeuzelijstMetKard', 'Test Keuzelijst Met Kard',
             'Test attribuut voor een keuzelijst met kardinaliteit > 1',
             'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '*',
             'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKeuzelijstMetKard',
             'https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#KlTestKeuzelijst', 0, '', 0, '', '',
             'OSLOEnumeration')]
        enum_rows = [('KlTestKeuzelijst', 'https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#KlTestKeuzelijst',
                      'Test keuzelijst',
                      'https://wegenenverkeer.data.vlaanderen.be/id/conceptscheme/KlTestKeuzelijst', '')]
        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, property_rows)
        g = OTLShaclGenerator.add_enums_to_graph(g, enum_rows)

        shape_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKeuzelijstShape')
        shape_ref_2 = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKeuzelijstMetKardShape')

        self.assertTrue((shape_ref, RDFS.comment, URIRef(enum_rows[0][1])) in g)
        self.assertTrue((shape_ref, SH.nodeKind, SH.IRI) in g)

        enum_list_node = g.value(subject=shape_ref, predicate=URIRef('http://www.w3.org/ns/shacl#in'))
        self.assertIsNotNone(enum_list_node)
        first_elem_node = g.value(subject=enum_list_node, predicate=RDF.first)
        self.assertEqual(URIRef('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlTestKeuzelijst/waarde-1'),
                         first_elem_node)

        self.assertTrue((shape_ref_2, RDFS.comment, URIRef(enum_rows[0][1])) in g)
        enum_list_node_2 = g.value(subject=shape_ref_2, predicate=URIRef('http://www.w3.org/ns/shacl#in'))
        self.assertIsNotNone(enum_list_node_2)
        first_elem_node_2 = g.value(subject=enum_list_node_2, predicate=RDF.first)
        self.assertEqual(URIRef('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlTestKeuzelijst/waarde-1'),
                         first_elem_node_2)

    def test_read_primitive_attributes_from_reader(self):
        reader = SQLDbReader(Path('OTL_AllCasesTestClass.db'))
        rows = OTLShaclGenerator.read_primitive_attributes_from_reader(reader)
        self.assertEqual(17, len(rows))

    def test_add_primitive_attributes_to_graph(self):
        property_rows = [('testKwantWrd', 'Test KwantWrd', 'Test attribuut voor een kwantitatieve waarde',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass', '1', '1',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKwantWrd',
                          'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest', 0, '', 0,
                          '', '', 'OSLODatatypePrimitive')]
        attribute_rows = [('KwantWrdTest',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest',
                           'Kwantitatieve test waarde', '', 'standaardEenheid', 'standaard eenheid',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest', '1', '1',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest.standaardEenheid',
                           'http://www.w3.org/2000/01/rdf-schema#Literal', '', '"%"^^cdt:ucumunit',
                           'OSLODatatypePrimitive'),
                          ('KwantWrdTest',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest',
                           'Kwantitatieve test waarde', '', 'waarde', 'waarde',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest',
                           '1', '1',
                           'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest.waarde',
                           'http://www.w3.org/2001/XMLSchema#decimal', '', '',
                           'OSLODatatypePrimitive')
                          ]

        g = Graph()
        g = OTLShaclGenerator.add_properties_to_graph(g, property_rows)
        g = OTLShaclGenerator.add_primitive_attributes_to_graph(g, attribute_rows)

        class_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClassShape')

        kwant_wrd_type_ref = URIRef('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest')
        kwant_wrd_attr_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AllCasesTestClass.testKwantWrdShape')

        standaard_eenheid_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest.standaardEenheidShape')
        waarde_ref = URIRef(
            'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#KwantWrdTest.waardeShape')

        self.assertTrue((class_ref, SH.property, kwant_wrd_attr_ref) in g)
        self.assertTrue((kwant_wrd_attr_ref, RDFS.comment, kwant_wrd_type_ref) in g)

        self.assertTrue((kwant_wrd_attr_ref, SH.nodeKind, SH.BlankNode) in g)

        self.assertTrue((kwant_wrd_attr_ref, SH.property, standaard_eenheid_ref) in g)
        self.assertTrue((kwant_wrd_attr_ref, SH.property, waarde_ref) in g)

        self.assertTrue((standaard_eenheid_ref, SH.nodeKind, SH.Literal) in g)
        self.assertTrue((standaard_eenheid_ref, SH.datatype, RDFS.Literal) in g)
        self.assertTrue((standaard_eenheid_ref, SH.equals, Literal('%')) in g)

        self.assertTrue((waarde_ref, SH.nodeKind, SH.Literal) in g)
        self.assertTrue((waarde_ref, SH.datatype, XSD.decimal) in g)
