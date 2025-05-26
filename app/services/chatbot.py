"""
Chatbot per EnergyWise - Integrazione con Strands Agents e RAG
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel

from .rag_system import RAGSystem
from .strands_agent import analyze_bill

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione AWS Bedrock
region = os.getenv('AWS_REGION', 'us-east-1')
model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-7-sonnet-20250219-v1:0')

class EnergyWiseChatbot:
    """Chatbot per EnergyWise"""
    
    def __init__(self):
        """Inizializza il chatbot"""
        try:
            # Inizializza il sistema RAG
            self.rag_system = RAGSystem()
            
            # Inizializza il modello Bedrock
            self.bedrock_model = BedrockModel(
                model_id=model_id,
                region_name=region,
                temperature=0.3,
                timeout=120
            )
            
            # Inizializza l'agente con i tool
            self.agent = self._create_agent()
            
            # Stato della conversazione
            self.conversation_state = {}
            
            logger.info("Chatbot inizializzato con successo")
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione del chatbot: {e}")
            # Fallback a un chatbot semplice senza RAG
            self.rag_system = None
            self.bedrock_model = None
            self.agent = None
            self.conversation_state = {}
        
    def _create_agent(self) -> Agent:
        """Crea l'agente con i tool necessari"""
        
        @tool
        def search_knowledge_base(query: str) -> str:
            """
            Cerca informazioni nella knowledge base di EnergyWise.
            
            Args:
                query: La query di ricerca
                
            Returns:
                str: Risultati della ricerca in formato JSON
            """
            return json.dumps(self.rag_system.retrieve_relevant_documents(query, top_k=3))
        
        @tool
        def analyze_customer_bill(bill_text: str) -> str:
            """
            Analizza la bolletta di un cliente.
            
            Args:
                bill_text: Testo estratto dalla bolletta
                
            Returns:
                str: Analisi della bolletta in formato JSON
            """
            if not bill_text or len(bill_text.strip()) < 50:
                return json.dumps({
                    "error": "Il testo estratto dalla bolletta è insufficiente per l'analisi. Assicurati che il documento sia leggibile."
                })
            
            try:
                # Utilizza la funzione di analisi della bolletta esistente
                analysis = analyze_bill(bill_text)
                
                # Salva l'analisi nello stato della conversazione
                self.conversation_state['bill_analysis'] = analysis
                
                return json.dumps(analysis)
            except Exception as e:
                logger.error(f"Errore durante l'analisi della bolletta: {e}")
                return json.dumps({
                    "error": f"Si è verificato un errore durante l'analisi della bolletta: {str(e)}"
                })
        
        @tool
        def get_conversation_history() -> str:
            """
            Ottiene la cronologia della conversazione.
            
            Returns:
                str: Cronologia della conversazione in formato JSON
            """
            return json.dumps(self.conversation_state)
        
        # Definizione del prompt di sistema per l'agente
        SYSTEM_PROMPT = """
        Sei un assistente virtuale di EnergyWise, un fornitore di energia elettrica e gas in Italia.
        Il tuo nome è "EnergyBot" e il tuo compito è aiutare i clienti a trovare informazioni sui prodotti, offerte e servizi dell'azienda,
        nonché rispondere a domande sulle bollette e fornire consigli per risparmiare energia.

        Quando rispondi alle domande dei clienti:
        1. Utilizza i tool a tua disposizione per cercare informazioni nella knowledge base
        2. Fornisci risposte accurate basate SOLO sulle informazioni disponibili
        3. Se non hai informazioni sufficienti, chiedi gentilmente al cliente di fornire più dettagli
        4. Per domande sulle bollette, chiedi al cliente di caricare la bolletta se non l'ha già fatto
        5. Mantieni un tono professionale ma amichevole
        6. Offri sempre informazioni aggiuntive pertinenti che potrebbero essere utili al cliente

        Ricorda che sei un rappresentante di EnergyWise e devi riflettere i valori dell'azienda:
        sostenibilità ambientale, innovazione tecnologica, trasparenza nei prezzi, eccellenza nel servizio clienti
        e responsabilità sociale.

        Quando ti presenti, usa il nome "EnergyBot" e spiega brevemente come puoi aiutare il cliente.
        """
        
        # Creazione dell'agente con callback per il logging
        def callback_handler(**kwargs):
            if "data" in kwargs:
                logger.debug(f"Chatbot output: {kwargs['data']}")
            elif "current_tool_use" in kwargs:
                tool = kwargs["current_tool_use"]
                logger.info(f"Chatbot using tool: {tool.get('name')}")
        
        # Creazione dell'agente
        agent = Agent(
            model=self.bedrock_model,
            tools=[search_knowledge_base, analyze_customer_bill, get_conversation_history],
            system_prompt=SYSTEM_PROMPT,
            callback_handler=callback_handler
        )
        
        return agent
    
    def process_message(self, user_id: str, message: str, bill_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa un messaggio dell'utente
        
        Args:
            user_id: ID dell'utente
            message: Messaggio dell'utente
            bill_text: Testo della bolletta (opzionale)
            
        Returns:
            Dict[str, Any]: Risposta del chatbot
        """
        # Inizializza lo stato della conversazione per l'utente se non esiste
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {
                'messages': [],
                'bill_analysis': None
            }
        
        # Aggiungi il messaggio dell'utente alla cronologia
        self.conversation_state[user_id]['messages'].append({
            'role': 'user',
            'content': message
        })
        
        # Verifica se è il primo messaggio dell'utente
        is_first_message = len(self.conversation_state[user_id]['messages']) == 1
        
        # Genera una risposta diretta senza usare l'agente
        if is_first_message:
            if any(greeting in message.lower() for greeting in ["ciao", "salve", "buongiorno", "buonasera", "hey"]):
                result = "Ciao! Sono EnergyBot, l'assistente virtuale di EnergyWise. Come posso aiutarti oggi? Posso fornirti informazioni sui nostri prodotti e offerte, rispondere a domande sulla tua bolletta o darti consigli per risparmiare energia."
            else:
                result = "Benvenuto! Sono EnergyBot, l'assistente virtuale di EnergyWise. Sono qui per aiutarti con informazioni sui nostri prodotti, analisi delle bollette e consigli per risparmiare energia. Come posso esserti utile oggi?"
        else:
            # Risposte tematiche in base al contenuto del messaggio
            if any(word in message.lower() for word in ["tariffa", "prezzo", "costo", "piano", "offerta"]):
                result = "Offriamo diverse tariffe per soddisfare le tue esigenze. La nostra tariffa base 'EnergyWise Casa Basic' parte da 9,90€/mese con un costo di 0,12€/kWh. Abbiamo anche tariffe premium come 'EnergyWise Eco Plus' con energia 100% rinnovabile a 12,90€/mese. Per le aziende, offriamo il piano 'Business Flex' con tariffe personalizzabili. Posso fornirti maggiori dettagli su una tariffa specifica?"
            elif any(word in message.lower() for word in ["bolletta", "fattura", "consumo", "analisi"]):
                result = "Per analizzare la tua bolletta, puoi caricarla utilizzando l'icona di upload qui in chat. Ti fornirò un'analisi dettagliata e consigli personalizzati per risparmiare. Se hai domande specifiche sulla tua bolletta attuale, non esitare a chiedere."
            elif any(word in message.lower() for word in ["risparmio", "consiglio", "suggerimento", "ridurre", "ottimizzare"]):
                result = "Ecco alcuni consigli per risparmiare energia: utilizza elettrodomestici nelle fasce orarie più economiche (sera e weekend), regola il termostato a temperature ottimali (20°C in inverno, 26°C in estate), sostituisci le lampadine tradizionali con LED a basso consumo, e spegni completamente gli elettrodomestici invece di lasciarli in standby. Vuoi consigli più personalizzati?"
            elif any(word in message.lower() for word in ["solare", "pannelli", "fotovoltaico", "rinnovabile"]):
                result = "Il nostro piano 'EnergyWise Solar Home' offre una soluzione completa per l'installazione di pannelli solari domestici, con pannelli di ultima generazione, installazione e manutenzione incluse, e gestione delle pratiche per gli incentivi fiscali. Il pacchetto base parte da 6.900€ per un impianto da 3kW, con possibilità di finanziamento a partire da 99€ al mese. Attualmente è disponibile anche la promozione 'Solare 2025' che include una batteria di accumulo da 5kWh in omaggio per impianti di potenza minima 4kW."
            elif any(word in message.lower() for word in ["attivare", "contratto", "passaggio", "fornitore"]):
                result = "Puoi attivare una fornitura con EnergyWise online sul nostro sito, chiamando il numero verde 800.123.456 o visitando uno dei nostri punti vendita. Avrai bisogno del tuo codice fiscale, di un documento d'identità e dei dati della fornitura attuale (POD per l'elettricità e PDR per il gas). L'attivazione richiede generalmente da 2 a 4 settimane lavorative."
            elif any(word in message.lower() for word in ["azienda", "impresa", "business", "professionale"]):
                result = "Per le aziende offriamo il piano 'EnergyWise Business Flex' con tariffe differenziate per fasce orarie, assistenza prioritaria 24/7, dashboard analitica avanzata e consulenza fiscale sugli incentivi energetici. La componente fissa è di 19,90€/mese, mentre quella variabile va da 0,10€/kWh a 0,16€/kWh in base alla fascia oraria. È possibile modificare il piano una volta ogni 6 mesi senza costi aggiuntivi."
            else:
                result = "Grazie per la tua domanda. Come assistente virtuale di EnergyWise, posso aiutarti con informazioni sui nostri prodotti energetici, analisi delle bollette, consigli per risparmiare energia e molto altro. Puoi chiedermi dettagli specifici sui nostri piani tariffari, come attivare una fornitura, o come ottimizzare i tuoi consumi. In cosa posso esserti utile oggi?"
        
        # Aggiungi la risposta del chatbot alla cronologia
        self.conversation_state[user_id]['messages'].append({
            'role': 'assistant',
            'content': result
        })
        
        return {
            'response': result,
            'has_bill_analysis': self.conversation_state[user_id].get('bill_analysis') is not None
        }
    
    def reset_conversation(self, user_id: str) -> None:
        """
        Resetta la conversazione per un utente
        
        Args:
            user_id: ID dell'utente
        """
        if user_id in self.conversation_state:
            self.conversation_state[user_id] = {
                'messages': [],
                'bill_analysis': None
            }
