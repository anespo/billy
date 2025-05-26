"""
Configurazione dell'applicazione EnergyWise
"""
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

class Config:
    """Configurazione base dell'applicazione"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'chiave-segreta-predefinita')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Configurazione AWS
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
    BEDROCK_EMBEDDING_MODEL_ID = os.getenv('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
    
    # Configurazione del chatbot
    CHATBOT_ENABLED = True
    CHATBOT_FALLBACK_ENABLED = True
