import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import tempfile
import logging

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_document(file_path):
    """
    Processa un documento (immagine o PDF) ed estrae il testo
    
    Args:
        file_path: Percorso del file da processare
        
    Returns:
        str: Testo estratto dal documento
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

def process_image(image_path):
    """
    Estrae il testo da un'immagine usando OCR
    
    Args:
        image_path: Percorso dell'immagine
        
    Returns:
        str: Testo estratto dall'immagine
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
        return ""

def process_pdf(pdf_path):
    """
    Converte un PDF in immagini ed estrae il testo usando OCR
    
    Args:
        pdf_path: Percorso del file PDF
        
    Returns:
        str: Testo estratto dal PDF
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
        return ""
