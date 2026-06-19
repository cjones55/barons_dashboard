import streamlit as st
import pandas as pd
import os
import json
import html
from io import StringIO
from PIL import Image
import base64

# ============================
# CONFIG
# ============================

CUMULATIVE_FILE = "ct_barons_stats.csv"
MASTER_LOG_FILE = "game_logs.csv"
GAME_LOG_DIR = "logs"
DEPTH_CHART_FILE = "depth_chart_ideas.json"
COACH_PASSWORD = "jonesy34"

os.makedirs(GAME_LOG_DIR, exist_ok=True)

st.set_page_config(page_title="CT Barons South", layout="wide")

# ============================
# THEME CSS (Orioles / Barons)
# ============================

def inject_css(css: str):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_css("""
/* GLOBAL BACKGROUND */
body, .stApp {
    background-color: #000000 !important;
    color: #FFFFFF !important;
}

/* HEADERS */
h1, h2, h3, h4 {
    color: #FF6F00 !important;
    font-weight: 800;
}

/* TABS */
.stTabs [data-baseweb="tab"] {
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 600;
    border: 1px solid #333333;
}

.stTabs [aria-selected="true"] {
    background-color: #FF6F00 !important;
    color: #000000 !important;
    border: 1px solid #FF6F00 !important;
}

/* BUTTONS */
.stButton>button {
    background-color: #FF6F00 !important;
    color: #000000 !important;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 700;
    border: none;
}

.stButton>button:hover {
    background-color: #FFA040 !important;
    color: #000000 !important;
}

/* DATAFRAME HEADERS */
.dataframe th {
    background-color: #FF6F00 !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

/* DATAFRAME CELLS */
.dataframe td {
    background-color: #111111 !important;
    color: #FFFFFF !important;
    border-color: #333333 !important;
}

/* INPUTS */
input, select, textarea {
    background-color: #222222 !important;
    color: #FFFFFF !important;
    border: 1px solid #FF6F00 !important;
    border-radius: 4px !important;
}
""")


def html_to_pdf_download_button(html_content, filename="game_report.pdf"):
    """
    Convert HTML to a downloadable PDF using base64 encoding.
    Works on Streamlit Cloud without external dependencies.
    """
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Download Game Report PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Run cleaner BEFORE anything else touches the log
    clean_master_log()



# ============================
# CENTERED LOGO HEADER
# ============================

st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.image("barons_logo.png", width=150)
st.markdown(
    """
    <h1 style="color:#FF6F00; font-weight:900; margin-top:10px; text-align:center;">
        CT BARONS SOUTH BASEBALL
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)




def clean_master_log():
    if not os.path.exists(MASTER_LOG_FILE):
        return

    # Step 1 — read file even if malformed
    df = pd.read_csv(MASTER_LOG_FILE, on_bad_lines="skip", engine="python")

    # Step 2 — unify column schema
    required_cols = [
        "Date", "Opponent", "LeagueGame", "Player", "Type",

        # Hitting
        "AB", "H", "2B", "3B", "HR", "RBI",
        "BB", "K", "HBP", "SF", "SB",
        "PA",

        # Pitching
        "IP", "W", "L", "SV", "R", "ER", "SO",
        "BB_p", "HR_p", "HBP_p",
    ]

    # Add any missing columns
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    # Step 3 — drop any extra garbage columns
    df = df[required_cols]

    # Step 4 — rewrite clean file
    df.to_csv(MASTER_LOG_FILE, index=False)



# ============================
# TEAM RECORD HELPERS
# ============================

TEAM_RECORD_FILE = "team_record.csv"

def load_team_record():
    if not os.path.exists(TEAM_RECORD_FILE):
        return {"Wins": 0, "Losses": 0}
    df = pd.read_csv(TEAM_RECORD_FILE)
    return {"Wins": int(df.loc[0, "Wins"]), "Losses": int(df.loc[0, "Losses"])}

def save_team_record(wins, losses):
    df = pd.DataFrame([{"Wins": wins, "Losses": losses}])
    df.to_csv(TEAM_RECORD_FILE, index=False)


def load_depth_chart_ideas():
    if not os.path.exists(DEPTH_CHART_FILE):
        return {}

    try:
        with open(DEPTH_CHART_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_depth_chart_ideas(ideas):
    with open(DEPTH_CHART_FILE, "w") as f:
        json.dump(ideas, f, indent=2)


record = load_team_record()
st.markdown(
    f"""
    <h3 style="text-align:center; color:#FFA040; margin-top:-10px;">
        Current Record: {record['Wins']}-{record['Losses']}
    </h3>
    """,
    unsafe_allow_html=True
)


# ============================
# ROSTER
# ============================

PLAYERS = {
    "James Aselta":      "P",
    "Timmy Domizio":     "UTIL",
    "Henry Silvia":      "UTIL",
    "Jack Farnen":       "OF",
    "Oliver Merced":     "1B",
    "Stephen Polizzi":   "C",
    "Nick Carlucci":     "OF",
    "Nevin Belanger":    "P",
    "Tommy Farrell":     "P",
    "Colin Donofrio":    "P",
    "Chris Keating":     "P",
    "Liam DaSilva":      "C/1B",
    "Brett Davino":      "UTIL",
    "Nick Dorso":        "UTIL",
    "Brandon Skerritt":  "C/OF",
    "Nick Petta":        "P",
    "Joel Strand":       "C",
    "Patrick Leonard":   "OF",
    "Christian Barboto": "P",
    "Nick Hios":         "P",
    "Tristian Pearl":    "P",
    "Mike Fischetti":    "OF",
    "Aidan O'Loughin":   "OF",
    "Mason Kuckinski":   "UTIL",
    "Antonio Galizia":   "1B",
    "Charlie Ellis":     "1B",
    "Jack Jensen":       "P",
    "Merritt Hole":      "P",
    "Mo Hood":           "UTIL",
    "Owen Staller":      "OF",
}

DISPLAY_TO_CSV_NAME = {}

CSV_NAME_TO_POS = {name: pos for name, pos in PLAYERS.items()}

# ============================
# SESSION STATE
# ============================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ============================
# CUMULATIVE STATS HELPERS
# ============================

def compute_team_pitching_totals(df, league_filter=None):
    if df is None or df.empty:
        return None

    df = df[df["Type"] == "P"]
    if league_filter is not None:
        df = df[df["LeagueGame"] == (1 if league_filter else 0)]
    if df.empty:
        return None

    for col in ["BB_p", "HR_p", "HBP_p", "W", "L", "SV"]:
        if col not in df.columns:
            df[col] = 0
    agg = df[["IP", "R", "ER", "SO", "BB_p", "HR_p", "HBP_p", "W", "L", "SV"]].sum()

    IP   = agg["IP"]
    R    = agg["R"]
    ER   = agg["ER"]
    SO   = agg["SO"]
    BB_p = agg["BB_p"]
    HBP_p = agg["HBP_p"]
    HR_p = agg["HR_p"]
    W    = int(agg["W"])
    L    = int(agg["L"])
    SV   = int(agg["SV"])

    ERA = (ER * 9) / IP if IP > 0 else 0
    FIP = ((13 * HR_p) + (3 * (BB_p + HBP_p)) - (2 * SO)) / IP + 3.1 if IP > 0 else 0
    Unearned = R - ER

    return {
        "IP": IP, "W": W, "L": L, "SV": SV,
        "R": R, "ER": ER, "Unearned": Unearned,
        "SO": SO, "BB": BB_p, "HR": HR_p,
        "ERA": ERA, "FIP": FIP
    }


def compute_team_hitting_totals(df, league_filter=None):
    if df is None or df.empty:
        return None

    df = df[df["Type"] == "H"]
    if league_filter is not None:
        df = df[df["LeagueGame"] == (1 if league_filter else 0)]
    if df.empty:
        return None

    # Ensure PA exists (older logs won't have it)
    if "PA" not in df.columns:
        df["PA"] = df["AB"] + df["BB"] + df["HBP"] + df["SF"]

    # Ensure all required columns exist
    required_cols = ["AB","H","2B","3B","HR","BB","K","HBP","SF","SB","PA","RBI"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    agg = df[required_cols].sum()

    AB  = agg["AB"]
    H   = agg["H"]
    _2B = agg["2B"]
    _3B = agg["3B"]
    HR  = agg["HR"]
    BB  = agg["BB"]
    K   = agg["K"]
    HBP = agg["HBP"]
    SF  = agg["SF"]
    SB  = agg["SB"]
    PA  = agg["PA"]
    RBI = int(agg["RBI"])

    AVG  = H / AB if AB > 0 else 0
    OBP  = (H + BB + HBP) / PA if PA > 0 else 0
    singles = H - _2B - _3B - HR
    TB   = singles + 2*_2B + 3*_3B + 4*HR
    SLG  = TB / AB if AB > 0 else 0
    OPS  = OBP + SLG
    woba_num = (
        0.69*BB + 0.72*HBP + 0.88*singles +
        1.247*_2B + 1.578*_3B + 2.031*HR
    )
    wOBA   = woba_num / PA if PA > 0 else 0
    K_pct  = K / PA if PA > 0 else 0
    BB_pct = BB / PA if PA > 0 else 0
    babip_denom = AB - K - HR + SF
    BABIP  = (H - HR) / babip_denom if babip_denom > 0 else 0

    return {
        "AB": AB, "H": H, "2B": _2B, "3B": _3B, "HR": HR,
        "BB": BB, "K": K, "HBP": HBP, "SF": SF, "SB": SB,
        "PA": PA, "RBI": RBI,
        "AVG": AVG, "OBP": OBP, "SLG": SLG, "OPS": OPS,
        "wOBA": wOBA, "BABIP": BABIP, "K%": K_pct, "BB%": BB_pct
    }




def ensure_cumulative_exists():
    if os.path.exists(CUMULATIVE_FILE):
        return

    hitter_rows = []
    pitcher_rows = []

    for disp_name, pos in PLAYERS.items():
        csv_name = DISPLAY_TO_CSV_NAME.get(disp_name, disp_name)
        base_pos = CSV_NAME_TO_POS.get(csv_name, pos)

        hitter_rows.append({
            "Name": csv_name,
            "Pos": base_pos,
            "PA": 0,
            "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0,
            "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
            "AVG": 0.0, "OBP": 0.0, "SLG": 0.0, "OPS": 0.0,
            "wOBA": 0.0, "K%": 0.0, "BB%": 0.0,
        })

        pitcher_rows.append({
            "Name": csv_name,
            "Pos": base_pos,
            "IP": 0.0, "W": 0, "L": 0, "SV": 0,
            "R": 0, "ER": 0, "SO": 0,
            "BB_p": 0, "HR_p": 0, "HBP_p": 0,
            "ERA": 0.0, "FIP": 0.0,
        })

    df_hitters = pd.DataFrame(hitter_rows).drop_duplicates(subset=["Name"])
    df_pitchers = pd.DataFrame(pitcher_rows).drop_duplicates(subset=["Name"])

    save_cumulative(df_hitters, df_pitchers)



def load_cumulative():
    if not os.path.exists(CUMULATIVE_FILE):
        return None, None

    with open(CUMULATIVE_FILE, "r") as f:
        lines = f.readlines()

    hitter_lines, pitcher_lines = [], []
    section = None

    for line in lines:
        line = line.strip()
        if line == "=== HITTERS ===":
            section = "hitters"
            continue
        if line == "=== PITCHERS ===":
            section = "pitchers"
            continue
        if not line:
            continue

        if section == "hitters":
            hitter_lines.append(line)
        elif section == "pitchers":
            pitcher_lines.append(line)

    df_hitters = pd.read_csv(StringIO("\n".join(hitter_lines))) if hitter_lines else None
    df_pitchers = pd.read_csv(StringIO("\n".join(pitcher_lines))) if pitcher_lines else None

    if df_pitchers is not None:
        # Backfill old cumulative files
        if "BB_p" not in df_pitchers.columns and "BB" in df_pitchers.columns:
            df_pitchers.rename(columns={"BB": "BB_p"}, inplace=True)
        if "HR_p" not in df_pitchers.columns and "HR" in df_pitchers.columns:
            df_pitchers.rename(columns={"HR": "HR_p"}, inplace=True)
        if "HBP_p" not in df_pitchers.columns:
            df_pitchers["HBP_p"] = 0
        if "R" not in df_pitchers.columns and "ER" in df_pitchers.columns:
            df_pitchers["R"] = df_pitchers["ER"]
        # 2026 new columns
        if "W" not in df_pitchers.columns:
            df_pitchers["W"] = 0
        if "L" not in df_pitchers.columns:
            df_pitchers["L"] = 0
        if "SV" not in df_pitchers.columns:
            df_pitchers["SV"] = 0

    if df_hitters is not None:
        if "RBI" not in df_hitters.columns:
            df_hitters["RBI"] = 0

    return df_hitters, df_pitchers


def save_cumulative(df_hitters, df_pitchers):
    with open(CUMULATIVE_FILE, "w") as f:
        f.write("=== HITTERS ===\n")
        df_hitters.to_csv(f, index=False)
        f.write("\n=== PITCHERS ===\n")
        df_pitchers.to_csv(f, index=False)


def recompute_hitting_metrics(df):
    if df is None or df.empty:
        return df

    AB = df["AB"]
    H = df["H"]
    _2B = df["2B"]
    _3B = df["3B"]
    HR = df["HR"]
    BB = df["BB"]
    K = df["K"]
    HBP = df["HBP"]
    SF = df["SF"]

    # Compute PA and store it
    df["PA"] = AB + BB + HBP + SF
    PA = df["PA"]

    # AVG
    df["AVG"] = H / AB.replace(0, pd.NA)

    # OBP uses PA
    df["OBP"] = (H + BB + HBP) / PA.replace(0, pd.NA)

    # SLG
    singles = H - _2B - _3B - HR
    TB = singles + 2*_2B + 3*_3B + 4*HR
    df["SLG"] = TB / AB.replace(0, pd.NA)

    # OPS
    df["OPS"] = df["OBP"] + df["SLG"]

    # wOBA (correct denominator = PA)
    woba_num = (
        0.69 * BB +
        0.72 * HBP +
        0.88 * singles +
        1.247 * _2B +
        1.578 * _3B +
        2.031 * HR
    )
    df["wOBA"] = woba_num / PA.replace(0, pd.NA)

    # Rates
    df["K%"] = K / PA.replace(0, pd.NA)
    df["BB%"] = BB / PA.replace(0, pd.NA)

    return df.fillna(0.0)



def recompute_pitching_metrics(df):
    if df is None or df.empty:
        return df

    IP   = df["IP"]
    ER   = df["ER"]
    SO   = df["SO"]
    BB_p = df["BB_p"]
    HR_p = df["HR_p"]

    HBP_p = df["HBP_p"] if "HBP_p" in df.columns else pd.Series(0, index=df.index)
    df["ERA"] = (ER * 9) / IP.replace(0, pd.NA)
    df["FIP"] = (13*HR_p + 3*(BB_p + HBP_p) - 2*SO) / IP.replace(0, pd.NA) + 3.1

    # W, L, SV are counting stats — preserve them, don't recompute
    for col in ["W", "L", "SV"]:
        if col not in df.columns:
            df[col] = 0

    return df.fillna(0.0)


def update_hitter_cumulative(player_name, stats):
    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    mask = df_hitters["Name"] == player_name
    if not mask.any():
        pos = CSV_NAME_TO_POS.get(player_name, "UTIL")
        new_row = {
            "Name": player_name,
            "Pos": pos,
            "PA": 0,
            "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0,
            "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
            "AVG": 0.0, "OBP": 0.0, "SLG": 0.0, "OPS": 0.0,
            "wOBA": 0.0, "K%": 0.0, "BB%": 0.0,
        }
        df_hitters = pd.concat([df_hitters, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_hitters["Name"] == player_name

    # Ensure RBI column exists (backward compat)
    if "RBI" not in df_hitters.columns:
        df_hitters["RBI"] = 0

    # Add raw counting stats (including RBI)
    for col in stats:
        if col in df_hitters.columns:
            df_hitters.loc[mask, col] += stats[col]

    # Add PA from this game
    df_hitters.loc[mask, "PA"] += (
        stats.get("AB", 0)
        + stats.get("BB", 0)
        + stats.get("HBP", 0)
        + stats.get("SF", 0)
    )

    # Recompute all metrics (RBI is preserved as raw count, not recomputed)
    df_hitters = recompute_hitting_metrics(df_hitters)
    df_pitchers = recompute_pitching_metrics(df_pitchers)

    save_cumulative(df_hitters, df_pitchers)



def update_pitcher_cumulative(player_name, stats):
    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    if df_pitchers is None:
        df_pitchers = pd.DataFrame(columns=[
            "Name", "Pos", "IP", "W", "L", "SV",
            "R", "ER", "SO", "BB_p", "HR_p", "HBP_p", "ERA", "FIP"
        ])

    mask = df_pitchers["Name"] == player_name
    if not mask.any():
        pos = CSV_NAME_TO_POS.get(player_name, "P")
        new_row = {
            "Name": player_name,
            "Pos": pos,
            "IP": 0.0, "W": 0, "L": 0, "SV": 0,
            "R": 0, "ER": 0, "SO": 0,
            "BB_p": 0, "HR_p": 0, "HBP_p": 0,
            "ERA": 0.0, "FIP": 0.0,
        }
        df_pitchers = pd.concat([df_pitchers, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_pitchers["Name"] == player_name

    # Ensure columns exist (including new 2026 cols)
    for col in ["IP", "W", "L", "SV", "R", "ER", "SO", "BB_p", "HR_p", "HBP_p"]:
        if col not in df_pitchers.columns:
            df_pitchers[col] = 0

    df_pitchers.loc[mask, "IP"]    += stats["IP"]
    df_pitchers.loc[mask, "W"]     += stats.get("W", 0)
    df_pitchers.loc[mask, "L"]     += stats.get("L", 0)
    df_pitchers.loc[mask, "SV"]    += stats.get("SV", 0)
    df_pitchers.loc[mask, "R"]     += stats["R"]
    df_pitchers.loc[mask, "ER"]    += stats["ER"]
    df_pitchers.loc[mask, "SO"]    += stats["SO"]
    df_pitchers.loc[mask, "BB_p"]  += stats["BB_p"]
    df_pitchers.loc[mask, "HR_p"]  += stats["HR_p"]
    df_pitchers.loc[mask, "HBP_p"] += stats["HBP_p"]

    df_pitchers = recompute_pitching_metrics(df_pitchers)
    df_hitters = recompute_hitting_metrics(df_hitters)
    save_cumulative(df_hitters, df_pitchers)


# ============================
# GAME LOG HELPERS
# ============================

def append_to_master_log(row_dict):
    df_row = pd.DataFrame([row_dict])
    if os.path.exists(MASTER_LOG_FILE):
        df_row.to_csv(MASTER_LOG_FILE, mode="a", header=False, index=False)
    else:
        df_row.to_csv(MASTER_LOG_FILE, mode="w", header=True, index=False)


def append_to_game_file(game_id, row_dict):
    filename = os.path.join(GAME_LOG_DIR, f"{game_id}.csv")
    df_row = pd.DataFrame([row_dict])
    if os.path.exists(filename):
        df_row.to_csv(filename, mode="a", header=False, index=False)
    else:
        df_row.to_csv(filename, mode="w", header=True, index=False)


def log_hitting(date, opponent, league_game, player_name, stats):
    # Compute PA for this hitting line
    PA = (
        stats.get("AB", 0)
        + stats.get("BB", 0)
        + stats.get("HBP", 0)
        + stats.get("SF", 0)
    )

    row = {
        "Date": date,
        "Opponent": opponent,
        "LeagueGame": 1 if league_game else 0,
        "Player": player_name,
        "Type": "H",

        # Hitting stats from the form (includes RBI if provided)
        **stats,

        # Add PA
        "PA": PA,

        # Pitching placeholders
        "IP": 0.0,
        "W": 0,
        "L": 0,
        "SV": 0,
        "R": 0,
        "ER": 0,
        "SO": 0,
        "BB_p": 0,
        "HR_p": 0,
        "HBP_p": 0,
    }

    game_id = f"{date}_{opponent.replace(' ', '_')}"
    append_to_master_log(row)
    append_to_game_file(game_id, row)



def log_pitching(date, opponent, league_game, player_name, stats):
    # Extract pitching stats safely with defaults
    IP    = float(stats.get("IP", 0))
    W     = int(stats.get("W", 0))
    L     = int(stats.get("L", 0))
    SV    = int(stats.get("SV", 0))
    R     = int(stats.get("R", 0))
    ER    = int(stats.get("ER", 0))
    SO    = int(stats.get("SO", 0))
    BB_p  = int(stats.get("BB_p", 0))
    HR_p  = int(stats.get("HR_p", 0))
    HBP_p = int(stats.get("HBP_p", 0))

    row = {
        "Date": date,
        "Opponent": opponent,
        "LeagueGame": 1 if league_game else 0,
        "Player": player_name,
        "Type": "P",

        # Hitting placeholders (must exist for schema consistency)
        "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "RBI": 0,
        "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
        "PA": 0,

        # Pitching stats
        "IP": IP,
        "W": W,
        "L": L,
        "SV": SV,
        "R": R,
        "ER": ER,
        "SO": SO,
        "BB_p": BB_p,
        "HR_p": HR_p,
        "HBP_p": HBP_p,
    }

    game_id = f"{date}_{opponent.replace(' ', '_')}"
    append_to_master_log(row)
    append_to_game_file(game_id, row)


def load_logs():
    if not os.path.exists(MASTER_LOG_FILE):
        return None

    try:
        return pd.read_csv(MASTER_LOG_FILE)
    except Exception:
        return pd.read_csv(MASTER_LOG_FILE, on_bad_lines="skip", engine="python")



# ============================
# REBUILD CUMULATIVE FROM LOGS
# ============================

def rebuild_cumulative_from_logs(df_logs):
    if os.path.exists(CUMULATIVE_FILE):
        os.remove(CUMULATIVE_FILE)

    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    for _, row in df_logs.iterrows():
        if row["Type"] == "H":
            stats = {
                "AB":  row["AB"],
                "H":   row["H"],
                "2B":  row["2B"],
                "3B":  row["3B"],
                "HR":  row["HR"],
                "RBI": row.get("RBI", 0),
                "BB":  row["BB"],
                "K":   row["K"],
                "HBP": row["HBP"],
                "SF":  row["SF"],
                "SB":  row["SB"],
                "PA":  row["PA"],
            }
            update_hitter_cumulative(row["Player"], stats)

        else:  # Pitching
            stats = {
                "IP":    row["IP"],
                "W":     row.get("W", 0),
                "L":     row.get("L", 0),
                "SV":    row.get("SV", 0),
                "R":     row["R"],
                "ER":    row["ER"],
                "SO":    row["SO"],
                "BB_p":  row["BB_p"],
                "HR_p":  row["HR_p"],
                "HBP_p": row.get("HBP_p", 0),
            }
            update_pitcher_cumulative(row["Player"], stats)




ROSTER_DATA = [
    {"Number": 1,  "Name": "James Aselta",    "Position": "P",    "Bats": "R", "Throws": "R", "School": "Sacred Heart",      "Year": "Senior"},
    {"Number": 4,  "Name": "Timmy Domizio",   "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Trinity College",    "Year": "Junior"},
    {"Number": 8,  "Name": "Henry Silvia",    "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Colby",             "Year": "Junior"},
    {"Number": 9,  "Name": "Jack Farnen",     "Position": "OF",   "Bats": "L", "Throws": "L", "School": "Hobart",            "Year": "Junior"},
    {"Number": 11, "Name": "Oliver Merced",   "Position": "1B",   "Bats": "L", "Throws": "R", "School": "Amherst",           "Year": "Senior"},
    {"Number": 13, "Name": "Stephen Polizzi", "Position": "C",    "Bats": "R", "Throws": "R", "School": "Campbell",         "Year": "Sophomore"},
    {"Number": 15, "Name": "Nick Carlucci",   "Position": "OF",   "Bats": "R", "Throws": "R", "School": "Pace",              "Year": "Senior"},
    {"Number": 17, "Name": "Nevin Belanger",  "Position": "P",    "Bats": "L", "Throws": "L", "School": "Johnson and Wales", "Year": "Senior"},
    {"Number": 20, "Name": "Tommy Farrell",   "Position": "P",    "Bats": "R", "Throws": "R", "School": "Gettysburg",        "Year": "Junior"},
    {"Number": 34, "Name": "Colin Donofrio",  "Position": "P",    "Bats": "R", "Throws": "R", "School": "SUNY Purchase",     "Year": "Junior"},
    {"Number": 39, "Name": "Chris Keating",   "Position": "P",    "Bats": "R", "Throws": "R", "School": "F&M",               "Year": "Sophomore"},
    {"Number": 41, "Name": "Liam DaSilva",    "Position": "C/1B", "Bats": "R", "Throws": "R", "School": "Dean College",      "Year": "Freshman"},
    {"Number": 50, "Name": "Brett Davino",    "Position": "UTIL", "Bats": "L", "Throws": "R", "School": "Stony Brook",       "Year": "Senior"},
    {"Number": 55, "Name": "Nick Dorso",      "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Roanoke",           "Year": "Sophomore"},
    {"Number": 69, "Name": "Brandon Skerritt", "Position": "C/OF", "Bats": "R", "Throws": "R", "School": "Bentley",              "Year": "Freshman"},
    {"Number": 72, "Name": "Nick Petta",       "Position": "P",    "Bats": "R", "Throws": "R", "School": "Roger Williams",       "Year": "Junior"},
    {"Number": 27, "Name": "Joel Strand",      "Position": "C",    "Bats": "R", "Throws": "R", "School": "Illinois Wesleyan",    "Year": "Junior"},
    {"Number": 20, "Name": "Patrick Leonard",  "Position": "OF",   "Bats": "L", "Throws": "L", "School": "Oberlin College",     "Year": "Sophomore"},
    {"Number": 5,  "Name": "Christian Barboto","Position": "P",    "Bats": "L", "Throws": "L", "School": "Emory",               "Year": "Sophomore"},
    {"Number": 30, "Name": "Tristian Pearl",   "Position": "P",    "Bats": "L", "Throws": "L", "School": "Babson",              "Year": "Senior"},
    {"Number": 40, "Name": "Nick Hios",        "Position": "P",    "Bats": "L", "Throws": "L", "School": "Monmouth",            "Year": "Senior"},
    {"Number": 23, "Name": "Mike Fischetti",   "Position": "OF",   "Bats": "L", "Throws": "L", "School": "Gettysburg",          "Year": "Junior"},
    {"Number": 24, "Name": "Aidan O'Loughin",  "Position": "OF",   "Bats": "R", "Throws": "R", "School": "Trinity College",     "Year": "Freshman"},
    {"Number": 6,  "Name": "Mason Kuckinski",  "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "St. Anselm",          "Year": "Freshman"},
    {"Number": 10, "Name": "Antonio Galizia",  "Position": "1B",   "Bats": "R", "Throws": "R", "School": "Western NE",          "Year": "Senior"},
    {"Number": 16, "Name": "Charlie Ellis",    "Position": "1B",   "Bats": "L", "Throws": "L", "School": "SIT",                 "Year": "Freshman"},
    {"Number": 19, "Name": "Jack Jensen",      "Position": "P",    "Bats": "R", "Throws": "R", "School": "Bentley",             "Year": "Sophomore"},
    {"Number": 18, "Name": "Merritt Hole",     "Position": "P",    "Bats": "R", "Throws": "R", "School": "Lafayette",           "Year": "Sophomore"},
    {"Number": 22, "Name": "Mo Hood",          "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Wash U",              "Year": "Freshman"},
    {"Number": 33, "Name": "Owen Staller",     "Position": "OF",   "Bats": "L", "Throws": "L", "School": "Nichols",             "Year": "Freshman"},
]


ROSTER_LOOKUP = {row["Name"]: row for row in ROSTER_DATA}


def build_player_snapshot(player_name, df_hitters, df_pitchers):
    roster_row = ROSTER_LOOKUP.get(player_name, {})
    hitter_row = None
    pitcher_row = None

    if df_hitters is not None and not df_hitters.empty:
        match = df_hitters[df_hitters["Name"] == player_name]
        if not match.empty:
            hitter_row = match.iloc[0]

    if df_pitchers is not None and not df_pitchers.empty:
        match = df_pitchers[df_pitchers["Name"] == player_name]
        if not match.empty:
            pitcher_row = match.iloc[0]

    return {
        "Player": player_name,
        "Pos": roster_row.get("Position", PLAYERS.get(player_name, "")),
        "B/T": f"{roster_row.get('Bats', '-')}/{roster_row.get('Throws', '-')}",
        "School": roster_row.get("School", ""),
        "Year": roster_row.get("Year", ""),
        "AVG": f"{float(hitter_row['AVG']):.3f}" if hitter_row is not None and "AVG" in hitter_row else "—",
        "OPS": f"{float(hitter_row['OPS']):.3f}" if hitter_row is not None and "OPS" in hitter_row else "—",
        "HR": int(hitter_row["HR"]) if hitter_row is not None and "HR" in hitter_row else 0,
        "RBI": int(hitter_row["RBI"]) if hitter_row is not None and "RBI" in hitter_row else 0,
        "SB": int(hitter_row["SB"]) if hitter_row is not None and "SB" in hitter_row else 0,
        "IP": f"{float(pitcher_row['IP']):.1f}" if pitcher_row is not None and "IP" in pitcher_row else "—",
        "ERA": f"{float(pitcher_row['ERA']):.2f}" if pitcher_row is not None and "ERA" in pitcher_row else "—",
        "SO": int(pitcher_row["SO"]) if pitcher_row is not None and "SO" in pitcher_row else 0,
    }


def make_snapshot_df(players, df_hitters, df_pitchers):
    rows = [build_player_snapshot(player, df_hitters, df_pitchers) for player in players if player]
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def file_to_data_uri(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{encoded}"


def lineup_card_name(player_name):
    if not player_name:
        return "—"
    pieces = str(player_name).strip().split()
    return pieces[-1].upper() if pieces else "—"


def render_lineup_card_html(logo_uri, card_meta, lineup_rows, sub_rows, bench_rows, pitcher_rows, notes):
    def cell(value):
        return html.escape(str(value if value not in [None, ""] else "—"))

    lineup_html = "".join(
        f"""
        <tr>
            <td class="order-cell">{cell(row.get('Order'))}</td>
            <td>{cell(lineup_card_name(row.get('Player', '')))}</td>
            <td class="pos-cell">{cell(row.get('Position') or '—')}</td>
        </tr>
        """
        for row in lineup_rows
    )

    subs_html = "".join(
        f"""
        <tr>
            <td class="order-cell">{cell(row.get('Order'))}</td>
            <td class="accent-cell">{cell(lineup_card_name(row.get('PlayerIn', '')))}</td>
            <td class="accent-cell">{cell(row.get('ForLabel', '—'))}</td>
            <td>{cell(lineup_card_name(row.get('PlayerOut', '')))}</td>
            <td class="pos-cell">{cell(row.get('Pos', '—'))}</td>
        </tr>
        """
        for row in sub_rows
    )

    bench_html = "".join(
        f"<tr><td>{cell(lineup_card_name(player))}</td></tr>"
        for player in bench_rows
    ) or "<tr><td>&nbsp;</td></tr>" * 5

    pitchers_html = "".join(
        f"""
        <tr>
            <td>{cell(lineup_card_name(row.get('Pitcher', '')))}</td>
            <td class="usage-cell">{cell(row.get('Usage', '—'))}</td>
        </tr>
        """
        for row in pitcher_rows
    ) or "<tr><td>&nbsp;</td><td>&nbsp;</td></tr>" * 5

    return f"""
    <style>
    .lineup-card-sheet {{
        background: radial-gradient(circle at top, #ffffff 0%, #f7f7f7 45%, #efefef 100%);
        color: #111111;
        border: 2px solid #1a1a1a;
        padding: 14px;
        margin-top: 12px;
        font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif;
        letter-spacing: 0.02em;
    }}
    .lineup-card-header {{
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 18px;
        margin-bottom: 18px;
    }}
    .lineup-card-header-line {{
        height: 5px;
        background: #ff5a0a;
    }}
    .lineup-card-logo {{
        max-width: 420px;
        width: 100%;
        display: block;
        margin: 0 auto;
    }}
    .lineup-card-meta {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        margin-bottom: 14px;
        font-size: 1.15rem;
    }}
    .lineup-card-meta-box {{
        border-bottom: 4px solid #1a1a1a;
        padding-bottom: 6px;
        text-transform: uppercase;
    }}
    .lineup-card-grid {{
        display: grid;
        grid-template-columns: 1.02fr 1.65fr;
        gap: 18px;
        margin-bottom: 16px;
    }}
    .lineup-card-lower {{
        display: grid;
        grid-template-columns: 1fr 1.15fr;
        gap: 18px;
        margin-bottom: 16px;
    }}
    .lineup-card-panel-title {{
        background: #050505;
        color: #ffffff;
        text-align: center;
        font-size: 1.5rem;
        padding: 10px 8px;
        text-transform: uppercase;
        border: 2px solid #222222;
        border-bottom: none;
    }}
    .lineup-card-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        background: rgba(255,255,255,0.95);
    }}
    .lineup-card-table th,
    .lineup-card-table td {{
        border: 2px solid rgba(20,20,20,0.45);
        padding: 10px 12px;
        font-size: 1.05rem;
        text-transform: uppercase;
    }}
    .lineup-card-table th {{
        background: #080808;
        color: #ffffff;
        font-size: 0.98rem;
    }}
    .lineup-card-table th.accent-head {{
        color: #ff5a0a;
    }}
    .lineup-card-table td.order-cell {{
        color: #ff5a0a;
        text-align: center;
        width: 52px;
        font-size: 1.35rem;
    }}
    .lineup-card-table td.pos-cell,
    .lineup-card-table td.usage-cell {{
        text-align: center;
    }}
    .lineup-card-table td.accent-cell {{
        color: #ff5a0a;
    }}
    .lineup-card-notes-title {{
        font-size: 1.2rem;
        margin-bottom: 6px;
        text-transform: uppercase;
    }}
    .lineup-card-notes-box {{
        min-height: 96px;
        border: 2px solid rgba(20,20,20,0.45);
        background: rgba(255,255,255,0.9);
        padding: 14px;
        font-size: 1rem;
        text-transform: uppercase;
    }}
    .lineup-card-mark {{
        display: flex;
        justify-content: flex-end;
        font-size: 4rem;
        color: #111111;
        -webkit-text-stroke: 2px #ff5a0a;
        line-height: 1;
    }}
    </style>
    <div class="lineup-card-sheet">
        <div class="lineup-card-header">
            <div class="lineup-card-header-line"></div>
            <div>{f'<img src="{logo_uri}" class="lineup-card-logo" />' if logo_uri else 'BARONS'}</div>
            <div class="lineup-card-header-line"></div>
        </div>
        <div class="lineup-card-meta">
            <div class="lineup-card-meta-box">Game: {cell(card_meta.get('game', ''))}</div>
            <div class="lineup-card-meta-box">Date: {cell(card_meta.get('date', ''))}</div>
            <div class="lineup-card-meta-box">Opponent: {cell(card_meta.get('opponent', ''))}</div>
            <div class="lineup-card-meta-box">First Pitch: {cell(card_meta.get('first_pitch', ''))}</div>
        </div>
        <div class="lineup-card-grid">
            <div>
                <div class="lineup-card-panel-title">Lineup</div>
                <table class="lineup-card-table">
                    <thead>
                        <tr><th style="width:52px;">Order</th><th>Player</th><th style="width:68px;">Pos</th></tr>
                    </thead>
                    <tbody>{lineup_html}</tbody>
                </table>
            </div>
            <div>
                <div class="lineup-card-panel-title">{cell(card_meta.get('sub_title', 'Substitutions'))}</div>
                <table class="lineup-card-table">
                    <thead>
                        <tr>
                            <th style="width:52px;">Order</th>
                            <th class="accent-head">Player In</th>
                            <th class="accent-head">For</th>
                            <th>Player Out</th>
                            <th style="width:68px;">Pos</th>
                        </tr>
                    </thead>
                    <tbody>{subs_html}</tbody>
                </table>
            </div>
        </div>
        <div class="lineup-card-lower">
            <div>
                <div class="lineup-card-panel-title">Bench / Available</div>
                <table class="lineup-card-table"><tbody>{bench_html}</tbody></table>
            </div>
            <div>
                <div class="lineup-card-panel-title">Live Pitchers</div>
                <table class="lineup-card-table"><tbody>{pitchers_html}</tbody></table>
            </div>
        </div>
        <div class="lineup-card-notes-title">Notes:</div>
        <div class="lineup-card-notes-box">{cell(notes)}</div>
        <div class="lineup-card-mark">B</div>
    </div>
    """



# ============================
# UI TABS
# ============================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Roster",            # tab1
    "Team Calendar",     # tab2
    "Cumulative Players",# tab3
    "Team Totals",       # tab4
    "Game Logs",         # tab5
    "Player Profiles",   # tab6
    "Coach Tools",       # tab7
])



# ---------- TAB 3: CUMULATIVE PLAYERS ----------

with tab3:
    st.header("Cumulative Player Stats")

    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    col1, col2 = st.columns(2)

    # Hitters
    with col1:
        st.subheader("Hitters")
        if df_hitters is None or df_hitters.empty:
            st.info("No hitter data yet.")
        else:
            # Show active players first (sort by PA descending)
            df_h_display = df_hitters.sort_values("PA", ascending=False).copy()
            # Select and order columns
            h_cols = [c for c in [
                "Name","Pos","PA","AB","H","2B","3B","HR","RBI",
                "BB","K","SB","AVG","OBP","SLG","OPS","wOBA","K%","BB%"
            ] if c in df_h_display.columns]
            df_h_display = df_h_display[h_cols]
            # Format K% and BB% as percentage strings
            df_h_display["K%"]  = (df_h_display["K%"]  * 100).round(1).astype(str) + "%"
            df_h_display["BB%"] = (df_h_display["BB%"] * 100).round(1).astype(str) + "%"
            st.dataframe(
                df_h_display.style.format({
                    "AVG":  "{:.3f}",
                    "OBP":  "{:.3f}",
                    "SLG":  "{:.3f}",
                    "OPS":  "{:.3f}",
                    "wOBA": "{:.3f}",
                })
            )

    # Pitchers
    with col2:
        st.subheader("Pitchers")
        if df_pitchers is None or df_pitchers.empty:
            st.info("No pitcher data yet.")
        else:
            # Sort by IP descending
            df_p = df_pitchers.sort_values("IP", ascending=False).copy()
            p_cols = [c for c in [
                "Name","Pos","IP","W","L","SV","R","ER","SO","BB_p","HR_p","ERA","FIP"
            ] if c in df_p.columns]
            df_p = df_p[p_cols]
            st.dataframe(
                df_p.style.format({
                    "IP":  "{:.1f}",
                    "ERA": "{:.2f}",
                    "FIP": "{:.2f}",
                })
            )


# ---------- TAB 4: TEAM TOTALS ----------

with tab4:
    st.header("Team Totals (from Game Logs)")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No game logs yet.")
    else:

        # -------------------------
        # NORMALIZE LOGS
        # -------------------------

        # Ensure PA exists for hitters
        if "PA" not in df_logs.columns:
            df_logs["PA"] = (
                df_logs["AB"].fillna(0) +
                df_logs["BB"].fillna(0) +
                df_logs["HBP"].fillna(0) +
                df_logs["SF"].fillna(0)
            )

        # Ensure pitching columns exist
        for col in ["BB_p", "HR_p", "HBP_p"]:
            if col not in df_logs.columns:
                df_logs[col] = 0

        # Normalize Type
        df_logs["Type"] = df_logs["Type"].astype(str).str.upper().str.strip()

        # Normalize LeagueGame
        df_logs["LeagueGame"] = df_logs["LeagueGame"].astype(int)

        # -------------------------
        # FILTER UI
        # -------------------------
        mode = st.radio(
            "Scope",
            ["Overall", "League games only", "Non-league games only"],
            horizontal=True
        )

        if mode == "Overall":
            league_filter = None
        elif mode == "League games only":
            league_filter = True
        else:
            league_filter = False

        # -------------------------
        # COMPUTE TOTALS
        # -------------------------
        hit_totals = compute_team_hitting_totals(df_logs, league_filter)
        pit_totals = compute_team_pitching_totals(df_logs, league_filter)

        if hit_totals is None and pit_totals is None:
            st.info("No data for this scope yet.")
        else:
            c1, c2 = st.columns(2)

            # -------------------------
            # HITTING TOTALS
            # -------------------------
            with c1:
                st.subheader("Hitting")

                if hit_totals:
                    ht = hit_totals

                    c_a, c_b, c_c, c_d = st.columns(4)
                    c_a.metric("AVG",  f"{ht['AVG']:.3f}")
                    c_b.metric("OBP",  f"{ht['OBP']:.3f}")
                    c_c.metric("SLG",  f"{ht['SLG']:.3f}")
                    c_d.metric("OPS",  f"{ht['OPS']:.3f}")
                    c_e, c_f, c_g, c_h = st.columns(4)
                    c_e.metric("wOBA", f"{ht['wOBA']:.3f}")
                    c_f.metric("BABIP", f"{ht['BABIP']:.3f}")
                    c_g.metric("K%",   f"{ht['K%']*100:.1f}%")
                    c_h.metric("BB%",  f"{ht['BB%']*100:.1f}%")
                    st.write(
                        f"PA: {int(ht['PA'])}  AB: {int(ht['AB'])}  H: {int(ht['H'])}  "
                        f"2B: {int(ht['2B'])}  3B: {int(ht['3B'])}  HR: {int(ht['HR'])}  "
                        f"RBI: {int(ht['RBI'])}  SB: {int(ht['SB'])}"
                    )
                    st.write(
                        f"BB: {int(ht['BB'])}  K: {int(ht['K'])}  "
                        f"HBP: {int(ht['HBP'])}  SF: {int(ht['SF'])}"
                    )

            # -------------------------
            # PITCHING TOTALS
            # -------------------------
            with c2:
                st.subheader("Pitching")

                if pit_totals:
                    pt = pit_totals

                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("ERA", f"{pt['ERA']:.2f}")
                    c_b.metric("FIP", f"{pt['FIP']:.2f}")
                    k9 = (pt['SO'] * 9 / pt['IP']) if pt['IP'] > 0 else 0
                    c_c.metric("K/9", f"{k9:.1f}")
                    c_d, c_e, c_f = st.columns(3)
                    bb9 = (pt['BB'] * 9 / pt['IP']) if pt['IP'] > 0 else 0
                    kbb = (pt['SO'] / pt['BB']) if pt['BB'] > 0 else 0
                    c_d.metric("BB/9", f"{bb9:.1f}")
                    c_e.metric("K/BB", f"{kbb:.2f}" if pt['BB'] > 0 else "—")
                    c_f.metric("W-L-SV", f"{int(pt['W'])}-{int(pt['L'])}-{int(pt['SV'])}")
                    st.write(
                        f"IP: {pt['IP']:.1f}  R: {int(pt['R'])}  ER: {int(pt['ER'])}  "
                        f"Unearned: {int(pt['Unearned'])}"
                    )
                    st.write(
                        f"SO: {int(pt['SO'])}  BB: {int(pt['BB'])}  HR: {int(pt['HR'])}"
                    )




# ---------- TAB 5: GAME LOGS ----------

with tab5:
    st.header("Game Logs")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No game logs yet.")
    else:

        # -------------------------
        # NORMALIZE LOGS
        # -------------------------

        # Normalize Type so pitching rows show up
        df_logs["Type"] = (
            df_logs["Type"]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace({"PITCHING": "P", "HITTING": "H"})
        )

        # Ensure PA exists for hitters
        if "PA" not in df_logs.columns:
            df_logs["PA"] = (
                df_logs["AB"].fillna(0) +
                df_logs["BB"].fillna(0) +
                df_logs["HBP"].fillna(0) +
                df_logs["SF"].fillna(0)
            )

        # Ensure pitching columns exist
        for col in ["BB_p", "HR_p", "HBP_p"]:
            if col not in df_logs.columns:
                df_logs[col] = 0

        # -------------------------
        # FILTER UI
        # -------------------------
        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            players = ["All"] + sorted(df_logs["Player"].unique().tolist())
            player_sel = st.selectbox("Player", players)

        with colf2:
            opps = ["All"] + sorted(df_logs["Opponent"].unique().tolist())
            opp_sel = st.selectbox("Opponent", opps)

        with colf3:
            lg_mode = st.selectbox("Game Type", ["All", "League only", "Non-league only"])

        df_view = df_logs.copy()

        # Filters
        if player_sel != "All":
            df_view = df_view[df_view["Player"] == player_sel]
        if opp_sel != "All":
            df_view = df_view[df_view["Opponent"] == opp_sel]
        if lg_mode == "League only":
            df_view = df_view[df_view["LeagueGame"] == 1]
        elif lg_mode == "Non-league only":
            df_view = df_view[df_view["LeagueGame"] == 0]

        # Sort
        df_view = df_view.sort_values(["Date", "Player", "Type"])

        # -------------------------
        # DISPLAY TABLE
        # -------------------------
        # Build display cols — only include columns that exist in df_view
        log_display_cols = [c for c in [
            "Date", "Opponent", "LeagueGame", "Player", "Type",
            # Hitting
            "PA", "AB", "H", "2B", "3B", "HR", "RBI",
            "BB", "K", "HBP", "SF", "SB",
            # Pitching
            "IP", "W", "L", "SV", "R", "ER", "SO",
            "BB_p", "HR_p", "HBP_p",
        ] if c in df_view.columns]

        st.dataframe(df_view[log_display_cols])




# ---------- TAB 6: PLAYER PROFILES ----------

with tab6:
    st.header("Player Profiles")

    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    all_players = sorted(set(df_hitters["Name"]).union(df_pitchers["Name"]))
    player = st.selectbox("Select a player", all_players)

    st.subheader(f"Profile: {player}")

    # Hitting stats
    hit_row = df_hitters[df_hitters["Name"] == player]
    if not hit_row.empty:
        st.markdown("### Hitting Stats")

        # Ensure PA is visible
        if "PA" not in hit_row.columns:
            hit_row = hit_row.copy()
            hit_row["PA"] = (
                hit_row["AB"] +
                hit_row["BB"] +
                hit_row["HBP"] +
                hit_row["SF"]
            )

        hit_display = hit_row.copy()

        # Compute advanced hitting stats
        ab  = hit_display["AB"].values[0]
        h_  = hit_display["H"].values[0]
        d2  = hit_display["2B"].values[0]
        d3  = hit_display["3B"].values[0]
        hr  = hit_display["HR"].values[0]
        bb  = hit_display["BB"].values[0]
        k   = hit_display["K"].values[0]
        hbp = hit_display["HBP"].values[0]
        sf  = hit_display["SF"].values[0]
        pa  = hit_display["PA"].values[0]
        slg = hit_display["SLG"].values[0] if "SLG" in hit_display.columns else 0
        avg = hit_display["AVG"].values[0] if "AVG" in hit_display.columns else 0

        singles = h_ - d2 - d3 - hr
        tb      = singles + 2*d2 + 3*d3 + 4*hr
        iso     = slg - avg
        xbh     = d2 + d3 + hr
        babip_d = ab - k - hr + sf
        babip   = (h_ - hr) / babip_d if babip_d > 0 else 0.0

        hit_display["ISO"]   = iso
        hit_display["XBH"]   = int(xbh)
        hit_display["TB"]    = int(tb)
        hit_display["BABIP"] = babip

        h_profile_cols = [c for c in [
            "Name", "Pos",
            "PA", "AB", "H", "2B", "3B", "HR", "RBI",
            "BB", "K", "HBP", "SF", "SB", "XBH", "TB",
            "AVG", "OBP", "SLG", "OPS",
            "wOBA", "BABIP", "ISO", "K%", "BB%"
        ] if c in hit_display.columns]

        hit_display = hit_display[h_profile_cols].copy()
        hit_display["K%"]  = (hit_display["K%"]  * 100).round(1).astype(str) + "%"
        hit_display["BB%"] = (hit_display["BB%"] * 100).round(1).astype(str) + "%"

        st.dataframe(
            hit_display.style.format({
                "AVG":   "{:.3f}",
                "OBP":   "{:.3f}",
                "SLG":   "{:.3f}",
                "OPS":   "{:.3f}",
                "wOBA":  "{:.3f}",
                "BABIP": "{:.3f}",
                "ISO":   "{:.3f}",
            })
        )

    # Pitching stats
    pit_row = df_pitchers[df_pitchers["Name"] == player]
    if not pit_row.empty:
        st.markdown("### Pitching Stats")
        pit_row = pit_row.copy()
        pit_row["Unearned"] = pit_row["R"] - pit_row["ER"]

        # Compute advanced pitching stats
        ip_  = pit_row["IP"].values[0]
        so_  = pit_row["SO"].values[0]
        bb_  = pit_row["BB_p"].values[0]
        hr_  = pit_row["HR_p"].values[0]
        pit_row["K/9"]  = round((so_ * 9 / ip_), 2) if ip_ > 0 else 0.0
        pit_row["BB/9"] = round((bb_ * 9 / ip_), 2) if ip_ > 0 else 0.0
        pit_row["HR/9"] = round((hr_ * 9 / ip_), 2) if ip_ > 0 else 0.0
        pit_row["K/BB"] = round(so_ / bb_, 2) if bb_ > 0 else None

        p_profile_cols = [c for c in [
            "Name", "Pos",
            "IP", "W", "L", "SV",
            "R", "ER", "Unearned",
            "SO", "BB_p", "HR_p", "HBP_p",
            "ERA", "FIP", "K/9", "BB/9", "HR/9", "K/BB"
        ] if c in pit_row.columns]

        st.dataframe(
            pit_row[p_profile_cols].style.format({
                "IP":   "{:.1f}",
                "ERA":  "{:.2f}",
                "FIP":  "{:.2f}",
                "K/9":  "{:.2f}",
                "BB/9": "{:.2f}",
                "HR/9": "{:.2f}",
            })
        )

        
# ---------- TAB 1: ROSTER ----------
with tab1:
    st.header("CT Barons South Roster")

    df_roster = pd.DataFrame(ROSTER_DATA)
    df_roster = df_roster.sort_values("Number")

    st.dataframe(
        df_roster.style.format({
            "Number": "{:d}"
        })
    )


    

# ---------- TAB 7: COACH TOOLS ----------
with tab7:
    st.header("Coach Tools (Password Protected)")

    # ---------------- AUTH ----------------
    if not st.session_state.authenticated:
        pwd = st.text_input("Enter coach password:", type="password")
        if st.button("Unlock"):
            if pwd == COACH_PASSWORD:
                st.session_state.authenticated = True
                st.success("Coach mode unlocked.")
            else:
                st.error("Incorrect password.")
        st.stop()
    else:
        st.success("Coach mode active.")

    # ============================================================
    # TEAM RECORD EDITOR
    # ============================================================
    st.subheader("Team Record")

    record = load_team_record()

    col_w, col_l = st.columns(2)
    with col_w:
        wins = st.number_input("Wins", min_value=0, value=record["Wins"], step=1)
    with col_l:
        losses = st.number_input("Losses", min_value=0, value=record["Losses"], step=1)

    if st.button("Save Team Record"):
        save_team_record(wins, losses)
        st.success(f"Record updated to {wins}-{losses}")

    # ============================================================
    # DEPTH CHART BUILDER
    # ============================================================
    st.subheader("Depth Chart Builder")

    saved_depth_charts = load_depth_chart_ideas()
    ensure_cumulative_exists()
    df_hitters_coach, df_pitchers_coach = load_cumulative()
    depth_chart_names = ["New Idea"] + sorted(saved_depth_charts.keys())
    selected_depth_chart = st.selectbox("Saved depth chart ideas", depth_chart_names)

    position_options = [
        "", "P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "EH",
        "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "UTIL", "C/OF", "C/1B", "INF", "OF"
    ]
    pitcher_pool = sorted(
        [
            player for player, pos in PLAYERS.items()
            if "P" in str(pos).upper()
        ]
    )
    bullpen_role_labels = [
        ("rotation_starter_1", "Starter 1"),
        ("rotation_starter_2", "Starter 2"),
        ("rotation_starter_3", "Starter 3"),
        ("rotation_starter_4", "Starter 4"),
        ("rotation_starter_5", "Starter 5"),
        ("rotation_closer", "Closer"),
        ("rotation_setup", "Setup"),
        ("rotation_fireman", "Fireman"),
        ("rotation_long_relief", "Long Relief"),
    ]

    for i in range(1, 11):
        st.session_state.setdefault(f"depth_player_{i}", "")
        st.session_state.setdefault(f"depth_pos_{i}", "")
    st.session_state.setdefault("depth_chart_notes", "")
    st.session_state.setdefault("depth_chart_bench", [])
    st.session_state.setdefault("depth_chart_inactive", [])
    st.session_state.setdefault("rotation_notes", "")
    st.session_state.setdefault("lineup_card_game", "1")
    st.session_state.setdefault("lineup_card_date", "")
    st.session_state.setdefault("lineup_card_opponent", "")
    st.session_state.setdefault("lineup_card_first_pitch", "")
    st.session_state.setdefault("lineup_card_sub_title", "Substitutions")
    st.session_state.setdefault("lineup_card_notes", "")
    for rotation_key, _ in bullpen_role_labels:
        st.session_state.setdefault(rotation_key, "")
        st.session_state.setdefault(f"card_pitch_usage_{rotation_key}", "")
    for idx in range(1, 11):
        st.session_state.setdefault(f"card_sub_in_{idx}", "")
        st.session_state.setdefault(f"card_sub_for_{idx}", "")
        st.session_state.setdefault(f"card_sub_out_{idx}", "")
        st.session_state.setdefault(f"card_sub_pos_{idx}", "")

    if selected_depth_chart != "New Idea":
        saved_chart = saved_depth_charts[selected_depth_chart]
        if st.button("Load Selected Idea"):
            for idx, slot in enumerate(saved_chart.get("lineup", []), start=1):
                if idx > 10:
                    break
                st.session_state[f"depth_player_{idx}"] = slot.get("player", "")
                st.session_state[f"depth_pos_{idx}"] = slot.get("position", "")
            for idx in range(len(saved_chart.get("lineup", [])) + 1, 11):
                st.session_state[f"depth_player_{idx}"] = ""
                st.session_state[f"depth_pos_{idx}"] = ""
            st.session_state["depth_chart_notes"] = saved_chart.get("notes", "")
            st.session_state["depth_chart_bench"] = saved_chart.get("bench", [])
            st.session_state["depth_chart_inactive"] = saved_chart.get("inactive", [])
            saved_rotation = saved_chart.get("rotation", {})
            for rotation_key, _ in bullpen_role_labels:
                st.session_state[rotation_key] = saved_rotation.get(rotation_key, "")
            st.session_state["rotation_notes"] = saved_rotation.get("notes", "")
            saved_lineup_card = saved_chart.get("lineup_card", {})
            st.session_state["lineup_card_game"] = saved_lineup_card.get("game", "1")
            st.session_state["lineup_card_date"] = saved_lineup_card.get("date", "")
            st.session_state["lineup_card_opponent"] = saved_lineup_card.get("opponent", "")
            st.session_state["lineup_card_first_pitch"] = saved_lineup_card.get("first_pitch", "")
            st.session_state["lineup_card_sub_title"] = saved_lineup_card.get("sub_title", "Substitutions")
            st.session_state["lineup_card_notes"] = saved_lineup_card.get("notes", "")
            saved_subs = saved_lineup_card.get("subs", [])
            for idx in range(1, 11):
                row = saved_subs[idx - 1] if idx - 1 < len(saved_subs) else {}
                st.session_state[f"card_sub_in_{idx}"] = row.get("player_in", "")
                st.session_state[f"card_sub_for_{idx}"] = row.get("for_label", "")
                st.session_state[f"card_sub_out_{idx}"] = row.get("player_out", "")
                st.session_state[f"card_sub_pos_{idx}"] = row.get("pos", "")
            saved_usage = saved_lineup_card.get("pitch_usage", {})
            for rotation_key, _ in bullpen_role_labels:
                st.session_state[f"card_pitch_usage_{rotation_key}"] = saved_usage.get(rotation_key, "")
            st.rerun()

        if st.button("Delete Selected Idea"):
            saved_depth_charts.pop(selected_depth_chart, None)
            save_depth_chart_ideas(saved_depth_charts)
            st.success(f"Deleted depth chart idea: {selected_depth_chart}")
            st.rerun()

    depth_chart_name = st.text_input(
        "Idea name",
        value="" if selected_depth_chart == "New Idea" else selected_depth_chart,
        key="depth_chart_name"
    )

    st.markdown(
        """
        <style>
        .depth-card {
            background: linear-gradient(135deg, #181818 0%, #0f0f0f 100%);
            border: 1px solid #333333;
            border-left: 6px solid #FF6F00;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 10px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
        }
        .depth-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .depth-slot-badge {
            display: inline-block;
            background: #FF6F00;
            color: #000000;
            font-weight: 800;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.9rem;
        }
        .depth-slot-label {
            color: #FFA040;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-size: 0.8rem;
        }
        .lineup-preview-card {
            background: linear-gradient(160deg, #101010 0%, #1b1b1b 100%);
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 16px;
        }
        .lineup-preview-row {
            display: grid;
            grid-template-columns: 56px 1fr 70px;
            gap: 10px;
            align-items: center;
            padding: 9px 0;
            border-bottom: 1px solid #2a2a2a;
        }
        .lineup-preview-row:last-child {
            border-bottom: none;
        }
        .lineup-preview-order {
            color: #FF6F00;
            font-weight: 900;
            font-size: 1.1rem;
        }
        .lineup-preview-player {
            color: #FFFFFF;
            font-weight: 700;
        }
        .lineup-preview-empty {
            color: #7a7a7a;
            font-style: italic;
        }
        .lineup-preview-pos {
            color: #000000;
            background: #FFA040;
            border-radius: 999px;
            text-align: center;
            padding: 3px 8px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .coach-panel {
            background: linear-gradient(145deg, #121212 0%, #1c1c1c 100%);
            border: 1px solid #2e2e2e;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
        }
        .coach-panel h4 {
            margin: 0 0 10px 0;
            color: #FFA040 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Batting Order (10 Spots)")
    depth_chart_rows = []
    inactive_players = st.multiselect(
        "Out / inactive today",
        sorted(PLAYERS.keys()),
        default=st.session_state.get("depth_chart_inactive", []),
        key="depth_chart_inactive",
        help="Players listed here stay off the auto bench list and are separated from active options."
    )
    active_roster = [player for player in sorted(PLAYERS.keys()) if player not in inactive_players]
    preview_rows = []
    for i in range(1, 11):
        current_player = st.session_state.get(f"depth_player_{i}", "")
        player_options = [""] + active_roster
        if current_player and current_player not in player_options:
            player_options.append(current_player)
        st.markdown(
            f"""
            <div class="depth-card">
                <div class="depth-card-header">
                    <span class="depth-slot-badge">#{i}</span>
                    <span class="depth-slot-label">Batting Order Spot</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([2.2, 1, 0.8])
        with col1:
            player = st.selectbox(
                f"Player {i}",
                player_options,
                key=f"depth_player_{i}",
                label_visibility="collapsed"
            )
        with col2:
            position = st.selectbox(
                f"Pos {i}",
                position_options,
                key=f"depth_pos_{i}",
                label_visibility="collapsed"
            )
        with col3:
            if st.button("Clear", key=f"clear_depth_{i}"):
                st.session_state[f"depth_player_{i}"] = ""
                st.session_state[f"depth_pos_{i}"] = ""
                st.rerun()

        if player:
            preview_rows.append(
                {
                    "order": i,
                    "player": player,
                    "position": position or "--"
                }
            )
        depth_chart_rows.append({
            "Order": i,
            "Player": player,
            "Position": position
        })

    selected_players = [row["Player"] for row in depth_chart_rows if row["Player"]]
    duplicate_players = sorted({player for player in selected_players if selected_players.count(player) > 1})
    inactive_in_lineup = [player for player in selected_players if player in inactive_players]
    open_spots = sum(1 for row in depth_chart_rows if not row["Player"])
    unused_players = [player for player in active_roster if player not in selected_players]

    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("Filled Spots", f"{10 - open_spots}/10")
    metric_b.metric("Bench Available", len(unused_players))
    metric_c.metric("Duplicate Players", len(duplicate_players))
    metric_d.metric("Out / Inactive", len(inactive_players))

    if duplicate_players:
        st.warning("Duplicate players in lineup: " + ", ".join(duplicate_players))
    if inactive_in_lineup:
        st.warning("Inactive players currently in lineup: " + ", ".join(inactive_in_lineup))

    current_bench = st.session_state.get("depth_chart_bench", [])
    bench_options = unused_players + [player for player in current_bench if player not in unused_players]
    bench_players = st.multiselect(
        "Bench / alternates",
        bench_options,
        default=current_bench,
        key="depth_chart_bench"
    )

    if st.button("Auto-fill Bench With Unused Players"):
        st.session_state["depth_chart_bench"] = unused_players
        st.rerun()

    st.markdown("### Player Snapshot Board")
    lineup_snapshot = make_snapshot_df(selected_players, df_hitters_coach, df_pitchers_coach)
    bench_snapshot = make_snapshot_df(bench_players, df_hitters_coach, df_pitchers_coach)
    inactive_snapshot = make_snapshot_df(inactive_players, df_hitters_coach, df_pitchers_coach)

    snapshot_col1, snapshot_col2 = st.columns([2, 1])
    with snapshot_col1:
        st.markdown('<div class="coach-panel"><h4>Projected Lineup Stats</h4></div>', unsafe_allow_html=True)
        if lineup_snapshot.empty:
            st.info("Add players to the lineup to see their hitting and pitching snapshots.")
        else:
            lineup_snapshot.insert(0, "Order", list(range(1, len(lineup_snapshot) + 1)))
            st.dataframe(
                lineup_snapshot[["Order", "Player", "Pos", "B/T", "Year", "AVG", "OPS", "HR", "RBI", "SB", "IP", "ERA", "SO"]],
                use_container_width=True,
                hide_index=True
            )
    with snapshot_col2:
        st.markdown('<div class="coach-panel"><h4>Bench And Availability</h4></div>', unsafe_allow_html=True)
        if not bench_snapshot.empty:
            st.markdown("**Bench**")
            st.dataframe(
                bench_snapshot[["Player", "Pos", "AVG", "OPS", "IP", "ERA"]],
                use_container_width=True,
                hide_index=True
            )
        if not inactive_snapshot.empty:
            st.markdown("**Out / Inactive**")
            st.dataframe(
                inactive_snapshot[["Player", "Pos", "Year", "School"]],
                use_container_width=True,
                hide_index=True
            )

    depth_chart_notes = st.text_area(
        "Notes",
        key="depth_chart_notes",
        placeholder="Bench ideas, matchup notes, alternate defensive alignments, courtesy runners, late defense..."
    )

    st.markdown("### Pitching Plan")
    rotation_col1, rotation_col2 = st.columns([1.3, 1])
    with rotation_col1:
        st.markdown('<div class="coach-panel"><h4>Rotation And Bullpen Roles</h4></div>', unsafe_allow_html=True)
        for idx in range(0, len(bullpen_role_labels), 3):
            role_cols = st.columns(3)
            for col, (rotation_key, rotation_label) in zip(role_cols, bullpen_role_labels[idx:idx + 3]):
                with col:
                    st.selectbox(
                        rotation_label,
                        [""] + pitcher_pool,
                        key=rotation_key
                    )
        rotation_notes = st.text_area(
            "Pitching notes",
            key="rotation_notes",
            placeholder="Weekend plan, pitch limits, short-rest flags, who can close, who is down today..."
        )
    with rotation_col2:
        st.markdown('<div class="coach-panel"><h4>Pitching Board</h4></div>', unsafe_allow_html=True)
        rotation_rows = []
        for rotation_key, rotation_label in bullpen_role_labels:
            pitcher_name = st.session_state.get(rotation_key, "")
            if pitcher_name:
                snapshot = build_player_snapshot(pitcher_name, df_hitters_coach, df_pitchers_coach)
                rotation_rows.append(
                    {
                        "Role": rotation_label,
                        "Pitcher": pitcher_name,
                        "IP": snapshot["IP"],
                        "ERA": snapshot["ERA"],
                        "SO": snapshot["SO"],
                        "B/T": snapshot["B/T"],
                    }
                )

        if rotation_rows:
            st.dataframe(pd.DataFrame(rotation_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Pick starters and bullpen roles to build your pitching board.")

    st.markdown("### Printable Lineup Card")
    card_meta_col1, card_meta_col2, card_meta_col3, card_meta_col4 = st.columns(4)
    with card_meta_col1:
        lineup_card_game = st.text_input("Game #", key="lineup_card_game")
    with card_meta_col2:
        lineup_card_date = st.text_input("Card date", key="lineup_card_date", placeholder="6/17")
    with card_meta_col3:
        lineup_card_opponent = st.text_input("Card opponent", key="lineup_card_opponent")
    with card_meta_col4:
        lineup_card_first_pitch = st.text_input("First pitch", key="lineup_card_first_pitch", placeholder="7:00 PM")

    lineup_card_sub_title = st.text_input(
        "Substitution header",
        key="lineup_card_sub_title",
        placeholder="Top of 5th inning substitutions"
    )

    st.markdown("#### Substitution Grid")
    sub_roster_options = [""] + sorted(PLAYERS.keys())
    card_sub_rows = []
    for idx in range(1, 11):
        sub_cols = st.columns([0.7, 1.6, 1.2, 1.6, 0.8])
        with sub_cols[0]:
            st.markdown(f"**{idx}**")
        with sub_cols[1]:
            player_in = st.selectbox(
                f"Player in {idx}",
                sub_roster_options,
                key=f"card_sub_in_{idx}",
                label_visibility="collapsed"
            )
        with sub_cols[2]:
            for_label = st.text_input(
                f"For label {idx}",
                key=f"card_sub_for_{idx}",
                placeholder="IN FOR / NEW POS",
                label_visibility="collapsed"
            )
        with sub_cols[3]:
            player_out = st.selectbox(
                f"Player out {idx}",
                sub_roster_options,
                key=f"card_sub_out_{idx}",
                label_visibility="collapsed"
            )
        with sub_cols[4]:
            sub_pos = st.text_input(
                f"Sub pos {idx}",
                key=f"card_sub_pos_{idx}",
                placeholder="POS",
                label_visibility="collapsed"
            )
        card_sub_rows.append(
            {
                "Order": idx,
                "PlayerIn": player_in,
                "ForLabel": for_label,
                "PlayerOut": player_out,
                "Pos": sub_pos,
            }
        )

    st.markdown("#### Pitcher Usage For Card")
    lineup_card_pitchers = []
    for rotation_key, rotation_label in bullpen_role_labels:
        pitcher_name = st.session_state.get(rotation_key, "")
        if not pitcher_name:
            continue
        usage_cols = st.columns([1.2, 1.4])
        with usage_cols[0]:
            st.markdown(f"**{rotation_label}: {pitcher_name}**")
        with usage_cols[1]:
            usage = st.text_input(
                f"{rotation_label} usage",
                key=f"card_pitch_usage_{rotation_key}",
                placeholder="1 inning / 1-2 innings"
            )
        lineup_card_pitchers.append({"Role": rotation_label, "Pitcher": pitcher_name, "Usage": usage})

    lineup_card_notes = st.text_area(
        "Lineup card notes",
        key="lineup_card_notes",
        placeholder="Baserunning reminders, defensive priorities, matchup notes..."
    )

    logo_uri = file_to_data_uri(os.path.join(os.getcwd(), "barons_logo.png"))
    card_meta = {
        "game": lineup_card_game,
        "date": lineup_card_date,
        "opponent": lineup_card_opponent,
        "first_pitch": lineup_card_first_pitch,
        "sub_title": lineup_card_sub_title or "Substitutions",
    }
    lineup_card_html = render_lineup_card_html(
        logo_uri,
        card_meta,
        depth_chart_rows,
        card_sub_rows,
        bench_players,
        lineup_card_pitchers,
        lineup_card_notes,
    )

    st.markdown("#### Lineup Card Preview")
    st.markdown(lineup_card_html, unsafe_allow_html=True)
    st.download_button(
        "Download Lineup Card HTML",
        lineup_card_html,
        file_name="barons_lineup_card.html",
        mime="text/html"
    )

    col_save, col_preview = st.columns([1, 2])
    with col_save:
        if st.button("Save Depth Chart Idea"):
            if not depth_chart_name.strip():
                st.error("Add an idea name before saving.")
            else:
                saved_depth_charts[depth_chart_name.strip()] = {
                    "lineup": [
                        {
                            "order": row["Order"],
                            "player": row["Player"],
                            "position": row["Position"]
                        }
                        for row in depth_chart_rows
                    ],
                    "bench": bench_players,
                    "inactive": inactive_players,
                    "notes": depth_chart_notes,
                    "rotation": {
                        **{rotation_key: st.session_state.get(rotation_key, "") for rotation_key, _ in bullpen_role_labels},
                        "notes": rotation_notes,
                    },
                    "lineup_card": {
                        "game": lineup_card_game,
                        "date": lineup_card_date,
                        "opponent": lineup_card_opponent,
                        "first_pitch": lineup_card_first_pitch,
                        "sub_title": lineup_card_sub_title,
                        "notes": lineup_card_notes,
                        "subs": [
                            {
                                "player_in": row["PlayerIn"],
                                "for_label": row["ForLabel"],
                                "player_out": row["PlayerOut"],
                                "pos": row["Pos"],
                            }
                            for row in card_sub_rows
                        ],
                        "pitch_usage": {
                            rotation_key: st.session_state.get(f"card_pitch_usage_{rotation_key}", "")
                            for rotation_key, _ in bullpen_role_labels
                        },
                    },
                }
                save_depth_chart_ideas(saved_depth_charts)
                st.success(f"Saved depth chart idea: {depth_chart_name.strip()}")

        if st.button("Start Fresh"):
            for idx in range(1, 11):
                st.session_state[f"depth_player_{idx}"] = ""
                st.session_state[f"depth_pos_{idx}"] = ""
            st.session_state["depth_chart_notes"] = ""
            st.session_state["depth_chart_bench"] = []
            st.session_state["depth_chart_inactive"] = []
            st.session_state["rotation_notes"] = ""
            st.session_state["lineup_card_game"] = "1"
            st.session_state["lineup_card_date"] = ""
            st.session_state["lineup_card_opponent"] = ""
            st.session_state["lineup_card_first_pitch"] = ""
            st.session_state["lineup_card_sub_title"] = "Substitutions"
            st.session_state["lineup_card_notes"] = ""
            for rotation_key, _ in bullpen_role_labels:
                st.session_state[rotation_key] = ""
                st.session_state[f"card_pitch_usage_{rotation_key}"] = ""
            for idx in range(1, 11):
                st.session_state[f"card_sub_in_{idx}"] = ""
                st.session_state[f"card_sub_for_{idx}"] = ""
                st.session_state[f"card_sub_out_{idx}"] = ""
                st.session_state[f"card_sub_pos_{idx}"] = ""
            st.rerun()

    with col_preview:
        st.markdown("### Lineup Card Preview")
        preview_html = ['<div class="lineup-preview-card">']
        for row in depth_chart_rows:
            player_display = row["Player"] if row["Player"] else '<span class="lineup-preview-empty">Open spot</span>'
            pos_display = row["Position"] if row["Position"] else "--"
            preview_html.append(
                f"""
                <div class="lineup-preview-row">
                    <div class="lineup-preview-order">#{row['Order']}</div>
                    <div class="lineup-preview-player">{player_display}</div>
                    <div class="lineup-preview-pos">{pos_display}</div>
                </div>
                """
            )
        preview_html.append("</div>")
        st.markdown("".join(preview_html), unsafe_allow_html=True)

        if bench_players:
            st.markdown("### Bench")
            st.write(", ".join(bench_players))

        if inactive_players:
            st.markdown("### Out / Inactive")
            st.write(", ".join(inactive_players))

        if rotation_rows:
            st.markdown("### Pitching Plan")
            st.dataframe(pd.DataFrame(rotation_rows), use_container_width=True, hide_index=True)

    if depth_chart_notes.strip():
        st.caption(depth_chart_notes)
    if rotation_notes.strip():
        st.caption(f"Pitching notes: {rotation_notes}")

    # ============================================================
    # GAME EDITOR (ALWAYS VISIBLE)
    # ============================================================
    st.subheader("Edit a Game (Single Player Line)")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No logs available.")
    else:
        # Select date
        dates = sorted(df_logs["Date"].unique())
        sel_date = st.selectbox("Select Date", dates, key="edit_date")

        # Select opponent
        opps = sorted(df_logs[df_logs["Date"] == sel_date]["Opponent"].unique())
        sel_opp = st.selectbox("Select Opponent", opps, key="edit_opp")

        # Filter rows for that game
        game_rows = df_logs[
            (df_logs["Date"] == sel_date) &
            (df_logs["Opponent"] == sel_opp)
        ]

        # Select player
        players = sorted(game_rows["Player"].unique())
        sel_player = st.selectbox("Select Player", players, key="edit_player")

        # Select type
        types = sorted(game_rows[game_rows["Player"] == sel_player]["Type"].unique())
        sel_type = st.selectbox("Stat Type", types, key="edit_type")

        # Load row
        row = game_rows[
            (game_rows["Player"] == sel_player) &
            (game_rows["Type"] == sel_type)
        ].iloc[0]

        st.markdown("### Edit Stats")

        if sel_type == "H":
            AB = st.number_input("AB", min_value=0, value=int(row["AB"]))
            H = st.number_input("H", min_value=0, value=int(row["H"]))
            _2B = st.number_input("2B", min_value=0, value=int(row["2B"]))
            _3B = st.number_input("3B", min_value=0, value=int(row["3B"]))
            HR = st.number_input("HR", min_value=0, value=int(row["HR"]))
            BB = st.number_input("BB", min_value=0, value=int(row["BB"]))
            K = st.number_input("K", min_value=0, value=int(row["K"]))
            HBP = st.number_input("HBP", min_value=0, value=int(row["HBP"]))
            SF = st.number_input("SF", min_value=0, value=int(row["SF"]))
            SB = st.number_input("SB", min_value=0, value=int(row["SB"]))

            if st.button("Save Changes", key="save_hit_edit"):
                df_logs.loc[row.name, ["AB","H","2B","3B","HR","BB","K","HBP","SF","SB"]] = \
                    [AB,H,_2B,_3B,HR,BB,K,HBP,SF,SB]

                # Recompute PA
                df_logs.loc[row.name, "PA"] = AB + BB + HBP + SF

                df_logs.to_csv(MASTER_LOG_FILE, index=False)
                rebuild_cumulative_from_logs(df_logs)
                st.success("Hitting line updated.")

        else:  # Pitching
            IP = st.number_input("IP", min_value=0.0, value=float(row["IP"]))
            R = st.number_input("R", min_value=0, value=int(row["R"]))
            ER = st.number_input("ER", min_value=0, value=int(row["ER"]))
            SO = st.number_input("SO", min_value=0, value=int(row["SO"]))
            BB_p = st.number_input("BB", min_value=0, value=int(row["BB_p"]))
            HR_p = st.number_input("HR Allowed", min_value=0, value=int(row["HR_p"]))
            HBP_p = st.number_input("HBP", min_value=0, value=int(row["HBP_p"]))

            if st.button("Save Changes", key="save_pitch_edit"):
                df_logs.loc[row.name, ["IP","R","ER","SO","BB_p","HR_p","HBP_p"]] = \
                    [IP,R,ER,SO,BB_p,HR_p,HBP_p]

                df_logs.to_csv(MASTER_LOG_FILE, index=False)
                rebuild_cumulative_from_logs(df_logs)
                st.success("Pitching line updated.")

    # ============================================================
    # GAME CONTEXT (FOR NEW GAME ENTRY)
    # ============================================================
    st.subheader("Game Context (For New Game Entry)")
    with st.form("game_context_form"):
        date = st.text_input("Game date (YYYY-MM-DD)")
        opponent = st.text_input("Opponent")
        league_game = st.checkbox("League game?")
        submitted_ctx = st.form_submit_button("Set Game Context")

    if not date or not opponent:
        st.info("Set game context above to enable stat entry.")
        st.stop()

    st.write(f"Current game: **{date} vs {opponent}** ({'League' if league_game else 'Non-league'})")

    # ============================================================
    # LINEUP BUILDER
    # ============================================================
    st.subheader("Lineup Builder")

    num_hitters = st.selectbox("Number of hitters in lineup:", list(range(9, 21)), index=0)

    st.markdown("### Starting Lineup (Batting Order)")
    lineup = []
    for i in range(1, num_hitters + 1):
        col1, col2 = st.columns([2, 1])
        with col1:
            player = st.selectbox(f"#{i} Batter", sorted(PLAYERS.keys()), key=f"bo_{i}")
        with col2:
            pos = st.text_input(f"Pos #{i}", key=f"pos_{i}")
        lineup.append({"order": i, "player": player, "position": pos})

    st.markdown("### Bench Players")
    bench_players = st.multiselect(
        "Available bench players:",
        sorted(PLAYERS.keys()),
        key="bench_list"
    )

    # ============================================================
    # SUBSTITUTIONS
    # ============================================================
    st.subheader("In-Game Substitutions")

    subs = []
    num_subs = st.number_input("Number of substitutions:", min_value=0, max_value=20, step=1)

    for i in range(num_subs):
        st.markdown(f"**Substitution #{i+1}**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            out_player = st.selectbox("Player Out", sorted(PLAYERS.keys()), key=f"sub_out_{i}")
        with col2:
            in_player = st.selectbox("Player In", sorted(PLAYERS.keys()), key=f"sub_in_{i}")
        with col3:
            inning = st.number_input("Inning Entered", min_value=1, max_value=9, step=1, key=f"sub_inn_{i}")
        with col4:
            new_pos = st.text_input("New Position", key=f"sub_pos_{i}")

        subs.append({
            "out": out_player,
            "in": in_player,
            "inning": inning,
            "position": new_pos
        })

    # ============================================================
    # PINCH HITTERS
    # ============================================================
    st.subheader("Pinch Hitters")

    pinch_hits = []
    num_ph = st.number_input("Number of pinch hitters:", min_value=0, max_value=20, step=1)

    for i in range(num_ph):
        st.markdown(f"**Pinch Hitter #{i+1}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            ph = st.selectbox("Pinch Hitter", sorted(PLAYERS.keys()), key=f"ph_{i}")
        with col2:
            for_player = st.selectbox("Hit For", sorted(PLAYERS.keys()), key=f"ph_for_{i}")
        with col3:
            inning = st.number_input("Inning", min_value=1, max_value=9, step=1, key=f"ph_inn_{i}")

        pinch_hits.append({
            "ph": ph,
            "for": for_player,
            "inning": inning
        })

    # ============================================================
    # FULL GAME BOX SCORE ENTRY (UP TO 20 HITTERS)
    # ============================================================
    st.subheader("Full Game Box Score Entry")

    st.markdown("### Select Hitters for This Game")
    selected_hitters = st.multiselect(
        "Choose hitters (in batting order):",
        sorted(PLAYERS.keys()),
        max_selections=num_hitters
    )

    if len(selected_hitters) != num_hitters:
        st.warning(f"Select exactly {num_hitters} hitters to continue.")
        st.stop()

    st.markdown("### Select Pitchers for This Game")
    selected_pitchers = st.multiselect(
        "Choose pitchers:",
        sorted(PLAYERS.keys()),
    )

    # ---------------- FULL BOX SCORE FORM ----------------
    with st.form("full_game_box_score"):

        # ---------------- HITTING ----------------
        st.write("## Hitting Box Score")

        hit_inputs = {}
        for player in selected_hitters:
            st.markdown(f"**{player}**")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                AB = st.number_input(f"AB ({player})", min_value=0, step=1, key=f"AB_{player}")
            with c2:
                H = st.number_input(f"H ({player})", min_value=0, step=1, key=f"H_{player}")
            with c3:
                _2B = st.number_input(f"2B ({player})", min_value=0, step=1, key=f"2B_{player}")
            with c4:
                _3B = st.number_input(f"3B ({player})", min_value=0, step=1, key=f"3B_{player}")
            with c5:
                HR = st.number_input(f"HR ({player})", min_value=0, step=1, key=f"HR_{player}")
            with c6:
                BB = st.number_input(f"BB ({player})", min_value=0, step=1, key=f"BB_{player}")

            c7, c8, c9, c10, c11 = st.columns(5)
            with c7:
                K = st.number_input(f"K ({player})", min_value=0, step=1, key=f"K_{player}")
            with c8:
                RBI = st.number_input(f"RBI ({player})", min_value=0, step=1, key=f"RBI_{player}")
            with c9:
                HBP = st.number_input(f"HBP ({player})", min_value=0, step=1, key=f"HBP_{player}")
            with c10:
                SF = st.number_input(f"SF ({player})", min_value=0, step=1, key=f"SF_{player}")
            with c11:
                SB = st.number_input(f"SB ({player})", min_value=0, step=1, key=f"SB_{player}")

            hit_inputs[player] = {
                "AB": AB, "H": H, "2B": _2B, "3B": _3B, "HR": HR, "RBI": RBI,
                "BB": BB, "K": K, "HBP": HBP, "SF": SF, "SB": SB
            }

        st.write("---")

        # ---------------- PITCHING ----------------
        st.write("## Pitching Box Score")

        pit_inputs = {}
        for player in selected_pitchers:
            st.markdown(f"**{player}**")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                IP = st.number_input(f"IP ({player})", min_value=0.0, step=0.1, key=f"IP_{player}")
            with c2:
                R = st.number_input(f"R ({player})", min_value=0, step=1, key=f"R_{player}")
            with c3:
                ER = st.number_input(f"ER ({player})", min_value=0, step=1, key=f"ER_{player}")
            with c4:
                BB_p = st.number_input(f"BB ({player})", min_value=0, step=1, key=f"BBp_{player}")

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                SO = st.number_input(f"K ({player})", min_value=0, step=1, key=f"SO_{player}")
            with c6:
                HR_p = st.number_input(f"HR Allowed ({player})", min_value=0, step=1, key=f"HRp_{player}")
            with c7:
                HBP_p = st.number_input(f"HBP ({player})", min_value=0, step=1, key=f"HBPp_{player}")
            with c8:
                GS = st.number_input(f"GS ({player})", min_value=0, max_value=1, step=1, key=f"GS_{player}")

            c9, c10, c11, c12 = st.columns(4)
            with c9:
                W = st.number_input(f"W ({player})", min_value=0, max_value=1, step=1, key=f"W_{player}")
            with c10:
                L = st.number_input(f"L ({player})", min_value=0, max_value=1, step=1, key=f"L_{player}")
            with c11:
                SV = st.number_input(f"SV ({player})", min_value=0, max_value=1, step=1, key=f"SV_{player}")
            with c12:
                PC = st.number_input(f"Pitch Count ({player})", min_value=0, step=1, key=f"PC_{player}")

            pit_inputs[player] = {
                "IP": IP, "R": R, "ER": ER, "SO": SO,
                "BB_p": BB_p, "HR_p": HR_p, "HBP_p": HBP_p,
                "GS": GS, "W": W, "L": L, "SV": SV,
                "PC": PC
            }

        submit_full = st.form_submit_button("Submit Full Game Box Score")

    # ---------------- SUBMISSION LOGIC ----------------
    if submit_full:

        # Hitting
        for player, stats in hit_inputs.items():
            if sum(stats.values()) > 0:
                csv_name = DISPLAY_TO_CSV_NAME.get(player, player)
                update_hitter_cumulative(csv_name, stats)
                log_hitting(date, opponent, league_game, csv_name, stats)

        # Pitching
        for player, stats in pit_inputs.items():
            if stats["IP"] > 0 or stats["R"] > 0 or stats["ER"] > 0:
                csv_name = DISPLAY_TO_CSV_NAME.get(player, player)
                update_pitcher_cumulative(csv_name, stats)
                log_pitching(date, opponent, league_game, csv_name, stats)

        st.success("Full game box score recorded for all players.")

    # ============================================================
    # DELETE ENTRY TOOL
    # ============================================================
    st.subheader("Remove a Stat Entry")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No logs to edit.")
    else:
        df_logs["Label"] = df_logs.apply(
            lambda r: f"{r['Date']} vs {r['Opponent']} — {r['Player']} ({r['Type']})",
            axis=1
        )

        entry = st.selectbox("Select entry to remove", df_logs["Label"])

        if st.button("Remove Selected Entry"):
            idx = df_logs[df_logs["Label"] == entry].index[0]
            df_logs = df_logs.drop(idx)
            df_logs.to_csv(MASTER_LOG_FILE, index=False)

            rebuild_cumulative_from_logs(df_logs)

            st.success("Entry removed and stats recalculated.")

# ---------- TAB 2: TEAM CALENDAR ----------
with tab2:
    st.header("Team Calendar")

    EMBED_URL = "https://calendar.google.com/calendar/embed?src=ac16d5a59cd0ddef373439ba781cf326390b134ef8f52790edb33f57e92c6e7b%40group.calendar.google.com&ctz=America%2FNew_York"

    st.components.v1.iframe(EMBED_URL, width=800, height=600)
