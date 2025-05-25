from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Assicurati che la cartella uploads esista
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER']), exist_ok=True)
    
    # Importa e registra le routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
