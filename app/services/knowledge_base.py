"""
Knowledge Base per EnergyWise - Contiene informazioni sui prodotti e offerte
"""
import json
import os
from typing import List, Dict, Any

# Definizione dei prodotti e offerte di EnergyWise
ENERGY_PRODUCTS = [
    {
        "id": "basic-home",
        "name": "EnergyWise Casa Basic",
        "type": "electricity",
        "description": "Piano base per abitazioni residenziali con tariffa fissa.",
        "features": [
            "Prezzo fisso per 12 mesi",
            "Energia 100% da fonti rinnovabili",
            "Nessun costo di attivazione",
            "Fatturazione mensile o bimestrale"
        ],
        "price": {
            "fixed_component": "9,90€/mese",
            "variable_component": "0,12€/kWh",
            "discount_first_month": "50%"
        },
        "target": "Famiglie con consumi medi",
        "requirements": "Nessun requisito particolare",
        "faq": [
            {
                "question": "Posso disdire in qualsiasi momento?",
                "answer": "Sì, puoi disdire il contratto in qualsiasi momento con un preavviso di 30 giorni senza penali."
            },
            {
                "question": "Come posso monitorare i miei consumi?",
                "answer": "Tramite l'app EnergyWise o l'area clienti sul sito web puoi monitorare i tuoi consumi in tempo reale."
            }
        ]
    },
    {
        "id": "eco-plus",
        "name": "EnergyWise Eco Plus",
        "type": "electricity",
        "description": "Piano premium con energia 100% verde e servizi aggiuntivi per la sostenibilità.",
        "features": [
            "Energia certificata 100% da fonti rinnovabili",
            "Report mensile di efficienza energetica",
            "Consulenza energetica gratuita",
            "Programma fedeltà con punti convertibili in sconti",
            "Assicurazione guasti elettrici inclusa"
        ],
        "price": {
            "fixed_component": "12,90€/mese",
            "variable_component": "0,14€/kWh",
            "discount_first_month": "30%"
        },
        "target": "Famiglie attente all'ambiente",
        "requirements": "Nessun requisito particolare",
        "faq": [
            {
                "question": "Cosa significa energia certificata?",
                "answer": "L'energia certificata è garantita da certificati GO (Garanzia d'Origine) che attestano la provenienza da impianti rinnovabili."
            },
            {
                "question": "In cosa consiste la consulenza energetica?",
                "answer": "Un nostro esperto analizzerà i tuoi consumi e ti suggerirà come ottimizzarli per risparmiare."
            }
        ]
    },
    {
        "id": "business-flex",
        "name": "EnergyWise Business Flex",
        "type": "electricity",
        "description": "Piano flessibile per piccole e medie imprese con tariffe personalizzabili.",
        "features": [
            "Tariffe differenziate per fasce orarie",
            "Assistenza prioritaria 24/7",
            "Dashboard analitica avanzata",
            "Consulenza fiscale sugli incentivi energetici",
            "Possibilità di installare colonnine di ricarica per veicoli elettrici"
        ],
        "price": {
            "fixed_component": "19,90€/mese",
            "variable_component": "da 0,10€/kWh a 0,16€/kWh in base alla fascia oraria",
            "discount_first_month": "20%"
        },
        "target": "Piccole e medie imprese",
        "requirements": "Partita IVA",
        "faq": [
            {
                "question": "Quali sono le fasce orarie?",
                "answer": "F1: Lun-Ven 8-19, F2: Lun-Ven 7-8 e 19-23, Sab 7-23, F3: Lun-Sab 23-7, Dom e festivi."
            },
            {
                "question": "Posso modificare il piano in corso d'anno?",
                "answer": "Sì, è possibile modificare il piano una volta ogni 6 mesi senza costi aggiuntivi."
            }
        ]
    },
    {
        "id": "dual-home",
        "name": "EnergyWise Dual Home",
        "type": "electricity_gas",
        "description": "Piano combinato per elettricità e gas con sconto dual fuel.",
        "features": [
            "Gestione unificata di elettricità e gas",
            "Sconto del 10% sul totale della bolletta",
            "Unica fattura per entrambi i servizi",
            "App dedicata per il monitoraggio dei consumi",
            "Assistenza tecnica prioritaria"
        ],
        "price": {
            "electricity": {
                "fixed_component": "8,90€/mese",
                "variable_component": "0,11€/kWh"
            },
            "gas": {
                "fixed_component": "9,90€/mese",
                "variable_component": "0,45€/Smc"
            },
            "discount_dual": "10% sul totale"
        },
        "target": "Famiglie con doppia fornitura",
        "requirements": "Attivazione di entrambi i servizi",
        "faq": [
            {
                "question": "Posso attivare prima un servizio e poi l'altro?",
                "answer": "Sì, puoi attivare prima un servizio e aggiungere l'altro successivamente. Lo sconto dual verrà applicato dalla prima bolletta dopo l'attivazione di entrambi."
            },
            {
                "question": "Cosa succede se disdico uno dei due servizi?",
                "answer": "Se disattivi uno dei due servizi, l'altro rimarrà attivo ma perderai lo sconto dual del 10%."
            }
        ]
    },
    {
        "id": "solar-home",
        "name": "EnergyWise Solar Home",
        "type": "solar",
        "description": "Soluzione completa per l'installazione di pannelli solari domestici.",
        "features": [
            "Pannelli solari di ultima generazione",
            "Installazione e manutenzione incluse",
            "Sistema di monitoraggio in tempo reale",
            "Gestione pratiche per incentivi fiscali",
            "Integrazione con batterie di accumulo (opzionale)",
            "Garanzia 25 anni sui pannelli"
        ],
        "price": {
            "base_package": "da 6.900€ per 3kW",
            "financing": "rate da 99€/mese per 84 mesi",
            "payback_period": "5-7 anni"
        },
        "target": "Proprietari di abitazioni",
        "requirements": "Tetto idoneo all'installazione",
        "faq": [
            {
                "question": "Quanto spazio serve sul tetto?",
                "answer": "Per un impianto da 3kW servono circa 15-20 m² di superficie."
            },
            {
                "question": "Quali incentivi fiscali sono disponibili?",
                "answer": "Attualmente è possibile usufruire della detrazione fiscale del 50% in 10 anni."
            }
        ]
    },
    {
        "id": "smart-home",
        "name": "EnergyWise Smart Home",
        "type": "smart_devices",
        "description": "Kit di dispositivi smart per l'ottimizzazione dei consumi domestici.",
        "features": [
            "Termostato intelligente",
            "Prese smart con monitoraggio consumi",
            "Sensori di presenza per ottimizzazione illuminazione",
            "Hub centrale di controllo",
            "App dedicata per gestione da remoto",
            "Compatibilità con Alexa e Google Home"
        ],
        "price": {
            "starter_kit": "299€",
            "monthly_subscription": "4,90€/mese per servizi cloud e assistenza",
            "installation": "99€ (gratuita per clienti EnergyWise)"
        },
        "target": "Famiglie tech-savvy",
        "requirements": "Connessione Wi-Fi domestica",
        "faq": [
            {
                "question": "Posso installare i dispositivi da solo?",
                "answer": "Sì, tutti i dispositivi sono progettati per un'installazione fai-da-te semplice. In caso di difficoltà, è disponibile un servizio di installazione professionale."
            },
            {
                "question": "Quanto posso risparmiare con questi dispositivi?",
                "answer": "In media, i nostri clienti risparmiano tra il 15% e il 25% sui consumi energetici annuali."
            }
        ]
    }
]

# Offerte speciali e promozioni
SPECIAL_OFFERS = [
    {
        "id": "summer-promo-2025",
        "name": "Promozione Estate 2025",
        "description": "Attiva una fornitura entro il 31/07/2025 e ricevi uno sconto del 30% per i primi 3 mesi.",
        "valid_until": "2025-07-31",
        "applicable_products": ["basic-home", "eco-plus", "dual-home"],
        "terms": "Lo sconto è applicabile solo ai nuovi clienti. Non cumulabile con altre promozioni."
    },
    {
        "id": "friends-referral",
        "name": "Porta un Amico",
        "description": "Ricevi 50€ di sconto in bolletta per ogni amico che attiva una fornitura con EnergyWise.",
        "valid_until": "ongoing",
        "applicable_products": ["all"],
        "terms": "Il bonus viene erogato dopo il primo mese di fornitura attiva dell'amico. Massimo 10 amici all'anno."
    },
    {
        "id": "digital-billing",
        "name": "Bolletta Digitale",
        "description": "Passa alla bolletta digitale e ricevi uno sconto di 2€ su ogni fattura.",
        "valid_until": "ongoing",
        "applicable_products": ["all"],
        "terms": "Lo sconto viene applicato automaticamente a partire dalla prima bolletta digitale."
    },
    {
        "id": "solar-2025",
        "name": "Solare 2025",
        "description": "Installa un impianto fotovoltaico entro il 31/12/2025 e ricevi una batteria di accumulo da 5kWh in omaggio.",
        "valid_until": "2025-12-31",
        "applicable_products": ["solar-home"],
        "terms": "Promozione valida per impianti di potenza minima 4kW. Installazione della batteria inclusa."
    }
]

# FAQ generali su EnergyWise
GENERAL_FAQ = [
    {
        "question": "Come posso attivare una fornitura con EnergyWise?",
        "answer": "Puoi attivare una fornitura online sul nostro sito, chiamando il numero verde 800.123.456 o visitando uno dei nostri punti vendita. Avrai bisogno del tuo codice fiscale, di un documento d'identità e dei dati della fornitura attuale (POD per l'elettricità e PDR per il gas)."
    },
    {
        "question": "Quanto tempo richiede l'attivazione di una nuova fornitura?",
        "answer": "L'attivazione di una nuova fornitura richiede generalmente da 2 a 4 settimane lavorative, a seconda del tipo di passaggio (switch da altro fornitore o nuova attivazione)."
    },
    {
        "question": "Come posso pagare la bolletta?",
        "answer": "Puoi pagare la bolletta tramite addebito diretto su conto corrente (SEPA), carta di credito, bollettino postale o tramite la nostra app. Offriamo anche la possibilità di rateizzare i pagamenti per importi superiori a 100€."
    },
    {
        "question": "Cosa devo fare in caso di guasto o interruzione di corrente?",
        "answer": "In caso di guasto o interruzione, verifica prima se il problema riguarda solo il tuo appartamento o l'intero edificio. Per problemi sulla rete di distribuzione, contatta il numero di emergenza del distributore locale. Per problemi relativi alla tua fornitura, contatta il nostro servizio clienti al numero 800.123.456."
    },
    {
        "question": "EnergyWise fornisce energia rinnovabile?",
        "answer": "Sì, tutti i nostri piani elettrici includono una percentuale di energia da fonti rinnovabili. I piani 'Eco Plus' e 'Solar Home' garantiscono il 100% di energia da fonti rinnovabili certificate."
    },
    {
        "question": "Come posso leggere la mia bolletta?",
        "answer": "La bolletta EnergyWise è strutturata in sezioni: dati cliente e fornitura, riepilogo importi, dettaglio consumi, dettaglio costi e informazioni utili. Puoi trovare una guida dettagliata nella sezione 'Supporto' del nostro sito o utilizzare il nostro chatbot per un'analisi personalizzata."
    },
    {
        "question": "Posso monitorare i miei consumi in tempo reale?",
        "answer": "Sì, tramite l'app EnergyWise o l'area clienti sul nostro sito web puoi monitorare i tuoi consumi quasi in tempo reale se disponi di un contatore intelligente. Altrimenti, potrai visualizzare i dati di consumo aggiornati mensilmente."
    },
    {
        "question": "Come posso risparmiare energia?",
        "answer": "Offriamo diversi strumenti per aiutarti a risparmiare: report personalizzati sui consumi, consigli di efficienza energetica, dispositivi smart per l'ottimizzazione e consulenze energetiche. Inoltre, sul nostro blog pubblichiamo regolarmente articoli con suggerimenti pratici per ridurre i consumi."
    }
]

# Informazioni sull'azienda
COMPANY_INFO = {
    "name": "EnergyWise S.p.A.",
    "founded": 2015,
    "headquarters": "Milano, Italia",
    "mission": "Fornire energia sostenibile e accessibile, aiutando i clienti a ottimizzare i consumi e ridurre l'impatto ambientale.",
    "values": [
        "Sostenibilità ambientale",
        "Innovazione tecnologica",
        "Trasparenza nei prezzi",
        "Eccellenza nel servizio clienti",
        "Responsabilità sociale"
    ],
    "certifications": [
        "ISO 9001:2015 - Gestione della Qualità",
        "ISO 14001:2015 - Gestione Ambientale",
        "ISO 50001:2018 - Gestione dell'Energia",
        "B Corp Certification"
    ],
    "contact": {
        "customer_service": "800.123.456",
        "email": "info@energywise.it",
        "website": "www.energywise.it",
        "social_media": {
            "facebook": "EnergyWiseItalia",
            "instagram": "@energywise_it",
            "linkedin": "EnergyWise-SpA",
            "twitter": "@EnergyWise_IT"
        }
    }
}

class KnowledgeBase:
    """Classe per gestire la knowledge base di EnergyWise"""
    
    def __init__(self):
        """Inizializza la knowledge base"""
        self.products = ENERGY_PRODUCTS
        self.offers = SPECIAL_OFFERS
        self.faq = GENERAL_FAQ
        self.company_info = COMPANY_INFO
        
        # Crea directory per i dati se non esiste
        try:
            os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'data'), exist_ok=True)
            
            # Salva i dati in file JSON per il RAG
            self._save_data()
            logger.info("Knowledge base inizializzata con successo")
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione della knowledge base: {e}")
        
    def _save_data(self):
        """Salva i dati in file JSON per il RAG"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
        # Salva prodotti
        with open(os.path.join(data_dir, 'products.json'), 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
            
        # Salva offerte
        with open(os.path.join(data_dir, 'offers.json'), 'w', encoding='utf-8') as f:
            json.dump(self.offers, f, ensure_ascii=False, indent=2)
            
        # Salva FAQ
        with open(os.path.join(data_dir, 'faq.json'), 'w', encoding='utf-8') as f:
            json.dump(self.faq, f, ensure_ascii=False, indent=2)
            
        # Salva info azienda
        with open(os.path.join(data_dir, 'company_info.json'), 'w', encoding='utf-8') as f:
            json.dump(self.company_info, f, ensure_ascii=False, indent=2)
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Ottiene un prodotto dal suo ID"""
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None
    
    def get_products_by_type(self, product_type: str) -> List[Dict[str, Any]]:
        """Ottiene tutti i prodotti di un determinato tipo"""
        return [p for p in self.products if p["type"] == product_type]
    
    def get_active_offers(self) -> List[Dict[str, Any]]:
        """Ottiene tutte le offerte attive"""
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        return [
            offer for offer in self.offers 
            if offer["valid_until"] == "ongoing" or offer["valid_until"] >= today
        ]
    
    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Cerca nella knowledge base"""
        query = query.lower()
        results = {
            "products": [],
            "offers": [],
            "faq": []
        }
        
        # Cerca nei prodotti
        for product in self.products:
            if (query in product["name"].lower() or 
                query in product["description"].lower() or
                any(query in feature.lower() for feature in product["features"])):
                results["products"].append(product)
                
        # Cerca nelle offerte
        for offer in self.offers:
            if (query in offer["name"].lower() or 
                query in offer["description"].lower()):
                results["offers"].append(offer)
                
        # Cerca nelle FAQ
        for faq in self.faq:
            if (query in faq["question"].lower() or 
                query in faq["answer"].lower()):
                results["faq"].append(faq)
                
        return results
