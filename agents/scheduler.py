import os
import sys
import datetime
import pytz

rome_tz = pytz.timezone("Europe/Rome")
now = datetime.datetime.now(rome_tz)
hour = now.hour

AGENTS_SEQUENCE = [
    ("f1", "agents/f1.py"),
    ("motogp", "agents/motogp.py"),
    ("serie_a", "agents/serie_a.py"),
    ("champions", "agents/champions_league.py"),
    ("europa", "agents/europa_league.py"),
    ("conference", "agents/conference_league.py"),
    ("tennis", "agents/tennis_italiani.py"),
    ("sci", "agents/sci.py"),
    ("merge", "agents/merge.py"),
]

agent_index = hour % 9
agent_name, agent_script = AGENTS_SEQUENCE[agent_index]

print(f"Ora: {hour:02d}:00 -> Eseguo agente #{agent_index}: {agent_name}")

if agent_name == "merge":
    os.system(f"python {agent_script}")
else:
    os.system(f"python {agent_script}")