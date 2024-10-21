import pytest

import render_cf

def test_parse_map_statement():
    assert render_cf.parse_map_statement('for item in items') == ('item', 'items')
    assert render_cf.parse_map_statement('for foo in bar') == ('foo', 'bar')

    with pytest.raises(ValueError, match='expected 4 tokens in map statement but got 3: item in items'):
        render_cf.parse_map_statement('item in items')

    with pytest.raises(ValueError, match='expected 4 tokens in map statement but got 5: for for item in items'):
        render_cf.parse_map_statement('for for item in items')

    with pytest.raises(ValueError, match="expected 'for', got 'fr': fr item in items"):
        render_cf.parse_map_statement('fr item in items')

    with pytest.raises(ValueError, match="expected 'in', got 'ib': for item ib items"):
        render_cf.parse_map_statement('for item ib items')
