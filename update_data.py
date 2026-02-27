import os
import json
import datetime
import pytz
from google import genai
from google.genai import types

# Setup timezone
rome_tz = pytz.timezone('Europe/Rome')
today = datetime.datetime.now(rome_tz)
date_str = today.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata nelle Github Secrets.")
    exit(1)

# Inizializza il nuovo client unificato
client = genai.Client(api_key=api_key)

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

try:
    # Configura il tool di ricerca secondo il nuovo SDK
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # Configura le impostazioni di generazione
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    # Effettua la richiesta usando l'API aggiornata e il modello 2.5-flash
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
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
    
    # Se il modello restituisce una stringa vuota
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