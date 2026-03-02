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
1. FUSI ORARI E TENNIS (es. Indian Wells, Miami): In USA il fuso orario è indietro di 9/6 ore. DEVI calcolare l'orario italiano esatto (CET/CEST). Se dicono "inizio programma alle 19:00", NON assegnare le 19:00 a tutti i giocatori. Se l'orario esatto del match di un italiano non è noto, inserisci "TBA" o un orario stimato con nota esplicita (es. "Dipende dal match precedente").
2. REGGINA E SERIE MINORI: I comunicati della Serie D spesso accorpano più giorni. Per inserire una partita della Reggina, devi avere la CERTEZZA ASSOLUTA che si giochi OGGI ({date_str}). Se trovi articoli che parlano di partite già giocate nel weekend (es. anticipi del sabato/domenica) o stai leggendo un riassunto di giornate precedenti, IGNORALE totalmente. Non confondere l'orario del "Monday Night" di altre squadre con la Reggina.

Novità: Per gli eventi in notturna (es. MotoGP, Formula 1, Tennis), includi anche gli orari delle repliche diurne sui canali principali (es. Sky Sport) in una riga separata o nelle note.

Categorie target (INCLUDI):
- Calcio: Serie A; Champions League / Europa League / Conference League con squadre italiane; Serie D per Reggina (SOLO SE GIOCA ESATTAMENTE OGGI)
- Tennis: SOLO match ATP/WTA che includono ALMENO UN GIOCATORE ITALIANO (es. Sinner, Musetti, Berrettini, Paolini, Errani, ecc.). Se non ci sono italiani in campo, IGNORA IL MATCH.
- Formula 1 (Gare, Qualifiche, Prove + Repliche diurne)
- MotoGP (Gare, Qualifiche, Sprint + Repliche diurne)
- Volley: SOLO PARTITE DEL MONZA (Vero Volley / Mint Monza). Ignora le altre squadre.
- Sci Alpino (Federica Brignone o Sofia Goggia)

Categorie da ESCLUDERE esplicitamente:
- Qualsiasi "Serie C"
- Calcio a 5 / futsal (Serie A, A2, A2 Elite, ecc.)
- Qualsiasi partita di volley che NON riguardi il Monza.
- Qualsiasi partita di tennis che NON includa giocatori italiani.
- Partite della Reggina o di Serie D già disputate in giorni precedenti.

Requisiti:
- Tutti gli orari in CET (Italiano).
- Output: restituisci ESCLUSIVAMENTE un array JSON valido (no markdown).
- Campi per ogni oggetto: "orario", "evento", "competizione", "canale", "note".
- Se non ci sono eventi: []
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
    
    # Filtro Futsal e Serie C
    futsal_markers = ["calcio a 5", "futsal", "a2 elite", "divisione calcio a 5"]
    if "serie c" in blob:
        return True
    if any(m in blob for m in futsal_markers):
        return True
        
    # Filtro Volley: deve esserci 'monza' (o varianti sponsorizzate)
    if "volley" in blob or "pallavolo" in blob or "superlega" in blob:
        if "monza" not in blob and "mint" not in blob and "vero" not in blob:
            return True
            
    # Filtro Tennis: deve esserci almeno un giocatore italiano se è un match specifico
    if "atp" in blob or "wta" in blob or "tennis" in blob:
        # Se è un riepilogo generico tipo "Diretta Torneo ATP", lo teniamo. 
        # Ma se contiene la parola "vs" o "contro" (indica un match specifico), verifichiamo i nomi
        if " vs " in blob or " vs. " in blob or " contro " in blob or "-" in item.get('evento',''):
            has_italian = any(player in blob for player in ITALIAN_TENNIS_PLAYERS)
            # Parole chiave che indicano una trasmissione generica e non un singolo match
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