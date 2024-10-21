import render_cf

def test_parse_job_step_map():
    assert render_cf.parse_job_step_map('for item in items') == ('item', 'items')
    assert render_cf.parse_job_step_map('for foo in bar') == ('foo', 'bar')
