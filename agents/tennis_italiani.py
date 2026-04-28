import os
import json
import datetime
import pytz
from google import genai
from google.genai import types

OUTPUT_FILE = "data/tennis.json"

rome_tz = pytz.timezone("Europe/Rome")
now = datetime.datetime.now(rome_tz)
date_str = now.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

prompt = f"""
Obiettivo: FAI UNA RICERCA SUL WEB e compila una lista di match di tennis in TV per OGGI ({date_str}) e fino alle 06:00 (CET) del giorno successivo.

REGOLE CRITICHE:
1. FUSI ORARI (specialmente USA - Indian Wells, Miami): In USA il fuso è indietro di 9 ore (EST) o 6 (PDT). Calcola l'orario italiano esatto.
2. ACCURATEZZA: Se l'orario dipende da match precedenti, usa "TBA" o stimato con asterisco.

GIOCATORI ITALIANI DA CERCARE (ATP):
- Jannik Sinner, Lorenzo Musetti, Matteo Berrettini, Flavio Cobolli, Luca Nardi, Francesco Passaro, Matteo Arnaldi, Lorenzo Sonego, Simone Bolelli, Andrea Vavassori, Fabian Bertasio, Federico Araldi

GIOCATRICI ITALIANE (WTA):
- Jasmine Paolini, Martina Trevisan, Lucia Bracciale, Cristina Ferrando, Matilde Mariani, Aurora Zantedeschina, Bianca Baulk, Angelica Raggi

INCLUDE SOLO match che coinvolgono almeno un giocatore italiano. Escludi:
- Rubriche, highlights, programmi studio, magazine
- Solo match senza italiani

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

ITALIAN_PLAYERS = [
    "sinner", "musetti", "berrettini", "paolini", "errani",
    "cobolli", "arnaldi", "sonego", "bolelli", "vavassori",
    "nardi", "passaro", "fognini", "bronzetti", "trevisan",
    "cocciaretto", "giorgi", "bracciale", "ferrando", "zantedeschina"
]

def should_exclude(item: dict) -> bool:
    blob = f"{item.get('competizione','')} {item.get('evento','')} {item.get('note','')}".lower()
    
    generic_markers = ["rubrica", "studio", "highlights", "magazine", "diretta tv", "speciale", "vela"]
    if any(m in blob for m in generic_markers):
        return True
    
    has_italian = any(player in blob for player in ITALIAN_PLAYERS)
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
        "agent": "tennis_italiani",
        "events": events
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"Dati Tennis italiani aggiornati! Eventi: {len(events)}")
except Exception as e:
    print("Errore:", e)
    raise SystemExit(1)