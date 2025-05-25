import os
import json
import logging
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione AWS Bedrock
region = os.getenv('AWS_REGION', 'us-east-1')
model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')

# Definizione dei tool personalizzati per l'agente
@tool
def extract_bill_data(bill_text: str) -> str:
    """
    Estrae i dati principali da una bolletta elettrica.
    
    Args:
        bill_text: Testo estratto dalla bolletta
        
    Returns:
        str: Dati estratti in formato JSON
    """
    logger.info("Tool extract_bill_data chiamato")
    if not bill_text or len(bill_text.strip()) < 50:
        return json.dumps({
            "error": "Il testo estratto dalla bolletta è insufficiente per l'analisi. Assicurati che il documento sia leggibile."
        })
    
    # Estrai i dati principali dalla bolletta
    return json.dumps({
        "status": "success",
        "message": "Dati estratti dalla bolletta",
        "text": bill_text[:500] + "..." # Tronca il testo per il log
    })

@tool
def analyze_consumption(consumption_data: str) -> str:
    """
    Analizza i dati di consumo di una bolletta elettrica.
    
    Args:
        consumption_data: Dati di consumo estratti dalla bolletta
        
    Returns:
        str: Analisi dei consumi in formato JSON
    """
    logger.info("Tool analyze_consumption chiamato")
    try:
        data = json.loads(consumption_data)
        return json.dumps({
            "status": "success",
            "message": "Analisi dei consumi completata",
            "data": data
        })
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Formato dati non valido"
        })

@tool
def generate_saving_tips(bill_data: str) -> str:
    """
    Genera consigli per risparmiare sulla bolletta elettrica.
    
    Args:
        bill_data: Dati della bolletta
        
    Returns:
        str: Consigli per risparmiare in formato JSON
    """
    logger.info("Tool generate_saving_tips chiamato")
    try:
        data = json.loads(bill_data) if isinstance(bill_data, str) else bill_data
        return json.dumps({
            "status": "success",
            "message": "Consigli generati",
            "data": data
        })
    except (json.JSONDecodeError, TypeError):
        return json.dumps({
            "error": "Formato dati non valido"
        })

@tool
def detect_anomalies(bill_data: str) -> str:
    """
    Rileva anomalie nei dati della bolletta elettrica.
    
    Args:
        bill_data: Dati della bolletta
        
    Returns:
        str: Anomalie rilevate in formato JSON
    """
    logger.info("Tool detect_anomalies chiamato")
    try:
        data = json.loads(bill_data) if isinstance(bill_data, str) else bill_data
        return json.dumps({
            "status": "success",
            "message": "Anomalie rilevate",
            "data": data
        })
    except (json.JSONDecodeError, TypeError):
        return json.dumps({
            "error": "Formato dati non valido"
        })

@tool
def compare_bills_data(current_bill_json: str, previous_bill_json: str) -> str:
    """
    Confronta due bollette elettriche e identifica differenze e anomalie.
    
    Args:
        current_bill_json: Dati della bolletta corrente in formato JSON
        previous_bill_json: Dati della bolletta precedente in formato JSON
        
    Returns:
        str: Risultato del confronto in formato JSON
    """
    logger.info("Tool compare_bills_data chiamato")
    try:
        current_bill = json.loads(current_bill_json) if isinstance(current_bill_json, str) else current_bill_json
        previous_bill = json.loads(previous_bill_json) if isinstance(previous_bill_json, str) else previous_bill_json
        
        return json.dumps({
            "status": "success",
            "message": "Confronto completato",
            "current_bill": current_bill,
            "previous_bill": previous_bill
        })
    except (json.JSONDecodeError, TypeError):
        return json.dumps({
            "error": "Formato dati non valido"
        })

# Definizione del prompt di sistema per l'agente
SYSTEM_PROMPT = """
Sei un assistente specializzato nell'analisi delle bollette elettriche spagnole. Il tuo compito è aiutare i clienti a comprendere le loro bollette, identificare possibili errori e fornire consigli per risparmiare energia.

Quando analizzi una bolletta, devi:
1. Estrarre i dati principali (periodo di fatturazione, importo totale, consumi in kWh)
2. Identificare le voci di costo specifiche presenti nella bolletta
3. Identificare eventuali anomalie o incongruenze nei consumi o nei costi
4. Fornire consigli pratici basati ESCLUSIVAMENTE sui dati reali estratti

Quando confronti due bollette, devi:
1. Identificare differenze nei consumi (kWh) se presenti in entrambe le bollette
2. Identificare differenze nei costi se presenti in entrambe le bollette
3. Identificare possibili errori o anomalie basati ESCLUSIVAMENTE sui dati forniti
4. Suggerire motivi plausibili per eventuali aumenti o diminuzioni
5. Fornire suggerimenti per contestare eventuali errori al call center SOLO se ci sono anomalie evidenti

Rispondi sempre in formato JSON strutturato e ben formattato.
"""

# Creazione del modello Bedrock con timeout aumentato
bedrock_model = BedrockModel(
    model_id=model_id,
    region_name=region,
    temperature=0.2,  # Temperatura bassa per risposte più deterministiche
    timeout=120  # Timeout aumentato a 120 secondi
)

# Creazione dell'agente con callback per il logging
def callback_handler(**kwargs):
    if "data" in kwargs:
        logger.debug(f"Strands Agent output: {kwargs['data']}")
    elif "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        logger.info(f"Strands Agent using tool: {tool.get('name')}")

# Creazione dell'agente
bill_analyzer_agent = Agent(
    model=bedrock_model,
    tools=[extract_bill_data, analyze_consumption, generate_saving_tips, detect_anomalies, compare_bills_data],
    system_prompt=SYSTEM_PROMPT,
    callback_handler=callback_handler
)

def analyze_bill(bill_text):
    """
    Analizza il testo di una bolletta elettrica utilizzando l'agente Strands
    
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
    Analizza attentamente la seguente bolletta elettrica ed estrai SOLO i dati reali presenti nel testo. Non inventare o simulare dati non presenti.

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
        logger.info("Invio richiesta all'agente Strands per analisi bolletta")
        
        # Utilizziamo l'agente Strands
        response = bill_analyzer_agent(prompt)
        result = response.message
        
        logger.info("Risposta ricevuta dall'agente Strands")
        
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
        logger.error(f"Errore durante l'analisi della bolletta con Strands Agent: {e}")
        
        # Fallback a boto3 diretto in caso di errore
        logger.info("Fallback a boto3 diretto")
        return fallback_analyze_bill(bill_text)

def compare_with_previous(current_bill, previous_bill=None):
    """
    Confronta la bolletta corrente con una precedente utilizzando l'agente Strands
    
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
    Confronta la bolletta corrente con quella precedente e identifica SOLO differenze reali basate sui dati forniti. Non inventare o simulare dati non presenti.

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
        logger.info("Invio richiesta all'agente Strands per confronto bollette")
        
        # Utilizziamo l'agente Strands
        response = bill_analyzer_agent(prompt)
        result = response.message
        
        logger.info("Risposta ricevuta dall'agente Strands")
        
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
        logger.error(f"Errore durante il confronto delle bollette con Strands Agent: {e}")
        
        # Fallback a boto3 diretto in caso di errore
        logger.info("Fallback a boto3 diretto")
        return fallback_compare_with_previous(current_bill, previous_bill)

def chat_with_assistant(user_input, bill_analysis=None):
    """
    Chatta con l'assistente per ottenere informazioni sulla bolletta utilizzando l'agente Strands
    
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
    
    Rispondi alla seguente domanda del cliente in modo chiaro, conciso e utile.
    Basa le tue risposte ESCLUSIVAMENTE sui dati reali presenti nell'analisi della bolletta.
    Se l'informazione richiesta non è disponibile nei dati, indica chiaramente che non puoi rispondere a quella domanda specifica.
    
    Domanda del cliente: {user_input}
    """
    
    try:
        logger.info("Invio richiesta all'agente Strands per chat con assistente")
        
        # Utilizziamo l'agente Strands
        response = bill_analyzer_agent(prompt)
        result = response.message
        
        logger.info("Risposta ricevuta dall'agente Strands")
        return result
            
    except Exception as e:
        logger.error(f"Errore durante la chat con l'assistente con Strands Agent: {e}")
        
        # Fallback a boto3 diretto in caso di errore
        logger.info("Fallback a boto3 diretto")
        return fallback_chat_with_assistant(user_input, bill_analysis)

# Funzioni di fallback che utilizzano boto3 direttamente
def fallback_analyze_bill(bill_text):
    """
    Funzione di fallback che utilizza boto3 direttamente per analizzare la bolletta
    """
    import boto3
    from botocore.config import Config
    
    prompt = f"""
    Analizza attentamente la seguente bolletta elettrica ed estrai SOLO i dati reali presenti nel testo. Non inventare o simulare dati non presenti.

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
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
            config=Config(
                read_timeout=120,
                connect_timeout=60,
                retries={'max_attempts': 3}
            )
        )
        
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
        
        # Estrai il JSON dalla risposta
        try:
            if '```json' in result:
                json_str = result.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(result)
        except json.JSONDecodeError:
            return {
                "error": "Impossibile analizzare la risposta come JSON", 
                "raw_response": result,
                "summary": "Errore nell'elaborazione della risposta. Controlla il testo estratto."
            }
            
    except Exception as e:
        logger.error(f"Errore durante l'analisi della bolletta con fallback: {e}")
        return {"error": str(e)}

def fallback_compare_with_previous(current_bill, previous_bill=None):
    """
    Funzione di fallback che utilizza boto3 direttamente per confrontare le bollette
    """
    import boto3
    from botocore.config import Config
    
    if not previous_bill:
        return {
            "message": "Nessuna bolletta precedente disponibile per il confronto",
            "comparison": None
        }
    
    prompt = f"""
    Confronta la bolletta corrente con quella precedente e identifica SOLO differenze reali basate sui dati forniti. Non inventare o simulare dati non presenti.

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
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
            config=Config(
                read_timeout=120,
                connect_timeout=60,
                retries={'max_attempts': 3}
            )
        )
        
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
        
        # Estrai il JSON dalla risposta
        try:
            if '```json' in result:
                json_str = result.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return json.loads(result)
        except json.JSONDecodeError:
            return {
                "error": "Impossibile analizzare la risposta come JSON", 
                "raw_response": result,
                "message": "Errore nell'elaborazione del confronto. Controlla i dati forniti."
            }
            
    except Exception as e:
        logger.error(f"Errore durante il confronto delle bollette con fallback: {e}")
        return {"error": str(e)}

def fallback_chat_with_assistant(user_input, bill_analysis=None):
    """
    Funzione di fallback che utilizza boto3 direttamente per chattare con l'assistente
    """
    import boto3
    from botocore.config import Config
    
    context = ""
    if bill_analysis:
        context = f"Analisi della bolletta: {json.dumps(bill_analysis, indent=2)}\n\n"
    
    prompt = f"""
    {context}
    
    Rispondi alla seguente domanda del cliente in modo chiaro, conciso e utile.
    Basa le tue risposte ESCLUSIVAMENTE sui dati reali presenti nell'analisi della bolletta.
    Se l'informazione richiesta non è disponibile nei dati, indica chiaramente che non puoi rispondere a quella domanda specifica.
    
    Domanda del cliente: {user_input}
    """
    
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
            config=Config(
                read_timeout=120,
                connect_timeout=60,
                retries={'max_attempts': 3}
            )
        )
        
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
        return result
            
    except Exception as e:
        logger.error(f"Errore durante la chat con l'assistente con fallback: {e}")
        return f"Mi dispiace, si è verificato un errore: {str(e)}"
