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

REGOLE CRITICHE:
1. FUSI ORARI E TENNIS (es. Indian Wells, Miami): In USA il fuso orario è indietro di 9/6 ore. DEVI calcolare l'orario italiano esatto (CET/CEST). Se dicono "inizio programma alle 19:00", NON assegnare le 19:00 a tutti i giocatori. Se l'orario esatto del match di un italiano non è noto, inserisci "TBA" o un orario stimato.
2. REGGINA E SERIE MINORI: I comunicati della Serie D spesso accorpano più giorni. Per inserire una partita della Reggina, devi avere la CERTEZZA ASSOLUTA che si giochi OGGI ({date_str}). Se trovi articoli che parlano di partite già giocate nel weekend o riassunti, IGNORALE.

Novità: Per gli eventi in notturna, includi anche gli orari delle repliche diurne sui canali principali (es. Sky Sport) in una riga separata o nelle note.

Categorie target (INCLUDI):
- Calcio: Serie A; Champions League / Europa League / Conference League con squadre italiane; Serie D per Reggina (SOLO SE GIOCA ESATTAMENTE OGGI)
- Tennis: SOLO match ATP/WTA che includono ALMENO UN GIOCATORE ITALIANO. Se non ci sono italiani in campo, IGNORA IL MATCH.
- Formula 1 (Gare, Qualifiche, Prove + Repliche diurne)
- MotoGP (Gare, Qualifiche, Sprint + Repliche diurne)
- Volley: SOLO PARTITE DEL MONZA (Vero Volley / Mint Monza). Ignora le altre.
- Sci Alpino (Federica Brignone o Sofia Goggia)

Categorie da ESCLUDERE esplicitamente:
- Qualsiasi "Serie C", Calcio a 5 / futsal
- Qualsiasi partita di volley senza il Monza.
- Qualsiasi partita di tennis senza italiani.
- Partite della Reggina o di Serie D già disputate in giorni precedenti.

Requisiti:
- Tutti gli orari in CET (Italiano).
- Output: restituisci ESCLUSIVAMENTE un array JSON valido.
- Campi obbligatori per ogni oggetto (usa null o "" se assenti):
  "orario": stringa,
  "evento": stringa,
  "competizione": stringa,
  "canale": stringa,
  "note": stringa,
  "fonte": stringa (URL della notizia da cui hai preso l'info, se disponibile),
  "accuratezza_orario": stringa (usa SOLO "esatto", "stimato" oppure "tba")
"""

# Lista di giocatori italiani noti da usare nel filtro Python
ITALIAN_TENNIS_PLAYERS = [
    "sinner", "musetti", "berrettini", "paolini", "errani", 
    "cobolli", "arnaldi", "sonego", "bolelli", "vavassori",
    "darderi", "nardi", "fognini", "bronzetti", "trevisan",
    "cocciaretto", "giorgi", "bronzi"
]

def should_exclude(item: dict) -> bool:
    blob = f"{item.get('competizione','')} {item.get('evento','')} {item.get('note','')}".lower()
    
    futsal_markers = ["calcio a 5", "futsal", "a2 elite", "divisione calcio a 5"]
    if "serie c" in blob or any(m in blob for m in futsal_markers):
        return True
        
    if "volley" in blob or "pallavolo" in blob or "superlega" in blob:
        if "monza" not in blob and "mint" not in blob and "vero" not in blob:
            return True
            
    if "atp" in blob or "wta" in blob or "tennis" in blob:
        if " vs " in blob or " vs. " in blob or " contro " in blob or "-" in item.get('evento',''):
            has_italian = any(player in blob for player in ITALIAN_TENNIS_PLAYERS)
            is_generic_broadcast = any(word in blob for word in ["diretta", "rubrica", "studio", "highlights", "magazine"])
            if not has_italian and not is_generic_broadcast:
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
        
    # Salva il file includendo il timestamp dell'aggiornamento e gli eventi
    final_data = {
        "last_updated": datetime.datetime.now(rome_tz).isoformat(),
        "events": events
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("Dati aggiornati con successo!")
except Exception as e:
    print("Si è verificato un errore durante l'esecuzione.")
    try:
        print("Risposta parziale:", response.text)
    except Exception:
        pass
    print("Dettaglio errore:", e)
    raise SystemExit(1)
