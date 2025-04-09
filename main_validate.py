# resources:
# https://www.ida.liu.se/~robke04/SHACLTutorial/Introduction%20to%20SHACL.pdf
# https://shacl.org/playground/
# http://www.validatingrdf.com/
# https://15926.org/topics/SHACL/index.htm

import time
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

if __name__ == '__main__':
    # load the SHACL graphs
    g = Graph()
    g.parse(format='turtle', source=Path('generated_ont_otl_dyn_borden.ttl'))
    g.parse(format='turtle', source=Path('generated_shacl_otl_dyn_borden.ttl'))
    print(f'Loaded {len(g)} triples in SHACL graph')

    # load the data graph
    h = Graph()
    h.parse(format='json-ld', source=Path('assets_dyn_borden.jsonld'))
    print(f'Loaded {len(h)} triples in data graph')

    start = time.time()
    r = validate(h,
                 shacl_graph=g,
                 allow_infos=True,
                 allow_warnings=True)
    conforms, results_graph, results_text = r
    end = time.time()
    print(f'Validation done in {round(end - start, 2)} seconds')
    print(results_text)
