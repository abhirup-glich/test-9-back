from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
import sys

try:
    from .config import Config
    from .routes import blp as AuthBlueprint
except ImportError:
    from config import Config
    from routes import blp as AuthBlueprint

def setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    setup_logging(app)
    app.logger.info("Starting Auth Service API...")

    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config["API_TITLE"] = "Auth Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    
    jwt = JWTManager(app)
    api = Api(app)
    
    api.register_blueprint(AuthBlueprint)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
