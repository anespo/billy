from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from app.services.document_processor import process_document
from app.services.strands_agent import analyze_bill, compare_with_previous

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.warning("Nessun file nella richiesta")
        return jsonify({'error': 'Nessun file nella richiesta'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        logger.warning("Nessun file selezionato")
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    if file and allowed_file(file.filename):
        # Genera un nome file sicuro con UUID per evitare conflitti
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Crea la directory di upload se non esiste
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), current_app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_folder, exist_ok=True)
        
        # Salva il file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        file.save(full_path)
        
        logger.info(f"File salvato: {full_path}")
        
        # Processa il documento
        extracted_text = process_document(full_path)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            logger.warning(f"Testo insufficiente estratto dal file: {unique_filename}")
            return jsonify({
                'error': 'Impossibile estrarre testo sufficiente dal documento. Assicurati che il documento sia leggibile.',
                'extracted_text': extracted_text
            }), 400
        
        # Analizza la bolletta
        logger.info(f"Analisi della bolletta in corso: {unique_filename}")
        analysis_result = analyze_bill(extracted_text)
        
        if "error" in analysis_result:
            logger.error(f"Errore nell'analisi: {analysis_result['error']}")
            return jsonify({
                'error': analysis_result['error'],
                'filename': unique_filename
            }), 400
        
        logger.info(f"Analisi completata con successo: {unique_filename}")
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'analysis': analysis_result
        })
    
    logger.warning(f"Tipo di file non consentito: {file.filename}")
    return jsonify({'error': 'Tipo di file non consentito'}), 400

@main_bp.route('/compare', methods=['POST'])
def compare_bills():
    data = request.json
    
    if not data or 'current_bill' not in data:
        logger.warning("Dati della bolletta corrente mancanti")
        return jsonify({'error': 'Dati della bolletta corrente mancanti'}), 400
    
    previous_bill = data.get('previous_bill', None)
    
    if not previous_bill:
        logger.warning("Nessuna bolletta precedente fornita per il confronto")
        return jsonify({
            'message': 'Nessuna bolletta precedente disponibile per il confronto',
            'comparison': None
        })
    
    logger.info("Confronto tra bollette in corso")
    comparison_result = compare_with_previous(data['current_bill'], previous_bill)
    
    if "error" in comparison_result:
        logger.error(f"Errore nel confronto: {comparison_result['error']}")
        return jsonify({
            'error': comparison_result['error']
        }), 400
    
    logger.info("Confronto completato con successo")
    return jsonify({
        'success': True,
        'comparison': comparison_result
    })
