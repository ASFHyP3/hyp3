from pathlib import Path

import prance


def get_spec_yaml(path_to_spec: Path):
    parser = prance.ResolvingParser(str(path_to_spec.resolve()))
    parser.parse()
    return parser.specification
