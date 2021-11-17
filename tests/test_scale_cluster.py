from datetime import date
import scale_cluster

def test_get_time_period():
    result = scale_cluster.get_time_period(date(year=2020, month=1, day=1))
    assert result == {'Start': '2020-01-01', 'End': '2020-02-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=12, day=31))
    assert result == {'Start': '2020-12-01', 'End': '2021-01-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=12, day=1))
    assert result == {'Start': '2020-12-01', 'End': '2021-01-01'}

    result = scale_cluster.get_time_period(date(year=2020, month=2, day=29))
    assert result == {'Start': '2020-02-01', 'End': '2020-03-01'}
