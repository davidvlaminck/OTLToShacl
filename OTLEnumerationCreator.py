import logging
from pathlib import Path
from typing import Dict
from urllib.request import urlretrieve
from zipfile import ZipFile

import rdflib
from otlmow_modelbuilder.AbstractDatatypeCreator import AbstractDatatypeCreator
from otlmow_modelbuilder.OSLOCollector import OSLOCollector
from rdflib import URIRef, Graph, RDF


class OTLEnumerationCreator(AbstractDatatypeCreator):
    default_environment = 'prd'
    graph_dict: Dict[str, Dict[str, Graph]] = {'prd': {}, 'tei': {}, 'dev': {}, 'aim': {}}
    oslo_github_branch_mapping = {
        'prd': 'master',
        'tei': 'test',
        'dev': 'dev',
        'aim': 'aim'
    }

    def __init__(self, oslo_collector: OSLOCollector, env: str = default_environment):
        super().__init__(oslo_collector)
        self.oslo_collector = oslo_collector
        self.env = env
        logging.info("Created an instance of OTLEnumerationCreator")

    def __enter__(self):
        self.path_zip_file = Path(__file__).parent / "all.ttl.zip"
        self.path_ttl_file = Path(__file__).parent / "all.ttl"
        if self.env != 'unittest':
            self.graph_dict[self.env] = self.download_unzip_and_parse_to_dict(env=self.env)
            logging.info("Downloaded, unzipped and parsed the enumerations ttl file")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path_zip_file.exists():
            self.path_zip_file.unlink()
        if self.path_ttl_file.exists():
            self.path_ttl_file.unlink()

    def download_unzip_and_parse_to_dict(self, env: str = default_environment) -> Dict[str, Graph]:
        directory_to_extract_to = self.path_zip_file.parent
        urlretrieve(f"https://github.com/Informatievlaanderen/OSLO-codelistgenerated/raw/refs/heads/wegenenverkeer-{self.oslo_github_branch_mapping[env]}/all.ttl.zip", self.path_zip_file)
        with ZipFile(self.path_zip_file) as zip_ref:
            zip_ref.extractall(directory_to_extract_to)

        return self.parse_graph_to_dict(path_ttl_file=self.path_ttl_file)

    @classmethod
    def get_graph(cls, keuzelijstnaam: str, env: str = default_environment):
        uri = f'https://wegenenverkeer.data.vlaanderen.be/id/conceptscheme/{keuzelijstnaam}'
        keuzelijst_graph = OTLEnumerationCreator.graph_dict[env].get(uri)
        if keuzelijst_graph is None:
            test_uri = uri.replace('wegenenverkeer', 'wegenenverkeer-test')
            keuzelijst_graph = OTLEnumerationCreator.graph_dict[env].get(test_uri)
        if keuzelijst_graph is not None:
            return keuzelijst_graph
        raise ValueError(f"Graph for {keuzelijstnaam} not found in the graph_dict")

    @staticmethod
    def parse_graph_to_dict(path_ttl_file: Path) -> Dict[str, Graph]:
        g = rdflib.Graph()
        g.parse(path_ttl_file, format="turtle")

        keuzelijst_dict = {}
        keuzelijst_uris = set(g.subjects(predicate=RDF.type, object=URIRef('http://www.w3.org/2004/02/skos/core#ConceptScheme')))

        for keuzelijst_uri in keuzelijst_uris:
            keuzelijst_graph = Graph()
            for triple in g.triples((keuzelijst_uri, None, None)):
                keuzelijst_graph.add(triple)

            keuzelijst_waarde_uris = g.subjects(predicate=URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
                                                object=keuzelijst_uri)
            for keuzelijst_waarde_uri in keuzelijst_waarde_uris:
                for triple in g.triples((keuzelijst_waarde_uri, None, None)):
                    keuzelijst_graph.add(triple)

            keuzelijst_dict[str(keuzelijst_uri)] = keuzelijst_graph
        rdflib.term.URIRef('https://wegenenverkeer.data.vlaanderen.be/id/conceptscheme/KlTestKeuzelijst')
        return keuzelijst_dict
