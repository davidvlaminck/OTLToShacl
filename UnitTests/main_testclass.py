import time
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate

from OTLShaclGenerator import OTLShaclGenerator


if __name__ == '__main__':
    subset_path = Path('OTL_AllCasesTestClass.db')
    shacl_path = Path('generated_shacl.ttl')
    ont_path = Path('generated_ont.ttl')
    shacl, ont = OTLShaclGenerator.generate_shacl_from_otl(subset_path=subset_path, shacl_path=shacl_path,
                                                           ont_path=ont_path)

    print(shacl.serialize(format='turtle'))
    print(ont.serialize(format='turtle'))

    h = Graph()
    start = time.time()
    h.parse('testclass.ttl')
    end = time.time()
    print(f'Loaded {len(h)} objects in {round(end - start, 2)} seconds')

    for s, p, o in shacl:
        print(f'{s} {p} {o}')

    start = time.time()
    r = validate(h,
                 shacl_graph=shacl,
                 ont_graph=ont,
                 allow_infos=True,
                 allow_warnings=True)
    conforms, results_graph, results_text = r
    end = time.time()
    print(f'Validation done in {round(end - start, 2)} seconds')
    print(results_text)
