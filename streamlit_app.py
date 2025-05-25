import streamlit as st
import os
import tempfile
import json
import logging
from dotenv import load_dotenv
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from app.services.document_processor import process_document
from app.services.strands_agent import analyze_bill, compare_with_previous, chat_with_assistant

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurazione della pagina
st.set_page_config(
    page_title="EnergyWise - Analisi Bollette",
    page_icon="⚡",
    layout="wide"
)

# Funzioni di utilità
def process_image(image_path):
    """
    Estrae il testo da un'immagine usando OCR
    """
    try:
        logger.info(f"Elaborazione immagine: {image_path}")
        image = Image.open(image_path)
        
        # Migliora la qualità dell'immagine per OCR
        # Converti in scala di grigi
        image = image.convert('L')
        
        # Prova con diverse lingue in ordine di priorità
        languages = ['spa', 'eng']
        text = ""
        
        for lang in languages:
            try:
                logger.info(f"Tentativo di OCR con lingua: {lang}")
                text = pytesseract.image_to_string(image, lang=lang)
                if text and len(text.strip()) > 10:
                    logger.info(f"OCR riuscito con lingua: {lang}")
                    break
            except Exception as e:
                logger.warning(f"OCR fallito con lingua {lang}: {e}")
        
        if not text or len(text.strip()) < 10:
            # Se tutte le lingue falliscono, prova senza specificare la lingua
            logger.warning("Tentativo di OCR senza specificare la lingua")
            text = pytesseract.image_to_string(image)
        
        if not text or len(text.strip()) < 10:
            logger.warning(f"Poco o nessun testo estratto dall'immagine: {image_path}")
        else:
            logger.info(f"Testo estratto con successo dall'immagine: {len(text)} caratteri")
        
        return text
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione dell'immagine: {e}")
        st.error(f"Errore durante l'elaborazione dell'immagine: {e}")
        return ""

def process_pdf(pdf_path):
    """
    Converte un PDF in immagini ed estrae il testo usando OCR
    """
    try:
        logger.info(f"Elaborazione PDF: {pdf_path}")
        with tempfile.TemporaryDirectory() as path:
            # Converti PDF in immagini
            images = convert_from_path(pdf_path, output_folder=path, dpi=300)
            
            if not images:
                logger.warning(f"Nessuna immagine estratta dal PDF: {pdf_path}")
                return ""
            
            logger.info(f"Estratte {len(images)} pagine dal PDF")
            
            text = ""
            # Prova con diverse lingue in ordine di priorità
            languages = ['spa', 'eng']
            
            for i, image in enumerate(images):
                # Converti in scala di grigi per migliorare OCR
                image = image.convert('L')
                
                page_text = ""
                for lang in languages:
                    try:
                        logger.info(f"Tentativo di OCR sulla pagina {i+1} con lingua: {lang}")
                        page_text = pytesseract.image_to_string(image, lang=lang)
                        if page_text and len(page_text.strip()) > 10:
                            logger.info(f"OCR riuscito sulla pagina {i+1} con lingua: {lang}")
                            break
                    except Exception as e:
                        logger.warning(f"OCR fallito sulla pagina {i+1} con lingua {lang}: {e}")
                
                if not page_text or len(page_text.strip()) < 10:
                    # Se tutte le lingue falliscono, prova senza specificare la lingua
                    logger.warning(f"Tentativo di OCR sulla pagina {i+1} senza specificare la lingua")
                    page_text = pytesseract.image_to_string(image)
                text += f"--- PAGINA {i+1} ---\n{page_text}\n\n"
            
            if not text or len(text.strip()) < 10:
                logger.warning(f"Poco o nessun testo estratto dal PDF: {pdf_path}")
            else:
                logger.info(f"Testo estratto con successo dal PDF: {len(text)} caratteri")
            
            return text
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione del PDF: {e}")
        st.error(f"Errore durante l'elaborazione del PDF: {e}")
        return ""

def process_document(file_path):
    """
    Processa un documento (immagine o PDF) ed estrae il testo
    """
    if not os.path.exists(file_path):
        logger.error(f"File non trovato: {file_path}")
        return ""
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.jpg', '.jpeg', '.png']:
        return process_image(file_path)
    elif file_extension == '.pdf':
        return process_pdf(file_path)
    else:
        logger.error(f"Formato file non supportato: {file_extension}")
        return ""

def analyze_bill(bill_text):
    """
    Analizza il testo di una bolletta elettrica utilizzando Claude 3.5 Sonnet
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

def compare_with_previous(current_bill, previous_bill):
    """
    Confronta la bolletta corrente con una precedente
    """
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

# Interfaccia utente
def main():
    # Sidebar
    with st.sidebar:
        st.image("app/static/images/hero-image-new.png", width=200)
        st.title("EnergyWise")
        st.subheader("Analisi Bollette Elettriche")
        
        st.markdown("---")
        st.markdown("### Come funziona")
        st.markdown("""
        1. Carica la tua bolletta elettrica
        2. Ottieni un'analisi dettagliata
        3. Confronta con bollette precedenti
        4. Chatta con l'assistente per chiarimenti
        """)
        
        st.markdown("---")
        st.markdown("### Formati supportati")
        st.markdown("- PDF")
        st.markdown("- JPG/JPEG")
        st.markdown("- PNG")
    
    # Header principale
    colored_header(
        label="Analizza la tua bolletta elettrica",
        description="Carica la tua bolletta e scopri come risparmiare, identificare errori e ottimizzare i tuoi consumi.",
        color_name="blue-70"
    )
    
    # Inizializza le variabili di sessione
    if 'current_bill_analysis' not in st.session_state:
        st.session_state.current_bill_analysis = None
    if 'previous_bill_analysis' not in st.session_state:
        st.session_state.previous_bill_analysis = None
    if 'comparison_result' not in st.session_state:
        st.session_state.comparison_result = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    if 'prev_extracted_text' not in st.session_state:
        st.session_state.prev_extracted_text = None
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Carica Bolletta", "Testo Estratto", "Analisi", "Assistente"])
    
    # Tab 1: Carica Bolletta
    with tab1:
        st.subheader("Carica la tua bolletta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader("Seleziona un file (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"], key="current_bill")
            
            if uploaded_file is not None:
                # Salva il file temporaneamente
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                st.success(f"File caricato: {uploaded_file.name}")
                
                # Mostra l'immagine o la prima pagina del PDF
                if uploaded_file.type.startswith('image'):
                    st.image(uploaded_file, caption="Bolletta caricata", use_column_width=True)
                elif uploaded_file.type == 'application/pdf':
                    try:
                        images = convert_from_path(tmp_file_path)
                        if images:
                            st.image(images[0], caption="Prima pagina della bolletta", use_column_width=True)
                    except Exception as e:
                        st.error(f"Errore nella visualizzazione del PDF: {e}")
                
                # Pulsante per analizzare la bolletta
                if st.button("Estrai Testo e Analizza Bolletta"):
                    with st.spinner("Estrazione del testo in corso..."):
                        # Estrai il testo dal documento
                        bill_text = process_document(tmp_file_path)
                        st.session_state.extracted_text = bill_text
                        
                        if bill_text and len(bill_text.strip()) > 50:
                            st.success("Testo estratto con successo! Vai alla tab 'Testo Estratto' per visualizzarlo.")
                            
                            with st.spinner("Analisi in corso..."):
                                # Analizza la bolletta
                                analysis_result = analyze_bill(bill_text)
                                
                                if "error" in analysis_result:
                                    st.error(f"Errore nell'analisi: {analysis_result['error']}")
                                else:
                                    st.session_state.current_bill_analysis = analysis_result
                                    st.success("Analisi completata! Vai alla tab 'Analisi' per vedere i risultati.")
                        else:
                            st.error("Impossibile estrarre testo sufficiente dal documento. Assicurati che il documento sia leggibile.")
        
        with col2:
            st.subheader("Confronta con bolletta precedente")
            previous_file = st.file_uploader("Seleziona la bolletta precedente (opzionale)", type=["pdf", "jpg", "jpeg", "png"], key="previous_bill")
            
            if previous_file is not None:
                # Salva il file temporaneamente
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(previous_file.name)[1]) as tmp_file:
                    tmp_file.write(previous_file.getvalue())
                    prev_tmp_file_path = tmp_file.name
                
                st.success(f"File precedente caricato: {previous_file.name}")
                
                # Mostra l'immagine o la prima pagina del PDF
                if previous_file.type.startswith('image'):
                    st.image(previous_file, caption="Bolletta precedente", use_column_width=True)
                elif previous_file.type == 'application/pdf':
                    try:
                        images = convert_from_path(prev_tmp_file_path)
                        if images:
                            st.image(images[0], caption="Prima pagina della bolletta precedente", use_column_width=True)
                    except Exception as e:
                        st.error(f"Errore nella visualizzazione del PDF: {e}")
                
                # Pulsante per analizzare la bolletta precedente
                if st.button("Estrai Testo e Analizza Bolletta Precedente"):
                    with st.spinner("Estrazione del testo in corso..."):
                        # Estrai il testo dal documento
                        prev_bill_text = process_document(prev_tmp_file_path)
                        st.session_state.prev_extracted_text = prev_bill_text
                        
                        if prev_bill_text and len(prev_bill_text.strip()) > 50:
                            st.success("Testo estratto con successo! Vai alla tab 'Testo Estratto' per visualizzarlo.")
                            
                            with st.spinner("Analisi in corso..."):
                                # Analizza la bolletta
                                prev_analysis_result = analyze_bill(prev_bill_text)
                                
                                if "error" in prev_analysis_result:
                                    st.error(f"Errore nell'analisi: {prev_analysis_result['error']}")
                                else:
                                    st.session_state.previous_bill_analysis = prev_analysis_result
                                    st.success("Analisi della bolletta precedente completata!")
                        else:
                            st.error("Impossibile estrarre testo sufficiente dal documento. Assicurati che il documento sia leggibile.")
            
            # Pulsante per confrontare le bollette
            if st.session_state.current_bill_analysis and st.session_state.previous_bill_analysis:
                if st.button("Confronta Bollette"):
                    with st.spinner("Confronto in corso..."):
                        comparison_result = compare_with_previous(
                            st.session_state.current_bill_analysis,
                            st.session_state.previous_bill_analysis
                        )
                        
                        if "error" in comparison_result:
                            st.error(f"Errore nel confronto: {comparison_result['error']}")
                        else:
                            st.session_state.comparison_result = comparison_result
                            st.success("Confronto completato! Vai alla tab 'Analisi' per vedere i risultati.")
    
    # Tab 2: Testo Estratto
    with tab2:
        st.subheader("Testo Estratto dalle Bollette")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Bolletta Corrente")
            if st.session_state.extracted_text:
                st.text_area("Testo estratto", st.session_state.extracted_text, height=400)
                
                # Opzione per modificare il testo estratto
                if st.button("Modifica Testo Estratto"):
                    edited_text = st.text_area("Modifica il testo estratto se necessario", st.session_state.extracted_text, height=400, key="edit_current")
                    
                    if st.button("Rianalizza con Testo Modificato"):
                        with st.spinner("Analisi in corso..."):
                            # Analizza la bolletta con il testo modificato
                            analysis_result = analyze_bill(edited_text)
                            
                            if "error" in analysis_result:
                                st.error(f"Errore nell'analisi: {analysis_result['error']}")
                            else:
                                st.session_state.current_bill_analysis = analysis_result
                                st.session_state.extracted_text = edited_text
                                st.success("Analisi completata! Vai alla tab 'Analisi' per vedere i risultati.")
            else:
                st.info("Carica e analizza una bolletta nella tab 'Carica Bolletta' per vedere il testo estratto qui.")
        
        with col2:
            st.markdown("### Bolletta Precedente")
            if st.session_state.prev_extracted_text:
                st.text_area("Testo estratto", st.session_state.prev_extracted_text, height=400)
                
                # Opzione per modificare il testo estratto
                if st.button("Modifica Testo Estratto (Precedente)"):
                    edited_text = st.text_area("Modifica il testo estratto se necessario", st.session_state.prev_extracted_text, height=400, key="edit_previous")
                    
                    if st.button("Rianalizza con Testo Modificato (Precedente)"):
                        with st.spinner("Analisi in corso..."):
                            # Analizza la bolletta con il testo modificato
                            prev_analysis_result = analyze_bill(edited_text)
                            
                            if "error" in prev_analysis_result:
                                st.error(f"Errore nell'analisi: {prev_analysis_result['error']}")
                            else:
                                st.session_state.previous_bill_analysis = prev_analysis_result
                                st.session_state.prev_extracted_text = edited_text
                                st.success("Analisi completata! Vai alla tab 'Analisi' per vedere i risultati.")
            else:
                st.info("Carica e analizza una bolletta precedente nella tab 'Carica Bolletta' per vedere il testo estratto qui.")
    
    # Tab 3: Analisi
    with tab3:
        if st.session_state.current_bill_analysis:
            st.subheader("Risultati dell'Analisi")
            
            # Riepilogo e voci di costo
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Riepilogo")
                st.markdown(st.session_state.current_bill_analysis.get("summary", "Nessuna informazione disponibile"))
            
            with col2:
                st.markdown("### Voci di Costo")
                st.markdown(st.session_state.current_bill_analysis.get("cost_breakdown", "Nessuna informazione disponibile"))
            
            # Consigli e anomalie
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Consigli per Risparmiare")
                saving_tips = st.session_state.current_bill_analysis.get("saving_tips", [])
                if saving_tips and len(saving_tips) > 0:
                    for tip in saving_tips:
                        st.markdown(f"- {tip}")
                else:
                    st.markdown("Nessun consiglio disponibile basato sui dati estratti")
            
            with col2:
                st.markdown("### Anomalie Rilevate")
                anomalies = st.session_state.current_bill_analysis.get("anomalies", [])
                if anomalies and len(anomalies) > 0:
                    for anomaly in anomalies:
                        st.markdown(f"- {anomaly}")
                else:
                    st.markdown("Nessuna anomalia rilevata nei dati estratti")
            
            # Dati grezzi
            st.markdown("### Dati Estratti")
            raw_data = st.session_state.current_bill_analysis.get("raw_data", {})
            if raw_data:
                st.json(raw_data)
            else:
                st.markdown("Nessun dato strutturato disponibile")
            
            # Confronto con bolletta precedente
            if st.session_state.comparison_result:
                st.markdown("---")
                st.subheader("Confronto con Bolletta Precedente")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Differenze nei Consumi")
                    st.markdown(st.session_state.comparison_result.get("consumption_diff", "Confronto non disponibile"))
                    
                    st.markdown("### Possibili Errori")
                    anomalies = st.session_state.comparison_result.get("anomalies", [])
                    if anomalies and len(anomalies) > 0:
                        for anomaly in anomalies:
                            st.markdown(f"- {anomaly}")
                    else:
                        st.markdown("Nessun errore rilevato nel confronto")
                
                with col2:
                    st.markdown("### Differenze nei Costi")
                    st.markdown(st.session_state.comparison_result.get("cost_diff", "Confronto non disponibile"))
                    
                    st.markdown("### Suggerimenti per Reclami")
                    complaint_tips = st.session_state.comparison_result.get("complaint_tips", [])
                    if complaint_tips and len(complaint_tips) > 0:
                        for tip in complaint_tips:
                            st.markdown(f"- {tip}")
                    else:
                        st.markdown("Nessun suggerimento disponibile per reclami")
                
                st.markdown("### Spiegazione")
                st.markdown(st.session_state.comparison_result.get("explanation", "Nessuna spiegazione disponibile"))
        else:
            st.info("Carica e analizza una bolletta nella tab 'Carica Bolletta' per vedere i risultati qui.")
    
    # Tab 4: Assistente
    with tab4:
        st.subheader("Assistente Virtuale")
        
        if st.session_state.current_bill_analysis:
            # Mostra la cronologia della chat
            for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
                message(user_msg, is_user=True, key=f"user_msg_{i}")
                message(bot_msg, key=f"bot_msg_{i}")
            
            # Input per la chat
            user_input = st.text_input("Fai una domanda sulla tua bolletta:", key="user_input")
            
            if user_input:
                # Aggiungi la domanda dell'utente alla cronologia
                st.session_state.chat_history.append((user_input, ""))
                
                # Ottieni la risposta dall'assistente
                with st.spinner("L'assistente sta rispondendo..."):
                    bot_response = chat_with_assistant(user_input, st.session_state.current_bill_analysis)
                
                # Aggiorna l'ultima risposta nella cronologia
                st.session_state.chat_history[-1] = (user_input, bot_response)
                
                # Pulisci l'input
                st.session_state.user_input = ""
                
                # Ricarica la pagina per mostrare la nuova risposta
                st.experimental_rerun()
        else:
            st.info("Carica e analizza una bolletta nella tab 'Carica Bolletta' per chattare con l'assistente.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        import os
        os.environ["STREAMLIT_SERVER_PORT"] = "8501"  # Porta predefinita di Streamlit
    main()
