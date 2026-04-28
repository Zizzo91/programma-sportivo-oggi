import os
import json
import datetime
import pytz
from google import genai
from google.genai import types

OUTPUT_FILE = "data/motogp.json"

rome_tz = pytz.timezone("Europe/Rome")
now = datetime.datetime.now(rome_tz)
date_str = now.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

prompt = f"""
Obiettivo: FAI UNA RICERCA SUL WEB e compila una lista di eventi di MotoGP in TV per OGGI ({date_str}) e fino alle 06:00 (CET) del giorno successivo.

REGOLE CRITICHE:
1. FUSI ORARI: Le gare/qualifiche in altri fusi orari. Calcola l'orario italiano esatto (CET/CEST).
2. ACCURATEZZA: Se l'orario non è ancora noto, usa "TBA". Se è stimato usa un asterisco (es. "14:00*").
3. REPLICHE: Inserisci come eventi SEPARATI tutte le repliche/differite delle sessioni (gara, sprint, qualifiche) trasmesse in giornata (fascia 08:00-20:00). Specifica l'orario esatto.

Categorie da includere:
- Gara (main race)
- Sprint
- Qualifiche
- Prove_libere
- Warm-up
- Repliche/differite

Format output:
- Restituisci ESCLUSIVAMENTE un array JSON valido (no markdown).
- Campi obbligatori:
  "orario": stringa,
  "evento": stringa,
  "competizione": stringa,
  "canale": stringa,
  "note": stringa,
  "fonte": stringa,
  "accuratezza_orario": "esatto" | "stimato" | "tba"
- Se nessun evento: []
"""

def should_exclude(item: dict) -> bool:
    return False

try:
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )

    result_text = (response.text or "").strip()
    if result_text.startswith("```json"): result_text = result_text[7:]
    elif result_text.startswith("```"): result_text = result_text[3:]
    if result_text.endswith("```"): result_text = result_text[:-3]
    result_text = result_text.strip() or "[]"

    try:
        data = json.loads(result_text)
    except json.JSONDecodeError:
        print("Risposta non JSON, tento di pulire...")
        import re
        match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            data = []

    events = []
    if isinstance(data, list):
        events = [x for x in data if isinstance(x, dict)]

    final_data = {
        "last_updated": datetime.datetime.now(rome_tz).isoformat(),
        "agent": "motogp",
        "events": events
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"Dati MotoGP aggiornati! Eventi: {len(events)}")
except Exception as e:
    print("Errore:", e)
    raise SystemExit(1)