import os
import json
import datetime
import pytz
from google import genai
from google.genai import types

rome_tz = pytz.timezone("Europe/Rome")
now = datetime.datetime.now(rome_tz)
date_str = now.strftime("%Y-%m-%d")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY non trovata nelle Github Secrets.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

prompt = f"""
Obiettivo: FAI UNA RICERCA SUL WEB e compila una lista di eventi sportivi italiani in TV per OGGI ({date_str}) e includi anche gli eventi fino alle 06:00 (CET) del giorno successivo, se considerati parte del palinsesto notturno.

Categorie target (INCLUDI):
- Calcio: Serie A; Champions League / Europa League / Conference League con squadre italiane; Serie D per Reggina
- Tennis: ATP/WTA con italiani (Sinner, Musetti, Berrettini, Paolini, ecc.)
- Formula 1
- MotoGP
- Volley (Monza)
- Sci Alpino (Federica Brignone o Sofia Goggia)

Categorie da ESCLUDERE esplicitamente:
- Qualsiasi "Serie C"
- Calcio a 5 / futsal (Serie A, A2, A2 Elite, ecc.)

Requisiti:
- Tutti gli orari in CET.
- Output: restituisci ESCLUSIVAMENTE un array JSON valido (no markdown).
- Campi per ogni oggetto: "orario", "evento", "competizione", "canale", "note".
- Se non ci sono eventi: []
"""

def should_exclude(item: dict) -> bool:
    blob = f"{item.get('competizione','')} {item.get('evento','')} {item.get('note','')}".lower()
    futsal_markers = ["calcio a 5", "futsal", "a2 elite", "divisione calcio a 5"]
    if "serie c" in blob:
        return True
    if any(m in blob for m in futsal_markers):
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

    # strip eventuali fence
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    elif result_text.startswith("```"):
        result_text = result_text[3:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]
    result_text = result_text.strip() or "[]"

    data = json.loads(result_text)

    # post-filter di sicurezza
    if isinstance(data, list):
        data = [x for x in data if isinstance(x, dict) and not should_exclude(x)]
    else:
        data = []

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Dati aggiornati con successo!")
except Exception as e:
    print("Si è verificato un errore durante l'esecuzione.")
    try:
        print("Risposta parziale:", response.text)
    except Exception:
        pass
    print("Dettaglio errore:", e)
    raise SystemExit(1)
