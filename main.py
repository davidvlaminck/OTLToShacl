import time
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL, Literal, SH, BNode, SKOS
from pyshacl import validate

from OTLShaclGenerator import OTLShaclGenerator


if __name__ == '__main__':
    subset_path = Path('OTL 2.13.db')
    shacl_path = Path('generated_shacl_otl_2.13.ttl')
    ont_path = Path('generated_ont_otl_2.13.ttl')
    shacl, ont = OTLShaclGenerator.generate_shacl_from_otl(subset_path=subset_path, shacl_path=shacl_path,
                                                           ont_path=ont_path)
