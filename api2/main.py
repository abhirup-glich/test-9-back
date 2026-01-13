from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
import logging
import sys
print("Starting main.py...", flush=True)

try:
    from .config import Config
    from .routes import blp as AuthBlueprint
    from .face_routes import blp as FaceBlueprint
except ImportError:
    from config import Config
    from routes import blp as AuthBlueprint
    from face_routes import blp as FaceBlueprint

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
    app.logger.info("Starting Auth Service API...")

    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config["API_TITLE"] = "Auth Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    
    api = Api(app)
    
    api.register_blueprint(AuthBlueprint)
    api.register_blueprint(FaceBlueprint)
    
    return app

app = create_app()

if __name__ == '__main__':
    print("About to run app...", flush=True)
    try:
        try:
            from .logic import connect_db, setup_db
        except ImportError:
            from logic import connect_db, setup_db
            
        print("Connecting to database...")
        conn, cur = connect_db()
        print("Setting up database...")
        setup_db(cur)
        conn.close()
    except Exception as e:
        print(f"Error during DB setup: {e}")

    app.run(host='0.0.0.0', port=5002)
