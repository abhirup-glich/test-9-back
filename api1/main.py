from flask import Flask, request, jsonify
from flask_smorest import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
import logging
import sys

try:
    from .config import Config
    from .routes import blp as AdminBlueprint
    from .error_manager import error_manager
except ImportError:
    from config import Config
    from routes import blp as AdminBlueprint
    from error_manager import error_manager

def setup_logging(app):
    # We will let ErrorManager handle the structured error logging, 
    # but we still want general app logs.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)

from datetime import datetime

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        context = {"url": request.url, "method": request.method, "remote_addr": request.remote_addr}
        unique_code, _ = error_manager.log_error(
            base_code=e.code,
            message=e.description,
            exception=e,
            context=context
        )
        response = {
            "code": e.code,
            "error_code": unique_code,
            "message": e.description,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "status": "error"
        }
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        context = {"url": request.url, "method": request.method, "remote_addr": request.remote_addr}
        unique_code, _ = error_manager.log_error(
            base_code=500,
            message=str(e),
            exception=e,
            context=context
        )
        response = {
            "code": 500,
            "error_code": unique_code,
            "message": "Internal Server Error",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "status": "error"
        }
        return jsonify(response), 500

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure error manager
    error_manager.configure(app.config)
    
    setup_logging(app)
    app.logger.info("Starting Admin Service API...")

    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config["API_TITLE"] = "Admin Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    
    jwt = JWTManager(app)
    api = Api(app)
    
    api.register_blueprint(AdminBlueprint)
    
    register_error_handlers(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
