from pathlib import Path

from openapi_core.spec.shortcuts import create_spec
import prance


def get_spec(path_to_spec: Path):
    parser = prance.ResolvingParser(str(path_to_spec.resolve()))
    parser.parse()
    return create_spec(parser.specification)
