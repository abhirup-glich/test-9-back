from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
import logging
import os
import sys

try:
    from .config import Config
    from .routes import blp as AttendanceBlueprint
except ImportError:
    from config import Config
    from routes import blp as AttendanceBlueprint

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
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        app.logger.error(f"Configuration Error: {e}")

    setup_logging(app)
    app.logger.info("Starting Attendance Service API...")

    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config["API_TITLE"] = "Attendance Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    
    api = Api(app)
    
    api.register_blueprint(AttendanceBlueprint)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
