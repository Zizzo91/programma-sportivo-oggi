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
1. Obiettivo: Trova e compila una lista di eventi sportivi italiani in TV per la data {date_str}. 
Categorie target: Calcio (Serie A, Champions League/Europa/Conference League con squadre italiane, Serie C per Monza e Catanzaro, Serie D per Reggina), Tennis (ATP/WTA tornei con giocatori italiani come Sinner, Musetti, Berrettini, Paolini, ecc.), Formula 1, MotoGP, Volley (partite di Monza), e Sci Alpino (Federica Brignone o Sofia Goggia).
Tutti gli orari devono essere convertiti e mostrati in CET. Includi anche eventi della notte fonda se fanno parte del palinsesto di oggi.

2. Formato di output: Rispondi ESCLUSIVAMENTE con un array JSON valido, senza blocchi markdown (no ```json). 
I campi per ogni oggetto devono essere esattamente: "orario", "evento", "competizione", "canale", "note".
Se non ci sono eventi in programma, restituisci un array vuoto: []
"""

model = genai.GenerativeModel('gemini-1.5-pro')
response = model.generate_content(prompt)

try:
    result_text = response.text.strip()
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]
    
    data = json.loads(result_text.strip())
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Dati aggiornati con successo!")
except Exception as e:
    print(f"Errore nel JSON. Risposta grezza:\\n{response.text}")
    print(f"Errore: {e}")
    exit(1)
