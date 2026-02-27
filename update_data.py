import os
import json
import datetime
import pytz
import google.generativeai as genai

# Setup timezone
rome_tz = pytz.timezone('Europe/Rome')
today = datetime.datetime.now(rome_tz)
date_str = today.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata nelle Github Secrets.")
    exit(1)

genai.configure(api_key=api_key)

prompt = f"""
1. Obiettivo: FAI UNA RICERCA SUL WEB per trovare e compilare una lista di eventi sportivi italiani in TV per la data di oggi, che è: {date_str}. 
Devi usare le tue capacità di ricerca per trovare il palinsesto televisivo reale di oggi per queste categorie target:
- Calcio (Serie A, Champions League/Europa/Conference League con squadre italiane, Serie C per Monza e Catanzaro, Serie D per Reggina)
- Tennis (ATP/WTA tornei con giocatori italiani come Sinner, Musetti, Berrettini, Paolini, ecc.)
- Formula 1
- MotoGP
- Volley (partite di Monza)
- Sci Alpino (Federica Brignone o Sofia Goggia).

Tutti gli orari devono essere convertiti e mostrati in CET. Includi anche eventi della notte fonda se fanno parte del palinsesto di oggi.

2. Formato di output: Rispondi ESCLUSIVAMENTE con un array JSON valido, senza blocchi markdown (no ```json). 
I campi per ogni oggetto devono essere esattamente: "orario", "evento", "competizione", "canale", "note".
Se non ci sono eventi in programma oggi in queste categorie, restituisci un array vuoto: []
"""

# Utilizziamo la versione 1.5-flash che è gratuita, veloce e 
# pienamente compatibile con il tool google_search_retrieval tramite l'SDK attuale
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    # Abilitiamo il tool di ricerca su Google
    response = model.generate_content(
        prompt,
        tools='google_search_retrieval'
    )
    
    result_text = response.text.strip()
    
    # Pulizia di eventuali markdown rimasti
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    elif result_text.startswith("```"):
        result_text = result_text[3:]
        
    if result_text.endswith("```"):
        result_text = result_text[:-3]
        
    result_text = result_text.strip()
    
    # Se il modello restituisce una stringa vuota ma non ha dato errore
    if not result_text:
        result_text = "[]"
    
    data = json.loads(result_text)
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Dati aggiornati con successo!")
except Exception as e:
    print(f"Si è verificato un errore durante l'esecuzione.")
    if 'response' in locals() and hasattr(response, 'text'):
        print(f"Risposta parziale: {response.text}")
    print(f"Dettaglio Errore: {e}")
    exit(1)