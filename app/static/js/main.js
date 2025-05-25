document.addEventListener('DOMContentLoaded', function() {
    // Elementi del DOM
    const uploadForm = document.getElementById('uploadForm');
    const compareCheck = document.getElementById('compareCheck');
    const previousBillUpload = document.getElementById('previousBillUpload');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsSection = document.getElementById('results');
    const comparisonSection = document.getElementById('comparisonSection');
    
    // Elementi dei risultati
    const summaryResult = document.getElementById('summaryResult');
    const costBreakdownResult = document.getElementById('costBreakdownResult');
    const savingTipsResult = document.getElementById('savingTipsResult');
    const anomaliesResult = document.getElementById('anomaliesResult');
    const consumptionDiffResult = document.getElementById('consumptionDiffResult');
    const costDiffResult = document.getElementById('costDiffResult');
    const comparisonAnomaliesResult = document.getElementById('comparisonAnomaliesResult');
    const complaintTipsResult = document.getElementById('complaintTipsResult');
    
    // Variabili per memorizzare i risultati dell'analisi
    let currentBillAnalysis = null;
    let previousBillAnalysis = null;
    
    // Mostra/nascondi il campo per la bolletta precedente
    compareCheck.addEventListener('change', function() {
        previousBillUpload.classList.toggle('d-none', !this.checked);
    });
    
    // Gestione del form di upload
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const billFile = document.getElementById('billFile').files[0];
        if (!billFile) {
            alert('Seleziona un file da analizzare');
            return;
        }
        
        // Mostra spinner di caricamento
        analyzeBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        
        try {
            // Analizza la bolletta corrente
            currentBillAnalysis = await analyzeBill(billFile);
            
            // Se è selezionato il confronto, analizza anche la bolletta precedente
            if (compareCheck.checked) {
                const previousBillFile = document.getElementById('previousBillFile').files[0];
                if (previousBillFile) {
                    previousBillAnalysis = await analyzeBill(previousBillFile);
                    
                    // Confronta le bollette
                    await compareBills(currentBillAnalysis, previousBillAnalysis);
                }
            }
            
            // Visualizza i risultati
            displayResults();
            
            // Scorri alla sezione dei risultati
            resultsSection.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Errore durante l\'analisi:', error);
            alert('Si è verificato un errore durante l\'analisi. Riprova più tardi.');
        } finally {
            // Nascondi spinner di caricamento
            analyzeBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
        }
    });
    
    // Funzione per analizzare una bolletta
    async function analyzeBill(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Errore durante l\'upload del file');
        }
        
        const data = await response.json();
        return data.analysis;
    }
    
    // Funzione per confrontare due bollette
    async function compareBills(currentBill, previousBill) {
        const response = await fetch('/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_bill: currentBill,
                previous_bill: previousBill
            })
        });
        
        if (!response.ok) {
            throw new Error('Errore durante il confronto delle bollette');
        }
        
        const data = await response.json();
        window.comparisonResult = data.comparison;
        return data.comparison;
    }
    
    // Funzione per visualizzare i risultati
    function displayResults() {
        // Mostra la sezione dei risultati
        resultsSection.classList.remove('d-none');
        
        // Popola i risultati dell'analisi corrente
        summaryResult.innerHTML = formatContent(currentBillAnalysis.summary);
        costBreakdownResult.innerHTML = formatContent(currentBillAnalysis.cost_breakdown);
        savingTipsResult.innerHTML = formatList(currentBillAnalysis.saving_tips);
        
        // Gestisci le anomalie
        if (currentBillAnalysis.anomalies && currentBillAnalysis.anomalies.length > 0) {
            anomaliesResult.innerHTML = formatList(currentBillAnalysis.anomalies);
        } else {
            anomaliesResult.innerHTML = '<p class="text-success">Nessuna anomalia rilevata.</p>';
        }
        
        // Gestisci la sezione di confronto
        if (previousBillAnalysis) {
            comparisonSection.classList.remove('d-none');
            
            // Ottieni i risultati del confronto
            const comparisonResult = window.comparisonResult || {};
            
            // Popola i risultati del confronto
            consumptionDiffResult.innerHTML = formatContent(comparisonResult.consumption_diff);
            costDiffResult.innerHTML = formatContent(comparisonResult.cost_diff);
            
            // Gestisci le anomalie del confronto
            if (comparisonResult.anomalies && comparisonResult.anomalies.length > 0) {
                comparisonAnomaliesResult.innerHTML = formatList(comparisonResult.anomalies);
            } else {
                comparisonAnomaliesResult.innerHTML = '<p class="text-success">Nessuna anomalia rilevata nel confronto.</p>';
            }
            
            // Suggerimenti per reclami
            if (comparisonResult.complaint_tips && comparisonResult.complaint_tips.length > 0) {
                complaintTipsResult.innerHTML = formatList(comparisonResult.complaint_tips);
            } else {
                complaintTipsResult.innerHTML = '<p>Non sono necessari reclami.</p>';
            }
        } else {
            comparisonSection.classList.add('d-none');
        }
    }
    
    // Funzione per formattare il contenuto testuale
    function formatContent(content) {
        if (!content) return '<p>Nessuna informazione disponibile.</p>';
        
        // Se è una stringa, formatta i paragrafi
        if (typeof content === 'string') {
            return content.split('\n').map(paragraph => `<p>${paragraph}</p>`).join('');
        }
        
        // Se è un array, formatta come lista
        if (Array.isArray(content)) {
            return formatList(content);
        }
        
        // Se è un oggetto, converti in JSON formattato
        if (typeof content === 'object') {
            try {
                return `<pre class="bg-light p-3 rounded">${JSON.stringify(content, null, 2)}</pre>`;
            } catch (e) {
                console.error('Errore nella conversione dell\'oggetto in JSON:', e);
                return '<p>Errore nella visualizzazione dei dati.</p>';
            }
        }
        
        // Altrimenti restituisci come stringa
        return `<p>${String(content)}</p>`;
    }
    
    // Funzione per formattare una lista
    function formatList(items) {
        if (!items || items.length === 0) return '<p>Nessun elemento disponibile.</p>';
        
        return `<ul class="list-group list-group-flush">
            ${items.map(item => `<li class="list-group-item">${item}</li>`).join('')}
        </ul>`;
    }
});
