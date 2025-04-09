from pathlib import Path
from OTLShaclGenerator import OTLShaclGenerator


if __name__ == '__main__':
    subset_path = Path('OTL_Dynamische_borden.db')
    shacl_path = Path('generated_shacl_otl_dyn_borden.ttl')
    ont_path = Path('generated_ont_otl_dyn_borden.ttl')
    shacl, ont = OTLShaclGenerator.generate_shacl_from_otl(subset_path=subset_path, shacl_path=shacl_path,
                                                           ont_path=ont_path)
