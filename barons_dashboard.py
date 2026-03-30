import streamlit as st
import pandas as pd
import os
from io import StringIO
from PIL import Image
import base64

# ============================
# CONFIG
# ============================

CUMULATIVE_FILE = "ct_barons_stats.csv"
MASTER_LOG_FILE = "game_logs.csv"
GAME_LOG_DIR = "logs"
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
        "AB", "H", "2B", "3B", "HR",
        "BB", "K", "HBP", "SF", "SB",
        "PA",   # <-- ADDED PA

        # Pitching
        "IP", "R", "ER", "SO",
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
    "Oliver Merced": "1B",
    "Antonio Galiza": "C/1B",
    "Charlie Ellis": "OF/1B",
    "Liam DaSilva": "C/1B",
    "Henry Silva": "UTIL",
    "Brett Davino": "UTIL",
    "Mason Kuckinski": "UTIL",
    "Nick Dorso": "UTIL",
    "Mo Hood": "UTIL",
    "Joel Strand": "C",
    "Brandon Skerritt": "C",
    "Jack Farnen": "OF",
    "Adien O'Laughlin": "OF",
    "Nick Carlucci": "OF",
    "Mike Fischetti": "OF",
    "Staller": "OF",
    "Tristan Pearl": "P",
    "Nevin Belanger": "P",
    "Tommy Burgers": "P",
    "Niko Christon": "P",
    "Colin D'onofrio": "P",
    "Jack Jenson": "P",
    "Merritt Hole": "P",
    "Nick Hios": "P",
    "James Aselta": "P",
    "Nick Petta": "P",
    "Christan Barboto": "P",
    "Adam Rosenfield": "P",
    "Branden Gaska": "P",
    "Tyler Easterbrook": "P",
}

DISPLAY_TO_CSV_NAME = {
    "Antonio Galiza": "Antonio Galiza",
    "Liam DaSilva": "Liam DaSilva",
    "Charlie Ellis": "Charlie Ellis",
}

CSV_NAME_TO_POS = {
    "Antonio Galiza": "1B/C",
    "Liam DaSilva": "1B/C",
    "Charlie Ellis": "1B/OF",
}

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

    agg = df[["IP", "R", "ER", "SO", "BB_p", "HR_p", "HBP_p"]].sum()

    IP = agg["IP"]
    R = agg["R"]
    ER = agg["ER"]
    SO = agg["SO"]
    BB_p = agg["BB_p"]
    HR_p = agg["HR_p"]

    ERA = (ER * 9) / IP if IP > 0 else 0
    FIP = ((13 * HR_p) + (3 * BB_p) - (2 * SO)) / IP + 3.1 if IP > 0 else 0
    Unearned = R - ER

    return {
        "IP": IP,
        "R": R,
        "ER": ER,
        "Unearned": Unearned,
        "SO": SO,
        "BB": BB_p,
        "HR": HR_p,
        "ERA": ERA,
        "FIP": FIP
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
    required_cols = ["AB","H","2B","3B","HR","BB","K","HBP","SF","SB","PA"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    agg = df[required_cols].sum()

    AB = agg["AB"]
    H = agg["H"]
    _2B = agg["2B"]
    _3B = agg["3B"]
    HR = agg["HR"]
    BB = agg["BB"]
    K = agg["K"]
    HBP = agg["HBP"]
    SF = agg["SF"]
    SB = agg["SB"]
    PA = agg["PA"]

    AVG = H / AB if AB > 0 else 0
    OBP = (H + BB + HBP) / PA if PA > 0 else 0

    singles = H - _2B - _3B - HR
    TB = singles + 2*_2B + 3*_3B + 4*HR
    SLG = TB / AB if AB > 0 else 0
    OPS = OBP + SLG

    woba_num = (
        0.69 * BB +
        0.72 * HBP +
        0.88 * singles +
        1.247 * _2B +
        1.578 * _3B +
        2.031 * HR
    )
    wOBA = woba_num / PA if PA > 0 else 0

    K_pct = K / PA if PA > 0 else 0
    BB_pct = BB / PA if PA > 0 else 0

    return {
        "AB": AB,
        "H": H,
        "2B": _2B,
        "3B": _3B,
        "HR": HR,
        "BB": BB,
        "K": K,
        "HBP": HBP,
        "SF": SF,
        "SB": SB,
        "PA": PA,
        "AVG": AVG,
        "OBP": OBP,
        "SLG": SLG,
        "OPS": OPS,
        "wOBA": wOBA,
        "K%": K_pct,
        "BB%": BB_pct
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
            "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0,
            "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
            "PA": 0,   # <-- ADDED
            "AVG": 0.0, "OBP": 0.0, "SLG": 0.0, "OPS": 0.0,
            "wOBA": 0.0, "K%": 0.0, "BB%": 0.0,
        })

        pitcher_rows.append({
            "Name": csv_name,
            "Pos": base_pos,
            "IP": 0.0, "R": 0, "ER": 0, "SO": 0,
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

    IP = df["IP"]
    ER = df["ER"]
    SO = df["SO"]
    BB_p = df["BB_p"]
    HR_p = df["HR_p"]

    df["ERA"] = (ER * 9) / IP.replace(0, pd.NA)
    df["FIP"] = (13*HR_p + 3*BB_p - 2*SO) / IP.replace(0, pd.NA) + 3.1

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
            "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0,
            "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
            "PA": 0,   # <-- ADDED
            "AVG": 0.0, "OBP": 0.0, "SLG": 0.0, "OPS": 0.0,
            "wOBA": 0.0, "K%": 0.0, "BB%": 0.0,
        }
        df_hitters = pd.concat([df_hitters, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_hitters["Name"] == player_name

    # Add raw counting stats
    for col in stats:
        df_hitters.loc[mask, col] += stats[col]

    # Add PA from this game
    df_hitters.loc[mask, "PA"] += (
        stats.get("AB", 0)
        + stats.get("BB", 0)
        + stats.get("HBP", 0)
        + stats.get("SF", 0)
    )

    # Recompute all metrics (including authoritative PA)
    df_hitters = recompute_hitting_metrics(df_hitters)
    df_pitchers = recompute_pitching_metrics(df_pitchers)

    save_cumulative(df_hitters, df_pitchers)



def update_pitcher_cumulative(player_name, stats):
    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    if df_pitchers is None:
        df_pitchers = pd.DataFrame(columns=[
            "Name", "Pos", "IP", "R", "ER", "SO",
            "BB_p", "HR_p", "HBP_p", "ERA", "FIP"
        ])

    mask = df_pitchers["Name"] == player_name
    if not mask.any():
        pos = CSV_NAME_TO_POS.get(player_name, "P")
        new_row = {
            "Name": player_name,
            "Pos": pos,
            "IP": 0.0, "R": 0, "ER": 0, "SO": 0,
            "BB_p": 0, "HR_p": 0, "HBP_p": 0,
            "ERA": 0.0, "FIP": 0.0,
        }
        df_pitchers = pd.concat([df_pitchers, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_pitchers["Name"] == player_name

    # Ensure columns exist
    for col in ["IP", "R", "ER", "SO", "BB_p", "HR_p", "HBP_p"]:
        if col not in df_pitchers.columns:
            df_pitchers[col] = 0

    df_pitchers.loc[mask, "IP"] += stats["IP"]
    df_pitchers.loc[mask, "R"] += stats["R"]
    df_pitchers.loc[mask, "ER"] += stats["ER"]
    df_pitchers.loc[mask, "SO"] += stats["SO"]
    df_pitchers.loc[mask, "BB_p"] += stats["BB_p"]
    df_pitchers.loc[mask, "HR_p"] += stats["HR_p"]
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

        # Hitting stats from the form
        **stats,

        # Add PA
        "PA": PA,

        # Pitching placeholders
        "IP": 0.0,
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
    row = {
        "Date": date,
        "Opponent": opponent,
        "LeagueGame": 1 if league_game else 0,
        "Player": player_name,
        "Type": "P",
        "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0,
        "BB": 0, "K": 0, "HBP": 0, "SF": 0, "SB": 0,
        **stats,  # must include IP, R, ER, SO, BB_p, HR_p, HBP_p
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
                "AB": row["AB"],
                "H": row["H"],
                "2B": row["2B"],
                "3B": row["3B"],
                "HR": row["HR"],
                "BB": row["BB"],
                "K": row["K"],
                "HBP": row["HBP"],
                "SF": row["SF"],
                "SB": row["SB"],
                "PA": row["PA"],   # <-- ADDED PA
            }
            update_hitter_cumulative(row["Player"], stats)

        else:  # Pitching
            stats = {
                "IP": row["IP"],
                "R": row["R"],
                "ER": row["ER"],
                "SO": row["SO"],
                "BB_p": row["BB_p"],
                "HR_p": row["HR_p"],
                "HBP_p": row.get("HBP_p", 0),
            }
            update_pitcher_cumulative(row["Player"], stats)




ROSTER_DATA = [
    {"Number": 11, "Name": "Oliver Merced", "Position": "1B", "Bats": "L", "Throws": "R", "School": "Amherst", "Year": "Senior"},
    {"Number": 10, "Name": "Antonio Galiza", "Position": "C/1B", "Bats": "R", "Throws": "R", "School": "Western NE.", "Year": "Senior"},
    {"Number": 16, "Name": "Charlie Ellis", "Position": "OF/1B", "Bats": "L", "Throws": "L", "School": "Stevens IT", "Year": "Freshman"},
    {"Number": 41, "Name": "Liam DaSilva", "Position": "C/1B", "Bats": "R", "Throws": "R", "School": "Dean College", "Year": "Freshman"},
    {"Number": 8, "Name": "Henry Silva", "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Colby", "Year": "Junior"},
    {"Number": 50, "Name": "Brett Davino", "Position": "UTIL", "Bats": "L", "Throws": "R", "School": "Stony Brook", "Year": "Senior"},
    {"Number": 6, "Name": "Mason Kuckinski", "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Saint Anselm", "Year": "Freshman"},
    {"Number": 7, "Name": "Nick Dorso", "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Roanoke", "Year": "Sophomore"},
    {"Number": 22, "Name": "Mo Hood", "Position": "UTIL", "Bats": "R", "Throws": "R", "School": "Wash U", "Year": "Freshman"},
    {"Number": 27, "Name": "Joel Strand", "Position": "C", "Bats": "R", "Throws": "R", "School": "Illinois Wesleyan", "Year": "Junior"},
    {"Number": 69, "Name": "Brandon Skerritt", "Position": "C", "Bats": "R", "Throws": "R", "School": "Bentley", "Year": "Freshman"},
    {"Number": 9, "Name": "Jack Farnen", "Position": "OF", "Bats": "L", "Throws": "L", "School": "Hobart", "Year": "Junior"},
    {"Number": 24, "Name": "Adien O'Laughlin", "Position": "OF", "Bats": "R", "Throws": "R", "School": "Trinity", "Year": "Freshman"},
    {"Number": 15, "Name": "Nick Carlucci", "Position": "OF", "Bats": "R", "Throws": "R", "School": "Pace", "Year": "Senior"},
    {"Number": 23, "Name": "Mike Fischetti", "Position": "OF", "Bats": "L", "Throws": "R", "School": "Gettysburg", "Year": "Junior"},
    {"Number": 33, "Name": "Staller", "Position": "OF", "Bats": "R", "Throws": "R", "School": "?", "Year": "?"},

    # Pitchers
    {"Number": 30, "Name": "Tristan Pearl", "Position": "P", "Bats": "L", "Throws": "L", "School": "Babson", "Year": "Senior"},
    {"Number": 17, "Name": "Nevin Belanger", "Position": "P", "Bats": "L", "Throws": "L", "School": "Johnson and Wales", "Year": "Senior"},
    {"Number": 20, "Name": "Tommy Burgers", "Position": "P", "Bats": "R", "Throws": "R", "School": "Gettysburg", "Year": "Junior"},
    {"Number": 89, "Name": "Niko Christon", "Position": "P", "Bats": "R", "Throws": "R", "School": "CCSU", "Year": "Junior"},
    {"Number": 34, "Name": "Colin D'onofrio", "Position": "P", "Bats": "R", "Throws": "R", "School": "SUNY Purchase", "Year": "Junior"},
    {"Number": 19, "Name": "Jack Jenson", "Position": "P", "Bats": "R", "Throws": "R", "School": "Bentley", "Year": "Sophomore"},
    {"Number": 18, "Name": "Merritt Hole", "Position": "P", "Bats": "R", "Throws": "R", "School": "Lafayette", "Year": "Sophomore"},
    {"Number": 40, "Name": "Nick Hios", "Position": "P", "Bats": "L", "Throws": "L", "School": "Monmouth", "Year": "Senior"},
    {"Number": 1, "Name": "James Aselta", "Position": "P", "Bats": "R", "Throws": "R", "School": "Sacred Heart", "Year": "Senior"},
    {"Number": 72, "Name": "Nick Petta", "Position": "P", "Bats": "R", "Throws": "R", "School": "Roger Williams", "Year": "Freshman"},
    {"Number": 5, "Name": "Christan Barboto", "Position": "P", "Bats": "R", "Throws": "R", "School": "Emory", "Year": "Freshman"},
    {"Number": 58, "Name": "Adam Rosenfield", "Position": "P", "Bats": "R", "Throws": "R", "School": "Montclair St.", "Year": "Sophomore"},
    {"Number": 42, "Name": "Branden Gaska", "Position": "P", "Bats": "R", "Throws": "R", "School": "Westfield St.", "Year": "Freshman"},
    {"Number": 35, "Name": "Tyler Easterbrook", "Position": "P", "Bats": "R", "Throws": "R", "School": "Tufts", "Year": "Freshman"},
]



# ============================
# UI TABS
# ============================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Cumulative Players",
    "Team Totals",
    "Game Logs",
    "Player Profiles",
    "Roster",
    "Coach Tools",
])


# ---------- TAB 1: CUMULATIVE PLAYERS ----------

with tab1:
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
            st.dataframe(
                df_hitters.style.format({
                    "AVG": "{:.3f}",
                    "OBP": "{:.3f}",
                    "SLG": "{:.3f}",
                    "OPS": "{:.3f}",
                    "wOBA": "{:.3f}",
                    "K%": "{:.1f}",
                    "BB%": "{:.1f}",
                })
            )

    # Pitchers
    with col2:
        st.subheader("Pitchers")
        if df_pitchers is None or df_pitchers.empty:
            st.info("No pitcher data yet.")
        else:
            df_p = df_pitchers.copy()
            df_p["Unearned"] = df_p["R"] - df_p["ER"]
            st.dataframe(
                df_p.style.format({
                    "IP": "{:.1f}",
                    "ERA": "{:.3f}",
                    "FIP": "{:.3f}",
                })
            )


# ---------- TAB 2: TEAM TOTALS ----------

with tab2:
    st.header("Team Totals (from Game Logs)")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No game logs yet.")
    else:
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

        # Compute totals
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

                    st.metric("AVG", f"{ht['AVG']:.3f}")
                    st.metric("OBP", f"{ht['OBP']:.3f}")
                    st.metric("SLG", f"{ht['SLG']:.3f}")
                    st.metric("OPS", f"{ht['OPS']:.3f}")
                    st.metric("wOBA", f"{ht['wOBA']:.3f}")

                    st.write(
                        f"AB: {ht['AB']}, H: {ht['H']}, 2B: {ht['2B']}, "
                        f"3B: {ht['3B']}, HR: {ht['HR']}"
                    )
                    st.write(
                        f"BB: {ht['BB']}, K: {ht['K']}, HBP: {ht['HBP']}, "
                        f"SF: {ht['SF']}, SB: {ht['SB']}, PA: {ht['PA']}"
                    )
                    st.write(
                        f"K%: {ht['K%']*100:.1f}%, BB%: {ht['BB%']*100:.1f}%"
                    )

            # -------------------------
            # PITCHING TOTALS
            # -------------------------
            with c2:
                st.subheader("Pitching")

                if pit_totals:
                    pt = pit_totals

                    st.metric("ERA", f"{pt['ERA']:.3f}")
                    st.metric("FIP", f"{pt['FIP']:.3f}")

                    st.write(
                        f"IP: {pt['IP']:.1f}, R: {pt['R']}, ER: {pt['ER']}, "
                        f"Unearned: {pt['Unearned']}"
                    )
                    st.write(
                        f"SO: {pt['SO']}, BB: {pt['BB']}, HR: {pt['HR']}"
                    )




# ---------- TAB 3: GAME LOGS ----------

with tab3:
    st.header("Game Logs")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No game logs yet.")
    else:
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

        if player_sel != "All":
            df_view = df_view[df_view["Player"] == player_sel]
        if opp_sel != "All":
            df_view = df_view[df_view["Opponent"] == opp_sel]
        if lg_mode == "League only":
            df_view = df_view[df_view["LeagueGame"] == 1]
        elif lg_mode == "Non-league only":
            df_view = df_view[df_view["LeagueGame"] == 0]

        df_view = df_view.sort_values(["Date", "Player"])
        st.dataframe(df_view)





# ---------- TAB 5: PLAYER PROFILES ----------

with tab4:
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
        st.dataframe(hit_row)

    # Pitching stats
    pit_row = df_pitchers[df_pitchers["Name"] == player]
    if not pit_row.empty:
        st.markdown("### Pitching Stats")
        pit_row = pit_row.copy()
        pit_row["Unearned"] = pit_row["R"] - pit_row["ER"]
        st.dataframe(pit_row)
        
# ---------- TAB 6: ROSTER ----------
with tab5:
    st.header("CT Barons South Roster")

    df_roster = pd.DataFrame(ROSTER_DATA)
    df_roster = df_roster.sort_values("Number")

    st.dataframe(
        df_roster.style.format({
            "Number": "{:d}"
        })
    )

# ---------- TAB 4: COACH TOOLS ----------
with tab6:
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

    # ---------------- TEAM RECORD EDITOR ----------------
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

    # ---------------- GAME CONTEXT ----------------
    st.subheader("Game Context")
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

            c7, c8, c9, c10 = st.columns(4)
            with c7:
                K = st.number_input(f"K ({player})", min_value=0, step=1, key=f"K_{player}")
            with c8:
                HBP = st.number_input(f"HBP ({player})", min_value=0, step=1, key=f"HBP_{player}")
            with c9:
                SF = st.number_input(f"SF ({player})", min_value=0, step=1, key=f"SF_{player}")
            with c10:
                SB = st.number_input(f"SB ({player})", min_value=0, step=1, key=f"SB_{player}")

            hit_inputs[player] = {
                "AB": AB, "H": H, "2B": _2B, "3B": _3B, "HR": HR,
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
    # EDIT A SINGLE PLAYER'S GAME LINE (OPTION C)
    # ============================================================
    st.subheader("Edit a Single Player's Stat Line")

    df_logs = load_logs()
    if df_logs is None or df_logs.empty:
        st.info("No logs available.")
    else:
        # Select game
        dates = sorted(df_logs["Date"].unique())
        sel_date = st.selectbox("Select Date", dates)

        opps = sorted(df_logs[df_logs["Date"] == sel_date]["Opponent"].unique())
        sel_opp = st.selectbox("Select Opponent", opps)

        players = sorted(df_logs[(df_logs["Date"] == sel_date) & (df_logs["Opponent"] == sel_opp)]["Player"].unique())
        sel_player = st.selectbox("Select Player", players)

        types = ["H", "P"]
        sel_type = st.selectbox("Type", types)

        # Load row
        row = df_logs[
            (df_logs["Date"] == sel_date) &
            (df_logs["Opponent"] == sel_opp) &
            (df_logs["Player"] == sel_player) &
            (df_logs["Type"] == sel_type)
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

            if st.button("Save Changes"):
                df_logs.loc[row.name, ["AB","H","2B","3B","HR","BB","K","HBP","SF","SB"]] = \
                    [AB,H,_2B,_3B,HR,BB,K,HBP,SF,SB]

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

            if st.button("Save Changes"):
                df_logs.loc[row.name, ["IP","R","ER","SO","BB_p","HR_p","HBP_p"]] = \
                    [IP,R,ER,SO,BB_p,HR_p,HBP_p]

                df_logs.to_csv(MASTER_LOG_FILE, index=False)
                rebuild_cumulative_from_logs(df_logs)
                st.success("Pitching line updated.")

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
