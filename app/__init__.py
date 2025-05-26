from flask import Flask
import os
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Crea la directory di upload se non esiste
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER']), exist_ok=True)
    
    # Registra i blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
