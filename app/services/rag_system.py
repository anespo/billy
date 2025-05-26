"""
Sistema RAG (Retrieval-Augmented Generation) per EnergyWise
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import boto3
from botocore.config import Config
import numpy as np
from strands import Agent, tool
from strands.models import BedrockModel

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione AWS Bedrock
region = os.getenv('AWS_REGION', 'us-east-1')
embedding_model_id = os.getenv('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-7-sonnet-20250219-v1:0')

class RAGSystem:
    """Sistema RAG per EnergyWise"""
    
    def __init__(self):
        """Inizializza il sistema RAG"""
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=region,
                config=Config(
                    read_timeout=120,
                    connect_timeout=60,
                    retries={'max_attempts': 3}
                )
            )
            
            # Carica i dati della knowledge base
            self.knowledge_base = self._load_knowledge_base()
            
            # Genera embedding per i documenti
            self.documents, self.embeddings = self._generate_embeddings()
            
            # Inizializza il modello Bedrock
            self.bedrock_model = BedrockModel(
                model_id=model_id,
                region_name=region,
                temperature=0.2,
                timeout=120
            )
            
            # Inizializza l'agente con i tool
            self.agent = self._create_agent()
            
            logger.info("Sistema RAG inizializzato con successo")
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione del sistema RAG: {e}")
            self.bedrock_runtime = None
            self.knowledge_base = {}
            self.documents = []
            self.embeddings = []
            self.bedrock_model = None
            self.agent = None
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Carica i dati della knowledge base"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        knowledge_base = {}
        
        # Carica prodotti
        try:
            with open(os.path.join(data_dir, 'products.json'), 'r', encoding='utf-8') as f:
                knowledge_base['products'] = json.load(f)
        except FileNotFoundError:
            knowledge_base['products'] = []
            
        # Carica offerte
        try:
            with open(os.path.join(data_dir, 'offers.json'), 'r', encoding='utf-8') as f:
                knowledge_base['offers'] = json.load(f)
        except FileNotFoundError:
            knowledge_base['offers'] = []
            
        # Carica FAQ
        try:
            with open(os.path.join(data_dir, 'faq.json'), 'r', encoding='utf-8') as f:
                knowledge_base['faq'] = json.load(f)
        except FileNotFoundError:
            knowledge_base['faq'] = []
            
        # Carica info azienda
        try:
            with open(os.path.join(data_dir, 'company_info.json'), 'r', encoding='utf-8') as f:
                knowledge_base['company_info'] = json.load(f)
        except FileNotFoundError:
            knowledge_base['company_info'] = {}
            
        return knowledge_base
    
    def _generate_document_text(self, doc_type: str, doc: Dict[str, Any]) -> str:
        """Genera il testo del documento per l'embedding"""
        if doc_type == 'products':
            features = "\n".join([f"- {feature}" for feature in doc.get('features', [])])
            faq_text = ""
            for faq in doc.get('faq', []):
                faq_text += f"Q: {faq.get('question', '')}\nA: {faq.get('answer', '')}\n"
            
            price_text = ""
            if isinstance(doc.get('price'), dict):
                if 'electricity' in doc['price'] and 'gas' in doc['price']:
                    # Dual fuel
                    price_text = f"""
                    Elettricità:
                    - Componente fissa: {doc['price']['electricity'].get('fixed_component', '')}
                    - Componente variabile: {doc['price']['electricity'].get('variable_component', '')}
                    
                    Gas:
                    - Componente fissa: {doc['price']['gas'].get('fixed_component', '')}
                    - Componente variabile: {doc['price']['gas'].get('variable_component', '')}
                    
                    Sconto dual: {doc['price'].get('discount_dual', '')}
                    """
                else:
                    # Single service
                    for key, value in doc['price'].items():
                        price_text += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            return f"""
            Prodotto: {doc.get('name', '')}
            Tipo: {doc.get('type', '')}
            Descrizione: {doc.get('description', '')}
            
            Caratteristiche:
            {features}
            
            Prezzo:
            {price_text}
            
            Target: {doc.get('target', '')}
            Requisiti: {doc.get('requirements', '')}
            
            FAQ:
            {faq_text}
            """
        
        elif doc_type == 'offers':
            return f"""
            Offerta: {doc.get('name', '')}
            Descrizione: {doc.get('description', '')}
            Valida fino: {doc.get('valid_until', '')}
            Prodotti applicabili: {', '.join(doc.get('applicable_products', []))}
            Termini e condizioni: {doc.get('terms', '')}
            """
        
        elif doc_type == 'faq':
            return f"""
            Domanda: {doc.get('question', '')}
            Risposta: {doc.get('answer', '')}
            """
        
        elif doc_type == 'company_info':
            values = "\n".join([f"- {value}" for value in doc.get('values', [])])
            certifications = "\n".join([f"- {cert}" for cert in doc.get('certifications', [])])
            
            return f"""
            Nome azienda: {doc.get('name', '')}
            Fondata: {doc.get('founded', '')}
            Sede: {doc.get('headquarters', '')}
            Missione: {doc.get('mission', '')}
            
            Valori:
            {values}
            
            Certificazioni:
            {certifications}
            
            Contatti:
            - Servizio clienti: {doc.get('contact', {}).get('customer_service', '')}
            - Email: {doc.get('contact', {}).get('email', '')}
            - Sito web: {doc.get('contact', {}).get('website', '')}
            """
        
        return json.dumps(doc)
    
    def _generate_embeddings(self) -> tuple:
        """Genera gli embedding per i documenti della knowledge base"""
        documents = []
        
        # Prodotti
        for product in self.knowledge_base.get('products', []):
            doc_text = self._generate_document_text('products', product)
            documents.append({
                'type': 'products',
                'id': product.get('id'),
                'text': doc_text,
                'data': product
            })
        
        # Offerte
        for offer in self.knowledge_base.get('offers', []):
            doc_text = self._generate_document_text('offers', offer)
            documents.append({
                'type': 'offers',
                'id': offer.get('id'),
                'text': doc_text,
                'data': offer
            })
        
        # FAQ
        for i, faq in enumerate(self.knowledge_base.get('faq', [])):
            doc_text = self._generate_document_text('faq', faq)
            documents.append({
                'type': 'faq',
                'id': f'faq_{i}',
                'text': doc_text,
                'data': faq
            })
        
        # Info azienda
        company_info = self.knowledge_base.get('company_info', {})
        if company_info:
            doc_text = self._generate_document_text('company_info', company_info)
            documents.append({
                'type': 'company_info',
                'id': 'company_info',
                'text': doc_text,
                'data': company_info
            })
        
        # Genera embedding per ogni documento
        embeddings = []
        for doc in documents:
            try:
                embedding = self._get_embedding(doc['text'])
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Errore durante la generazione dell'embedding per {doc['id']}: {e}")
        
        return documents, embeddings
    
    def _get_embedding(self, text: str) -> List[float]:
        """Ottiene l'embedding per un testo utilizzando Amazon Bedrock"""
        try:
            if self.bedrock_runtime is None:
                logger.warning("Client Bedrock non inizializzato, ritorno embedding vuoto")
                return []
                
            response = self.bedrock_runtime.invoke_model(
                modelId=embedding_model_id,
                body=json.dumps({
                    "inputText": text[:8000]  # Limita il testo a 8000 caratteri
                })
            )
            
            response_body = json.loads(response.get('body').read())
            embedding = response_body.get('embedding', [])
            return embedding
        except Exception as e:
            logger.error(f"Errore durante la generazione dell'embedding: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcola la similarità del coseno tra due vettori"""
        if not a or not b:
            return 0.0
            
        a = np.array(a)
        b = np.array(b)
        
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Recupera i documenti più rilevanti per una query"""
        if not self.documents or not self.embeddings:
            # Fallback con risposte predefinite se non ci sono documenti
            logger.warning("Nessun documento disponibile per la ricerca")
            
            # Crea una risposta di fallback basata sulla query
            if "tariffa" in query.lower() or "prezzo" in query.lower() or "costo" in query.lower():
                return [{
                    'type': 'products',
                    'id': 'basic-home',
                    'text': "EnergyWise offre diverse tariffe, tra cui la tariffa base 'EnergyWise Casa Basic' a 9,90€/mese con un costo di 0,12€/kWh e la tariffa premium 'EnergyWise Eco Plus' con energia 100% rinnovabile a 12,90€/mese.",
                    'similarity': 0.95
                }]
            elif "eco" in query.lower() or "verde" in query.lower() or "rinnovabile" in query.lower():
                return [{
                    'type': 'products',
                    'id': 'eco-plus',
                    'text': "Il piano 'EnergyWise Eco Plus' offre energia certificata 100% da fonti rinnovabili, report mensile di efficienza energetica, consulenza energetica gratuita e un programma fedeltà con punti convertibili in sconti.",
                    'similarity': 0.95
                }]
            elif "business" in query.lower() or "azienda" in query.lower() or "impresa" in query.lower():
                return [{
                    'type': 'products',
                    'id': 'business-flex',
                    'text': "Il piano 'EnergyWise Business Flex' è pensato per piccole e medie imprese con tariffe differenziate per fasce orarie, assistenza prioritaria 24/7 e dashboard analitica avanzata.",
                    'similarity': 0.95
                }]
            elif "solare" in query.lower() or "pannelli" in query.lower() or "fotovoltaico" in query.lower():
                return [{
                    'type': 'products',
                    'id': 'solar-home',
                    'text': "La soluzione 'EnergyWise Solar Home' include pannelli solari di ultima generazione, installazione e manutenzione incluse, sistema di monitoraggio in tempo reale e gestione pratiche per incentivi fiscali.",
                    'similarity': 0.95
                }]
            elif "offerta" in query.lower() or "promozione" in query.lower() or "sconto" in query.lower():
                return [{
                    'type': 'offers',
                    'id': 'summer-promo-2025',
                    'text': "La 'Promozione Estate 2025' offre uno sconto del 30% per i primi 3 mesi attivando una fornitura entro il 31/07/2025.",
                    'similarity': 0.95
                }]
            else:
                return [{
                    'type': 'company_info',
                    'id': 'company_info',
                    'text': "EnergyWise è un fornitore di energia elettrica e gas fondato nel 2015 con sede a Milano. La nostra missione è fornire energia sostenibile e accessibile, aiutando i clienti a ottimizzare i consumi e ridurre l'impatto ambientale.",
                    'similarity': 0.95
                }]
            
        # Genera embedding per la query
        try:
            query_embedding = self._get_embedding(query)
        except Exception as e:
            logger.error(f"Errore durante la generazione dell'embedding per la query: {e}")
            return []
        
        # Calcola similarità con tutti i documenti
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
        
        # Ordina per similarità decrescente
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Prendi i top_k documenti più rilevanti
        relevant_docs = []
        for i, similarity in similarities[:top_k]:
            if similarity > 0.5:  # Soglia minima di similarità
                doc = self.documents[i].copy()
                doc['similarity'] = similarity
                relevant_docs.append(doc)
        
        return relevant_docs
    
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
            relevant_docs = self.retrieve_relevant_documents(query, top_k=3)
            
            if not relevant_docs:
                return json.dumps({
                    "status": "no_results",
                    "message": "Nessun risultato trovato nella knowledge base."
                })
            
            return json.dumps({
                "status": "success",
                "results": relevant_docs
            })
        
        @tool
        def get_product_details(product_id: str) -> str:
            """
            Ottiene i dettagli di un prodotto specifico.
            
            Args:
                product_id: ID del prodotto
                
            Returns:
                str: Dettagli del prodotto in formato JSON
            """
            for product in self.knowledge_base.get('products', []):
                if product.get('id') == product_id:
                    return json.dumps({
                        "status": "success",
                        "product": product
                    })
            
            return json.dumps({
                "status": "not_found",
                "message": f"Prodotto con ID {product_id} non trovato."
            })
        
        @tool
        def get_active_offers() -> str:
            """
            Ottiene tutte le offerte attive.
            
            Returns:
                str: Offerte attive in formato JSON
            """
            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            active_offers = [
                offer for offer in self.knowledge_base.get('offers', [])
                if offer.get("valid_until") == "ongoing" or offer.get("valid_until", "") >= today
            ]
            
            return json.dumps({
                "status": "success",
                "offers": active_offers
            })
        
        # Definizione del prompt di sistema per l'agente
        SYSTEM_PROMPT = """
        Sei un assistente virtuale di EnergyWise, un fornitore di energia elettrica e gas.
        Il tuo compito è aiutare i clienti a trovare informazioni sui prodotti, offerte e servizi dell'azienda,
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
        """
        
        # Creazione dell'agente con callback per il logging
        def callback_handler(**kwargs):
            if "data" in kwargs:
                logger.debug(f"RAG Agent output: {kwargs['data']}")
            elif "current_tool_use" in kwargs:
                tool = kwargs["current_tool_use"]
                logger.info(f"RAG Agent using tool: {tool.get('name')}")
        
        # Creazione dell'agente
        agent = Agent(
            model=self.bedrock_model,
            tools=[search_knowledge_base, get_product_details, get_active_offers],
            system_prompt=SYSTEM_PROMPT,
            callback_handler=callback_handler
        )
        
        return agent
    
    def answer_question(self, question: str, bill_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Risponde a una domanda utilizzando il sistema RAG
        
        Args:
            question: La domanda dell'utente
            bill_analysis: Analisi della bolletta (opzionale)
            
        Returns:
            str: Risposta alla domanda
        """
        context = ""
        if bill_analysis:
            context = f"""
            Il cliente ha caricato una bolletta. Ecco l'analisi:
            {json.dumps(bill_analysis, indent=2)}
            
            Utilizza queste informazioni per rispondere alla domanda se pertinente.
            """
        
        prompt = f"""
        {context}
        
        Domanda del cliente: {question}
        
        Rispondi in modo chiaro, conciso e utile. Utilizza i tool a tua disposizione per cercare informazioni nella knowledge base.
        Se la domanda riguarda la bolletta e non hai informazioni sufficienti, chiedi gentilmente al cliente di caricare la bolletta.
        """
        
        try:
            logger.info("Invio richiesta all'agente RAG")
            
            # Utilizziamo l'agente RAG
            response = self.agent(prompt)
            result = response.message
            
            logger.info("Risposta ricevuta dall'agente RAG")
            return result
            
        except Exception as e:
            logger.error(f"Errore durante la risposta alla domanda con l'agente RAG: {e}")
            return f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Puoi riprovare più tardi o contattare il nostro servizio clienti al numero 800.123.456."
