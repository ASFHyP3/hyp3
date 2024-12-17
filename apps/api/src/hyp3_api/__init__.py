from flask import Flask


app = Flask(__name__, template_folder='ui/swagger/', static_folder='ui/swagger/', static_url_path='/ui/')
CMR_URL = 'https://cmr.earthdata.nasa.gov/search/granules.json'

from hyp3_api import routes  # noqa Has to be at end of file or will cause circular import

__all__ = [
    'app',
    'CMR_URL',
    'routes',
]
