"""
import_2026_stats.py
-------------------
Reads the 2026 season CSV from the Barons Stats folder and writes a fresh
ct_barons_stats.csv in the two-section format expected by barons_dashboard.py.
Also resets game_logs.csv to just its header row.

Run from any directory:
    python3 /Users/chrisjones/Desktop/ct_barons_app/import_2026_stats.py
"""

import csv
import os
import math

# ── Paths ────────────────────────────────────────────────────────────────────
APP_DIR      = "/Users/chrisjones/Desktop/ct_barons_app"
SOURCE_CSV   = "/Users/chrisjones/Desktop/Barons Stats/CT Barons South 18O Summer 2026 Stats.csv"
OUT_STATS    = os.path.join(APP_DIR, "ct_barons_stats.csv")
OUT_LOGS     = os.path.join(APP_DIR, "game_logs.csv")

# ── Roster / Position map ────────────────────────────────────────────────────
PLAYERS = {
    "James Aselta":    "P",
    "Timmy Domizio":   "UTIL",
    "Henry Silvia":    "UTIL",
    "Jack Farnen":     "OF",
    "Oliver Merced":   "1B",
    "Stephen Polizzi": "C",
    "Nick Carlucci":   "OF",
    "Nevin Belanger":  "P",
    "Tommy Farrell":   "P",
    "Colin Donofrio":  "P",
    "Chris Keating":   "P",
    "Liam DaSilva":    "C/1B",
    "Brett Davino":    "UTIL",
    "Nick Dorso":      "UTIL",
    "Brandon Skerritt":"C",
    "Nick Petta":      "P",
}

# Name fixes from CSV "First Last" → canonical display name
NAME_FIXES = {
    "Steve Polizzi": "Stephen Polizzi",
    "Henry Silvia":  "Henry Silvia",   # CSV spells it "Silvia" — same as roster
}

# ── Column indices (0-based) ──────────────────────────────────────────────────
COL_NUMBER  = 0
COL_LAST    = 1
COL_FIRST   = 2

# Batting
COL_GP_bat  = 3
COL_PA      = 4
COL_AB      = 5
COL_H       = 10
COL_2B      = 12
COL_3B      = 13
COL_HR_bat  = 14
COL_RBI     = 15
COL_R_bat   = 16
COL_BB_bat  = 17
COL_SO_bat  = 18
COL_HBP_bat = 20
COL_SF      = 22
COL_SB      = 25

# Pitching
COL_IP      = 54
COL_W       = 59
COL_L       = 60
COL_SV      = 61
COL_H_pit   = 65
COL_R_pit   = 66
COL_ER      = 67
COL_BB_pit  = 68
COL_SO_pit  = 69
COL_HBP_pit = 71
COL_ERA     = 72
COL_HR_pit  = 112


# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_float(val):
    try:
        return float(str(val).strip().replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0

def safe_int(val):
    return int(safe_float(val))

def compute_hitting_metrics(AB, H, _2B, _3B, HR, BB, HBP, SF, SB, K, RBI, PA):
    """Return dict of derived hitting stats."""
    singles = H - _2B - _3B - HR
    TB = singles + 2*_2B + 3*_3B + 4*HR

    AVG  = H / AB    if AB > 0 else 0.0
    OBP  = (H + BB + HBP) / PA if PA > 0 else 0.0
    SLG  = TB / AB   if AB > 0 else 0.0
    OPS  = OBP + SLG

    woba_num = (
        0.69  * BB +
        0.72  * HBP +
        0.88  * singles +
        1.247 * _2B +
        1.578 * _3B +
        2.031 * HR
    )
    wOBA = woba_num / PA if PA > 0 else 0.0
    K_pct  = K  / PA if PA > 0 else 0.0
    BB_pct = BB / PA if PA > 0 else 0.0

    return dict(AVG=AVG, OBP=OBP, SLG=SLG, OPS=OPS,
                wOBA=wOBA, Kpct=K_pct, BBpct=BB_pct)

def compute_pitching_metrics(IP, ER, SO, BB, HR):
    """Return ERA and FIP."""
    ERA = (ER * 9) / IP if IP > 0 else 0.0
    FIP = ((13*HR + 3*BB - 2*SO) / IP + 3.1) if IP > 0 else 0.0
    return ERA, FIP


# ── Parse source CSV ──────────────────────────────────────────────────────────

with open(SOURCE_CSV, encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    all_rows = list(reader)

# Row 0: section header (Batting / Pitching / Fielding)
# Row 1: column names
# Row 2+: player data (skip "Totals" and "Glossary" rows)

hitter_rows  = []
pitcher_rows = []

for row in all_rows[2:]:
    if not row or not row[COL_NUMBER].strip():
        continue
    # Skip aggregate rows
    num_cell = row[COL_NUMBER].strip()
    if num_cell.lower() in ("totals", "glossary", ""):
        continue
    try:
        int(num_cell)
    except ValueError:
        continue

    # Build canonical name
    first = row[COL_FIRST].strip()
    last  = row[COL_LAST].strip()
    raw_name = f"{first} {last}"
    canon_name = NAME_FIXES.get(raw_name, raw_name)
    pos = PLAYERS.get(canon_name, "UTIL")

    # ── Batting ──────────────────────────────────────────────────────────────
    PA      = safe_int(row[COL_PA])
    AB      = safe_int(row[COL_AB])
    H       = safe_int(row[COL_H])
    _2B     = safe_int(row[COL_2B])
    _3B     = safe_int(row[COL_3B])
    HR_bat  = safe_int(row[COL_HR_bat])
    RBI     = safe_int(row[COL_RBI])
    R_bat   = safe_int(row[COL_R_bat])
    BB_bat  = safe_int(row[COL_BB_bat])
    K_bat   = safe_int(row[COL_SO_bat])
    HBP_bat = safe_int(row[COL_HBP_bat])
    SF      = safe_int(row[COL_SF])
    SB      = safe_int(row[COL_SB])

    metrics = compute_hitting_metrics(AB, H, _2B, _3B, HR_bat, BB_bat, HBP_bat, SF, SB, K_bat, RBI, PA)

    hitter_rows.append({
        "Name":  canon_name,
        "Pos":   pos,
        "PA":    PA,
        "AB":    AB,
        "H":     H,
        "2B":    _2B,
        "3B":    _3B,
        "HR":    HR_bat,
        "RBI":   RBI,
        "BB":    BB_bat,
        "K":     K_bat,
        "HBP":   HBP_bat,
        "SF":    SF,
        "SB":    SB,
        "AVG":   metrics["AVG"],
        "OBP":   metrics["OBP"],
        "SLG":   metrics["SLG"],
        "OPS":   metrics["OPS"],
        "wOBA":  metrics["wOBA"],
        "K%":    metrics["Kpct"],
        "BB%":   metrics["BBpct"],
    })

    # ── Pitching ─────────────────────────────────────────────────────────────
    IP      = safe_float(row[COL_IP])
    W       = safe_int(row[COL_W])
    L       = safe_int(row[COL_L])
    SV      = safe_int(row[COL_SV])
    H_pit   = safe_int(row[COL_H_pit])
    R_pit   = safe_int(row[COL_R_pit])
    ER      = safe_int(row[COL_ER])
    BB_pit  = safe_int(row[COL_BB_pit])
    SO_pit  = safe_int(row[COL_SO_pit])
    HBP_pit = safe_int(row[COL_HBP_pit])
    HR_pit  = safe_int(row[COL_HR_pit])

    ERA, FIP = compute_pitching_metrics(IP, ER, SO_pit, BB_pit, HR_pit)

    pitcher_rows.append({
        "Name":   canon_name,
        "Pos":    pos,
        "IP":     IP,
        "W":      W,
        "L":      L,
        "SV":     SV,
        "R":      R_pit,
        "ER":     ER,
        "SO":     SO_pit,
        "BB_p":   BB_pit,
        "HR_p":   HR_pit,
        "HBP_p":  HBP_pit,
        "ERA":    ERA,
        "FIP":    FIP,
    })


# ── Write ct_barons_stats.csv ─────────────────────────────────────────────────

HITTER_COLS = [
    "Name","Pos","PA","AB","H","2B","3B","HR","RBI",
    "BB","K","HBP","SF","SB",
    "AVG","OBP","SLG","OPS","wOBA","K%","BB%",
]

PITCHER_COLS = [
    "Name","Pos","IP","W","L","SV",
    "R","ER","SO","BB_p","HR_p","HBP_p",
    "ERA","FIP",
]

with open(OUT_STATS, "w", newline="") as f:
    f.write("=== HITTERS ===\n")
    writer = csv.DictWriter(f, fieldnames=HITTER_COLS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(hitter_rows)
    f.write("\n=== PITCHERS ===\n")
    writer = csv.DictWriter(f, fieldnames=PITCHER_COLS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(pitcher_rows)

print(f"Wrote {len(hitter_rows)} hitter rows and {len(pitcher_rows)} pitcher rows to {OUT_STATS}")


# ── Reset game_logs.csv to header only ───────────────────────────────────────

LOG_COLS = [
    "Date","Opponent","LeagueGame","Player","Type",
    # Hitting
    "AB","H","2B","3B","HR","RBI",
    "BB","K","HBP","SF","SB","PA",
    # Pitching
    "IP","W","L","SV","R","ER","SO",
    "BB_p","HR_p","HBP_p",
]

with open(OUT_LOGS, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=LOG_COLS)
    writer.writeheader()

print(f"Reset {OUT_LOGS} to header only.")
print("Done.")
