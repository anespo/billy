import boto3
from botocore.config import Config
import json
import os
import logging
from dotenv import load_dotenv

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Configurazione AWS Bedrock
region = os.getenv('AWS_REGION', 'us-east-1')
model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=region,
    config=Config(
        read_timeout=120,  # Aumentato timeout a 120 secondi
        connect_timeout=60,
        retries={'max_attempts': 3}  # Aggiunto retry automatico
    )
)

def analyze_bill(bill_text):
    """
    Analizza il testo di una bolletta elettrica utilizzando Claude 3.5 Sonnet
    
    Args:
        bill_text: Testo estratto dalla bolletta
        
    Returns:
        dict: Risultato dell'analisi
    """
    if not bill_text or len(bill_text.strip()) < 50:
        return {
            "error": "Il testo estratto dalla bolletta è insufficiente per l'analisi. Assicurati che il documento sia leggibile."
        }
    
    prompt = f"""
    Sei un assistente specializzato nell'analisi delle bollette elettriche spagnole. Analizza attentamente la seguente bolletta elettrica ed estrai SOLO i dati reali presenti nel testo. Non inventare o simulare dati non presenti.

    1. Estrai i dati principali (periodo di fatturazione, importo totale, consumi in kWh)
    2. Identifica le voci di costo specifiche presenti nella bolletta
    3. Identifica eventuali anomalie o incongruenze nei consumi o nei costi
    4. Fornisci consigli pratici basati ESCLUSIVAMENTE sui dati reali estratti

    Se alcuni dati non sono presenti o non possono essere estratti con certezza, indica chiaramente "Dato non disponibile" invece di inventare informazioni.

    Ecco il testo della bolletta:
    {bill_text}

    Rispondi in formato JSON con i seguenti campi:
    - summary: riepilogo dei dati principali effettivamente trovati
    - cost_breakdown: spiegazione delle voci di costo identificate nel testo
    - saving_tips: consigli per risparmiare basati sui dati reali
    - anomalies: eventuali anomalie rilevate nei dati
    - raw_data: dati strutturati estratti (periodo, importo, consumi, etc.)
    """
    
    try:
        logger.info("Invio richiesta a Bedrock per analisi bolletta")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        result = response_body.get('content')[0].get('text')
        logger.info("Risposta ricevuta da Bedrock")
        
        # Estrai il JSON dalla risposta
        try:
            # Cerca di estrarre il JSON dalla risposta
            if '```json' in result:
                json_str = result.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(result)
        except json.JSONDecodeError:
            logger.error("Impossibile analizzare la risposta come JSON")
            # Se non riesce a decodificare il JSON, restituisci la risposta come testo
            return {
                "error": "Impossibile analizzare la risposta come JSON", 
                "raw_response": result,
                "summary": "Errore nell'elaborazione della risposta. Controlla il testo estratto."
            }
            
    except Exception as e:
        logger.error(f"Errore durante l'analisi della bolletta: {e}")
        return {"error": str(e)}

def compare_with_previous(current_bill, previous_bill=None):
    """
    Confronta la bolletta corrente con una precedente
    
    Args:
        current_bill: Dati della bolletta corrente
        previous_bill: Dati della bolletta precedente (opzionale)
        
    Returns:
        dict: Risultato del confronto
    """
    if not previous_bill:
        return {
            "message": "Nessuna bolletta precedente disponibile per il confronto",
            "comparison": None
        }
    
    prompt = f"""
    Sei un assistente specializzato nell'analisi delle bollette elettriche spagnole. Confronta la bolletta corrente con quella precedente e identifica SOLO differenze reali basate sui dati forniti. Non inventare o simulare dati non presenti.

    1. Identifica differenze nei consumi (kWh) se presenti in entrambe le bollette
    2. Identifica differenze nei costi se presenti in entrambe le bollette
    3. Identifica possibili errori o anomalie basati ESCLUSIVAMENTE sui dati forniti
    4. Suggerisci motivi plausibili per eventuali aumenti o diminuzioni
    5. Fornisci suggerimenti per contestare eventuali errori al call center SOLO se ci sono anomalie evidenti

    Se alcuni dati non sono presenti o non possono essere confrontati con certezza, indica chiaramente "Confronto non disponibile" invece di inventare informazioni.

    Bolletta corrente:
    {json.dumps(current_bill, indent=2)}

    Bolletta precedente:
    {json.dumps(previous_bill, indent=2)}

    Rispondi in formato JSON con i seguenti campi:
    - consumption_diff: differenza nei consumi con percentuale (solo se i dati sono disponibili)
    - cost_diff: differenza nei costi con percentuale (solo se i dati sono disponibili)
    - anomalies: eventuali anomalie o errori rilevati (solo se evidenti dai dati)
    - explanation: possibili spiegazioni per le differenze (basate sui dati reali)
    - complaint_tips: suggerimenti per contestare eventuali errori (solo se necessario)
    """
    
    try:
        logger.info("Invio richiesta a Bedrock per confronto bollette")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        result = response_body.get('content')[0].get('text')
        logger.info("Risposta ricevuta da Bedrock")
        
        # Estrai il JSON dalla risposta
        try:
            # Cerca di estrarre il JSON dalla risposta
            if '```json' in result:
                json_str = result.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(result)
        except json.JSONDecodeError:
            logger.error("Impossibile analizzare la risposta come JSON")
            # Se non riesce a decodificare il JSON, restituisci la risposta come testo
            return {
                "error": "Impossibile analizzare la risposta come JSON", 
                "raw_response": result,
                "message": "Errore nell'elaborazione del confronto. Controlla i dati forniti."
            }
            
    except Exception as e:
        logger.error(f"Errore durante il confronto delle bollette: {e}")
        return {"error": str(e)}

def chat_with_assistant(user_input, bill_analysis=None):
    """
    Chatta con l'assistente per ottenere informazioni sulla bolletta
    
    Args:
        user_input: Domanda dell'utente
        bill_analysis: Risultato dell'analisi della bolletta (opzionale)
        
    Returns:
        str: Risposta dell'assistente
    """
    context = ""
    if bill_analysis:
        context = f"Analisi della bolletta: {json.dumps(bill_analysis, indent=2)}\n\n"
    
    prompt = f"""
    {context}
    
    Sei un assistente specializzato nell'aiutare i clienti a comprendere le loro bollette elettriche e a risparmiare energia.
    Rispondi alla seguente domanda del cliente in modo chiaro, conciso e utile.
    Basa le tue risposte ESCLUSIVAMENTE sui dati reali presenti nell'analisi della bolletta.
    Se l'informazione richiesta non è disponibile nei dati, indica chiaramente che non puoi rispondere a quella domanda specifica.
    
    Domanda del cliente: {user_input}
    """
    
    try:
        logger.info("Invio richiesta a Bedrock per chat con assistente")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        result = response_body.get('content')[0].get('text')
        logger.info("Risposta ricevuta da Bedrock")
        return result
            
    except Exception as e:
        logger.error(f"Errore durante la chat con l'assistente: {e}")
        return f"Mi dispiace, si è verificato un errore: {str(e)}"
