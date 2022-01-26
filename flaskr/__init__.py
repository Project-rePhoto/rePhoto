import os

from flask import Flask
#Google Maps API
from flask_googlemaps import GoogleMaps
#import Geocoder
#from flask_simple_geoip import SimpleGeoIP
from .config import map_key, username, password, database, host

#simple_geoip = '';

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    #Initialize Maps extension
    GoogleMaps(app, key=map_key)

    #Initialize SimpleGeoIP extension
    #app.config["GEOIPIFY_API_KEY"] = geo_key

    #global simple_geoip
    #simple_geoip = SimpleGeoIP(app)

    #Add Google Cloud credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/liuchao/key.json'

    #Configure upload folder path
    UPLOAD_FOLDER = '/home/liuchao/rePhoto/flaskr/static/myImgs'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    #MySQL connection
    app.config['MYSQL_DATABASE_USER'] = username
    app.config['MYSQL_DATABASE_PASSWORD'] = password
    app.config['MYSQL_DATABASE_DB'] = database
    app.config['MYSQL_DATABASE_HOST'] = host

    app.config.from_mapping(
        SECRET_KEY='dev',
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