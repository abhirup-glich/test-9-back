from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
try:
    from .config import Config
    from .routes import blp as AdminBlueprint
except ImportError:
    from config import Config
    from routes import blp as AdminBlueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config["API_TITLE"] = "Admin Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    
    jwt = JWTManager(app)
    api = Api(app)
    
    api.register_blueprint(AdminBlueprint)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
