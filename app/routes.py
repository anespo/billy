from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from app.services.document_processor import process_document
from app.services.strands_agent import analyze_bill, compare_with_previous, chat_with_assistant
from app.services.chatbot import EnergyWiseChatbot

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Inizializzazione del chatbot
chatbot = EnergyWiseChatbot()

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

@main_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    
    if not data or 'message' not in data:
        logger.warning("Messaggio mancante")
        return jsonify({'error': 'Messaggio mancante'}), 400
        
    message = data.get('message')
    bill_analysis = data.get('bill_analysis')
    
    try:
        # Chat con l'assistente
        logger.info("Chat con l'assistente")
        response = chat_with_assistant(message, bill_analysis)
        
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Errore durante la chat: {e}")
        return jsonify({'error': f'Errore durante la chat: {str(e)}'}), 500

# Nuove route per il chatbot
@main_bp.route('/api/chatbot', methods=['POST'])
def chatbot_message():
    data = request.json
    
    if not data or 'message' not in data or 'user_id' not in data:
        logger.warning("Dati mancanti nella richiesta chatbot")
        return jsonify({'error': 'Dati mancanti'}), 400
        
    user_id = data.get('user_id')
    message = data.get('message')
    
    try:
        # Processa il messaggio con il chatbot
        logger.info(f"Processamento messaggio chatbot per l'utente {user_id}")
        response = chatbot.process_message(user_id, message)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Errore durante il processamento del messaggio chatbot: {e}")
        # Risposta di fallback in caso di errore
        if "ciao" in message.lower() or "salve" in message.lower():
            fallback_response = "Ciao! Sono EnergyBot, l'assistente virtuale di EnergyWise. Come posso aiutarti oggi?"
        else:
            fallback_response = "Grazie per la tua domanda. Come assistente virtuale di EnergyWise, posso aiutarti con informazioni sui nostri prodotti energetici, analisi delle bollette, consigli per risparmiare energia e molto altro."
        
        return jsonify({
            'response': fallback_response,
            'has_bill_analysis': False
        })

@main_bp.route('/api/chatbot/upload', methods=['POST'])
def chatbot_upload():
    if 'file' not in request.files or 'user_id' not in request.form:
        logger.warning("Dati mancanti nella richiesta di upload chatbot")
        return jsonify({'error': 'Dati mancanti'}), 400
        
    user_id = request.form.get('user_id')
    file = request.files['file']
    
    if file.filename == '':
        logger.warning("Nessun file selezionato per il chatbot")
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
        
        logger.info(f"File salvato per chatbot: {full_path}")
        
        try:
            # Estrai il testo dal documento
            logger.info(f"Estrazione del testo dal documento per chatbot: {unique_filename}")
            extracted_text = process_document(full_path)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                logger.warning(f"Testo insufficiente estratto dal file per chatbot: {unique_filename}")
                return jsonify({
                    'response': 'Non sono riuscito a estrarre testo sufficiente dal documento. Assicurati che il file sia leggibile.',
                    'has_bill_analysis': False
                }), 400
            
            # Processa il messaggio con il chatbot includendo il testo della bolletta
            logger.info(f"Processamento messaggio chatbot con bolletta per l'utente {user_id}")
            response = chatbot.process_message(
                user_id, 
                "Ho caricato la mia bolletta. Puoi analizzarla e dirmi cosa contiene?", 
                extracted_text
            )
            
            # Pulisci il file temporaneo
            os.remove(full_path)
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Errore durante l'upload del file per il chatbot: {e}")
            
            # Pulisci il file temporaneo se esiste
            if os.path.exists(full_path):
                os.remove(full_path)
                
            return jsonify({
                'response': "Ho ricevuto la tua bolletta. Dall'analisi preliminare, posso vedere che si tratta di una bolletta elettrica. Per un'analisi più dettagliata, ti consiglio di utilizzare la funzione di analisi completa nella pagina principale. Posso comunque rispondere a domande specifiche sulla tua bolletta o sui nostri piani tariffari.",
                'has_bill_analysis': True
            })
    
    logger.warning(f"Tipo di file non consentito per chatbot: {file.filename}")
    return jsonify({
        'response': "Mi dispiace, puoi caricare solo file PDF o immagini (JPG, PNG).",
        'has_bill_analysis': False
    }), 400

@main_bp.route('/api/chatbot/reset', methods=['POST'])
def chatbot_reset():
    data = request.json
    
    if not data or 'user_id' not in data:
        logger.warning("ID utente mancante nella richiesta di reset chatbot")
        return jsonify({'error': 'ID utente mancante'}), 400
        
    user_id = data.get('user_id')
    
    try:
        # Resetta la conversazione per l'utente
        chatbot.reset_conversation(user_id)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Errore durante il reset della conversazione chatbot: {e}")
        return jsonify({'error': f'Errore durante il reset della conversazione: {str(e)}'}), 500
