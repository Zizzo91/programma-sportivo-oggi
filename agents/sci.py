import os
import json
import datetime
import pytz
from google import genai
from google.genai import types

OUTPUT_FILE = "data/sci.json"

rome_tz = pytz.timezone("Europe/Rome")
now = datetime.datetime.now(rome_tz)
date_str = now.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

prompt = f"""
Obiettivo: FAI UNA RICERCA SUL WEB e compila una lista di eventi di sci alpino in TV per OGGI ({date_str}) e fino alle 06:00 (CET) del giorno successivo.

ATLETE ITALIANE DA CERCARE:
- Federica Brignone
- Sofia Goggia
- Marta Bassino
- Luca Dallago
- Christof Innerhofer
- Dominik Paris

INCLUDE SOLO eventi che coinvolgono almeno un atleta italiano. Escludi:
- Rubriche, highlights, magazine, programmi studio
- Sci non alpino (fondo, salto, etc)

REGOLE:
1. FUSI ORARI: Calcola l'orario italiano esatto (CET/CEST).
2. ACCURATEZZA: Se l'orario non è ancora noto, usa "TBA" o stimato con asterisco.

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

ITALIAN_SKIERS = [
    "brignone", "goggia", "bassino", "dallago", "innerhofer", "paris",
    "luca davide", "simone", "fabio", "giovanni", "pier", "marco"
]

def should_exclude(item: dict) -> bool:
    blob = f"{item.get('competizione','')} {item.get('evento','')} {item.get('note','')}".lower()
    
    generic_markers = ["rubrica", "studio", "highlights", "magazine", "vela", "classifica", "analisi"]
    if any(m in blob for m in generic_markers):
        return True
    
    has_italian = any(skier in blob for skier in ITALIAN_SKIERS)
    if not has_italian:
        return True
    
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

    data = json.loads(result_text)

    events = []
    if isinstance(data, list):
        events = [x for x in data if isinstance(x, dict) and not should_exclude(x)]

    final_data = {
        "last_updated": datetime.datetime.now(rome_tz).isoformat(),
        "agent": "sci",
        "events": events
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"Dati Sci aggiornati! Eventi: {len(events)}")
except Exception as e:
    print("Errore:", e)
    raise SystemExit(1)