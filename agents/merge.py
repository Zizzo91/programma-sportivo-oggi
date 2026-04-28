import os
import json
import glob

DATA_DIR = "data"
OUTPUT_FILE = "data.json"

def should_exclude_final(item: dict) -> bool:
    blob = f"{item.get('competizione','')} {item.get('evento','')} {item.get('note','')}".lower()
    
    futsal_markers = ["calcio a 5", "futsal", "a2 elite", "divisione calcio a 5"]
    if "serie c" in blob or any(m in blob for m in futsal_markers):
        return True
    if "volley" in blob or "pallavolo" in blob or "superlega" in blob:
        if "monza" not in blob and "mint" not in blob and "vero" not in blob:
            return True
    if "atp" in blob or "wta" in blob or "tennis" in blob:
        if " vs " in blob or " vs. " in blob or " contro " in blob or "-" in item.get('evento',''):
            italian_tennis = ["sinner", "musetti", "berrettini", "paolini", "errani", "cobolli", "arnaldi", "sonego", "bolelli", "vavassori", "nardi", "passaro", "fognini", "bronzetti", "trevisan", "cocciaretto", "giorgi", "bracciale", "ferrando", "zantedeschina"]
            has_italian = any(p in blob for p in italian_tennis)
            is_generic = any(w in blob for w in ["rubrica", "studio", "highlights", "magazine", "diretta"])
            if not has_italian and not is_generic:
                return True
    return False

def merge_all():
    all_events = []
    json_files = sorted(glob.glob(f"{DATA_DIR}/*.json"))
    
    print(f"Trovati {len(json_files)} file da mergiare...")
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        if filename == OUTPUT_FILE:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = data.get("events", [])
            agent_name = data.get("agent", filename.replace(".json", ""))
            print(f"  {agent_name}: {len(events)} eventi")
            for event in events:
                if not should_exclude_final(event):
                    all_events.append(event)
        except Exception as e:
            print(f"  Errore lettura {filename}: {e}")
    
    all_events.sort(key=lambda x: x.get("orario", "00:00"))
    
    final_data = {
        "last_updated": all_events[0].get("last_updated", "") if all_events else "",
        "events": all_events
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Merge completato! Totale eventi: {len(all_events)}")

if __name__ == "__main__":
    merge_all()