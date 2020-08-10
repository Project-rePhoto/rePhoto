import os

from flask import Flask, jsonify
#Google Maps API
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
#import Geocoder
from flask_simple_geoip import SimpleGeoIP

simple_geoip = '';

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    #Google Maps API KEY
    map_key = 'AIzaSyD9Fjwz6Qp1UzoKbPfjz1Q1lumfGUA1kyo'
    #Initialize Google Maps extension
    GoogleMaps(app, key=map_key)

    #geoip API key
    geo_key = 'at_ZWBYLzwBQx7uClQFX6IOlqLPPbsDm'
    #Initialize SimpleGeoIP extension
    app.config["GEOIPIFY_API_KEY"] = geo_key

    global simple_geoip
    simple_geoip = SimpleGeoIP(app)

    #Configure upload folder path
    UPLOAD_FOLDER = '/home/chliu/flask_rephoto/flaskr/static'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app