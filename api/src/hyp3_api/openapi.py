from pathlib import Path

import prance


def get_spec(path_to_spec: Path):
    parser = prance.ResolvingParser(str(path_to_spec.absolute()))
    parser.parse()
    return parser.specification
