import streamlit as st
import pandas as pd
import os
from io import StringIO

# ============================
# CONFIG
# ============================

CUMULATIVE_FILE = "ct_barons_stats.csv"
MASTER_LOG_FILE = "game_logs.csv"
GAME_LOG_DIR = "logs"
COACH_PASSWORD = "Murphy200"

os.makedirs(GAME_LOG_DIR, exist_ok=True)

st.set_page_config(page_title="CT Barons Dashboard", layout="wide")

# ============================
# ROSTER
# ============================

PLAYERS = {
    # Infielders
    "Oliver Merced": "1B",
    "Antonio Galiza": "C/1B",
    "Charlie Ellis": "OF/1B",
    "Liam DaSilva": "C/1B",
    "Henry Silva": "UTIL",
    "Brett Davino": "UTIL",
    "Mason Kuckinski": "UTIL",
    "Nick Dorso": "UTIL",
    "Mo Hood": "UTIL",
    # Catchers
    "Joel Strand": "C",
    "Brandon Skerritt": "C",
    # Outfielders
    "Jack Farnen": "OF",
    "Adien O'Laughlin": "OF",
    "Nick Carlucci": "OF",
    "Mike Fischetti": "OF",
    "Staller": "OF",
    # Pitchers
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

# Normalize duplicate names for dropdown vs CSV
DISPLAY_TO_CSV_NAME = {
    "Antonio Galiza": "Antonio Galiza",
    "Antonio Galiza (C)": "Antonio Galiza",
    "Liam DaSilva": "Liam DaSilva",
    "Liam DaSilva (C)": "Liam DaSilva",
    "Charlie Ellis": "Charlie Ellis",
    "Charlie Ellis (OF)": "Charlie Ellis",
}
CSV_NAME_TO_POS = {
    "Antonio Galiza": "1B/C",
    "Liam DaSilva": "1B/C",
    "Charlie Ellis": "1B/OF",
}
# For others, use PLAYERS mapping directly


# ============================
# SESSION STATE
# ============================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# ============================
# CUMULATIVE STATS HELPERS
# ============================

def ensure_cumulative_exists():
    if os.path.exists(CUMULATIVE_FILE):
        return

    # Initialize hitters and pitchers with zero stats
    hitter_rows = []
    pitcher_rows = []

    for disp_name, pos in PLAYERS.items():
        csv_name = DISPLAY_TO_CSV_NAME.get(disp_name, disp_name)
        base_pos = CSV_NAME_TO_POS.get(csv_name, pos)

        # Hitter row
        hitter_rows.append({
            "Name": csv_name,
            "Pos": base_pos,
            "AB": 0,
            "H": 0,
            "2B": 0,
            "3B": 0,
            "HR": 0,
            "BB": 0,
            "K": 0,
            "HBP": 0,
            "SF": 0,
            "SB": 0,
            "AVG": 0.0,
            "OBP": 0.0,
            "SLG": 0.0,
            "OPS": 0.0,
            "wOBA": 0.0,
            "K%": 0.0,
            "BB%": 0.0,
        })

        # Pitcher row
        pitcher_rows.append({
            "Name": csv_name,
            "Pos": base_pos,
            "IP": 0.0,
            "R": 0,
            "ER": 0,
            "SO": 0,
            "BB": 0,
            "HR": 0,
            "ERA": 0.0,
            "FIP": 0.0,
        })

    df_hitters = pd.DataFrame(hitter_rows).drop_duplicates(subset=["Name"])
    df_pitchers = pd.DataFrame(pitcher_rows).drop_duplicates(subset=["Name"])

    save_cumulative(df_hitters, df_pitchers)


def load_cumulative():
    if not os.path.exists(CUMULATIVE_FILE):
        return None, None

    with open(CUMULATIVE_FILE, "r") as f:
        lines = f.readlines()

    hitter_lines = []
    pitcher_lines = []
    section = None

    for line in lines:
        line = line.strip()
        if line == "=== HITTERS ===":
            section = "hitters"
            continue
        elif line == "=== PITCHERS ===":
            section = "pitchers"
            continue
        elif line == "":
            continue

        if section == "hitters":
            hitter_lines.append(line)
        elif section == "pitchers":
            pitcher_lines.append(line)

    df_hitters = pd.read_csv(StringIO("\n".join(hitter_lines))) if hitter_lines else None
    df_pitchers = pd.read_csv(StringIO("\n".join(pitcher_lines))) if pitcher_lines else None

    # Backward compatibility: if R missing, assume R = ER
    if df_pitchers is not None and "R" not in df_pitchers.columns:
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

    PA = AB + BB + HBP + SF

    df["AVG"] = H / AB.replace(0, pd.NA)
    df["OBP"] = (H + BB + HBP) / (AB + BB + HBP + SF).replace(0, pd.NA)

    singles = H - _2B - _3B - HR
    TB = singles + 2*_2B + 3*_3B + 4*HR
    df["SLG"] = TB / AB.replace(0, pd.NA)
    df["OPS"] = df["OBP"] + df["SLG"]

    wBB = 0.69
    wHBP = 0.72
    w1B = 0.88
    w2B = 1.247
    w3B = 1.578
    wHR = 2.031

    woba_num = (wBB * BB +
                wHBP * HBP +
                w1B * singles +
                w2B * _2B +
                w3B * _3B +
                wHR * HR)
    woba_den = AB + BB + HBP + SF
    df["wOBA"] = woba_num / woba_den.replace(0, pd.NA)

    df["K%"] = K / PA.replace(0, pd.NA)
    df["BB%"] = BB / PA.replace(0, pd.NA)

    df = df.fillna(0.0)
    return df


def recompute_pitching_metrics(df):
    if df is None or df.empty:
        return df

    IP = df["IP"]
    ER = df["ER"]
    SO = df["SO"]
    BB = df["BB"]
    HR = df["HR"]

    df["ERA"] = (ER * 9) / IP.replace(0, pd.NA)
    df["FIP"] = (13*HR + 3*BB - 2*SO) / IP.replace(0, pd.NA) + 3.1

    df = df.fillna(0.0)
    return df


def update_hitter_cumulative(player_name, stats):
    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    if df_hitters is None:
        return

    mask = df_hitters["Name"] == player_name
    if not mask.any():
        # Add new row if missing
        pos = CSV_NAME_TO_POS.get(player_name, "UTIL")
        new_row = {
            "Name": player_name,
            "Pos": pos,
            "AB": 0,
            "H": 0,
            "2B": 0,
            "3B": 0,
            "HR": 0,
            "BB": 0,
            "K": 0,
            "HBP": 0,
            "SF": 0,
            "SB": 0,
            "AVG": 0.0,
            "OBP": 0.0,
            "SLG": 0.0,
            "OPS": 0.0,
            "wOBA": 0.0,
            "K%": 0.0,
            "BB%": 0.0,
        }
        df_hitters = pd.concat([df_hitters, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_hitters["Name"] == player_name

    for col in ["AB", "H", "2B", "3B", "HR", "BB", "K", "HBP", "SF", "SB"]:
        df_hitters.loc[mask, col] += stats[col]

    df_hitters = recompute_hitting_metrics(df_hitters)
    df_pitchers = recompute_pitching_metrics(df_pitchers) if df_pitchers is not None else None
    save_cumulative(df_hitters, df_pitchers)


def update_pitcher_cumulative(player_name, stats):
    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    if df_pitchers is None:
        return

    mask = df_pitchers["Name"] == player_name
    if not mask.any():
        pos = CSV_NAME_TO_POS.get(player_name, "P")
        new_row = {
            "Name": player_name,
            "Pos": pos,
            "IP": 0.0,
            "R": 0,
            "ER": 0,
            "SO": 0,
            "BB": 0,
            "HR": 0,
            "ERA": 0.0,
            "FIP": 0.0,
        }
        df_pitchers = pd.concat([df_pitchers, pd.DataFrame([new_row])], ignore_index=True)
        mask = df_pitchers["Name"] == player_name

    df_pitchers.loc[mask, "IP"] += stats["IP"]
    df_pitchers.loc[mask, "R"] += stats["R"]
    df_pitchers.loc[mask, "ER"] += stats["ER"]
    df_pitchers.loc[mask, "SO"] += stats["SO"]
    df_pitchers.loc[mask, "BB"] += stats["BB_p"]
    df_pitchers.loc[mask, "HR"] += stats["HR_p"]

    df_pitchers = recompute_pitching_metrics(df_pitchers)
    df_hitters = recompute_hitting_metrics(df_hitters) if df_hitters is not None else None
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
    row = {
        "Date": date,
        "Opponent": opponent,
        "LeagueGame": 1 if league_game else 0,
        "Player": player_name,
        "Type": "H",
        "AB": stats["AB"],
        "H": stats["H"],
        "2B": stats["2B"],
        "3B": stats["3B"],
        "HR": stats["HR"],
        "BB": stats["BB"],
        "K": stats["K"],
        "HBP": stats["HBP"],
        "SF": stats["SF"],
        "SB": stats["SB"],
        "IP": 0.0,
        "R": 0,
        "ER": 0,
        "SO": 0,
        "BB_p": 0,
        "HR_p": 0,
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
        "AB": 0,
        "H": 0,
        "2B": 0,
        "3B": 0,
        "HR": 0,
        "BB": 0,
        "K": 0,
        "HBP": 0,
        "SF": 0,
        "SB": 0,
        "IP": stats["IP"],
        "R": stats["R"],
        "ER": stats["ER"],
        "SO": stats["SO"],
        "BB_p": stats["BB_p"],
        "HR_p": stats["HR_p"],
    }
    game_id = f"{date}_{opponent.replace(' ', '_')}"
    append_to_master_log(row)
    append_to_game_file(game_id, row)


def load_logs():
    if not os.path.exists(MASTER_LOG_FILE):
        return None
    return pd.read_csv(MASTER_LOG_FILE)


def compute_team_hitting_totals(df, league_filter=None):
    if df is None or df.empty:
        return None

    df = df[df["Type"] == "H"]
    if league_filter is not None:
        df = df[df["LeagueGame"] == (1 if league_filter else 0)]
    if df.empty:
        return None

    agg = df[["AB", "H", "2B", "3B", "HR", "BB", "K", "HBP", "SF", "SB"]].sum()

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

    PA = AB + BB + HBP + SF

    AVG = H / AB if AB > 0 else 0
    OBP = (H + BB + HBP) / (AB + BB + HBP + SF) if (AB + BB + HBP + SF) > 0 else 0
    singles = H - _2B - _3B - HR
    TB = singles + 2*_2B + 3*_3B + 4*HR
    SLG = TB / AB if AB > 0 else 0
    OPS = OBP + SLG

    wBB = 0.69
    wHBP = 0.72
    w1B = 0.88
    w2B = 1.247
    w3B = 1.578
    wHR = 2.031

    woba_num = (wBB * BB +
                wHBP * HBP +
                w1B * singles +
                w2B * _2B +
                w3B * _3B +
                wHR * HR)
    woba_den = AB + BB + HBP + SF
    wOBA = woba_num / woba_den if woba_den > 0 else 0

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
        "AVG": AVG,
        "OBP": OBP,
        "SLG": SLG,
        "OPS": OPS,
        "wOBA": wOBA,
        "K%": K_pct,
        "BB%": BB_pct
    }


def compute_team_pitching_totals(df, league_filter=None):
    if df is None or df.empty:
        return None

    df = df[df["Type"] == "P"]
    if league_filter is not None:
        df = df[df["LeagueGame"] == (1 if league_filter else 0)]
    if df.empty:
        return None

    agg = df[["IP", "R", "ER", "SO", "BB_p", "HR_p"]].sum()

    IP = agg["IP"]
    R = agg["R"]
    ER = agg["ER"]
    SO = agg["SO"]
    BB_p = agg["BB_p"]
    HR_p = agg["HR_p"]

    ERA = (ER * 9) / IP if IP > 0 else 0
    FIP = (13*HR_p + 3*BB_p - 2*SO) / IP + 3.1 if IP > 0 else 0
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


# ============================
# UI: TABS
# ============================

st.title("CT Barons Baseball Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["Cumulative Players", "Team Totals", "Game Logs", "Coach Tools"])

# ---------- TAB 1: CUMULATIVE PLAYERS ----------

with tab1:
    st.header("Cumulative Player Stats")

    ensure_cumulative_exists()
    df_hitters, df_pitchers = load_cumulative()

    col1, col2 = st.columns(2)

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

        hit_totals = compute_team_hitting_totals(df_logs, league_filter)
        pit_totals = compute_team_pitching_totals(df_logs, league_filter)

        if hit_totals is None and pit_totals is None:
            st.info("No data for this scope yet.")
        else:
            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Hitting")
                if hit_totals is None:
                    st.write("No hitting data.")
                else:
                    ht = hit_totals
                    st.metric("AVG", f"{ht['AVG']:.3f}")
                    st.metric("OBP", f"{ht['OBP']:.3f}")
                    st.metric("SLG", f"{ht['SLG']:.3f}")
                    st.metric("OPS", f"{ht['OPS']:.3f}")
                    st.metric("wOBA", f"{ht['wOBA']:.3f}")
                    st.write(
                        f"AB: {ht['AB']}, H: {ht['H']}, 2B: {ht['2B']}, 3B: {ht['3B']}, HR: {ht['HR']}"
                    )
                    st.write(
                        f"BB: {ht['BB']}, K: {ht['K']}, HBP: {ht['HBP']}, SF: {ht['SF']}, SB: {ht['SB']}"
                    )
                    st.write(
                        f"K%: {ht['K%']*100:.1f}%, BB%: {ht['BB%']*100:.1f}%"
                    )

            with c2:
                st.subheader("Pitching")
                if pit_totals is None:
                    st.write("No pitching data.")
                else:
                    pt = pit_totals
                    st.metric("ERA", f"{pt['ERA']:.3f}")
                    st.metric("FIP", f"{pt['FIP']:.3f}")
                    st.write(
                        f"IP: {pt['IP']:.1f}, R: {pt['R']}, ER: {pt['ER']}, Unearned: {pt['Unearned']}"
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

# ---------- TAB 4: COACH TOOLS (PASSWORD) ----------

with tab4:
    st.header("Coach Tools (Password Protected)")

    if not st.session_state.authenticated:
        pwd = st.text_input("Enter coach password:", type="password")
        if st.button("Unlock"):
            if pwd == COACH_PASSWORD:
                st.session_state.authenticated = True
                st.success("Coach mode unlocked.")
            else:
                st.error("Incorrect password.")
    else:
        st.success("Coach mode active.")

        st.subheader("Game Context")
        with st.form("game_context_form"):
            date = st.text_input("Game date (YYYY-MM-DD)")
            opponent = st.text_input("Opponent")
            league_game = st.checkbox("League game?")
            submitted_ctx = st.form_submit_button("Set Game Context")

        if not date or not opponent:
            st.info("Set game context above to enable stat entry.")
        else:
            st.write(f"Current game: **{date} vs {opponent}** ({'League' if league_game else 'Non-league'})")

            st.subheader("Enter Player Stats")

            colh, colp = st.columns(2)

            # HITTING FORM
            with colh:
                st.markdown("### Hitting Stats")
                with st.form("hitting_form"):
                    player_disp = st.selectbox("Hitter", sorted(PLAYERS.keys()))
                    AB = st.number_input("AB", min_value=0, step=1)
                    H = st.number_input("H", min_value=0, step=1)
                    _2B = st.number_input("2B", min_value=0, step=1)
                    _3B = st.number_input("3B", min_value=0, step=1)
                    HR = st.number_input("HR", min_value=0, step=1)
                    BB = st.number_input("BB", min_value=0, step=1)
                    K = st.number_input("K", min_value=0, step=1)
                    HBP = st.number_input("HBP", min_value=0, step=1)
                    SF = st.number_input("SF", min_value=0, step=1)
                    SB = st.number_input("SB", min_value=0, step=1)
                    submit_hit = st.form_submit_button("Submit Hitting Stats")

                if submit_hit:
                    csv_name = DISPLAY_TO_CSV_NAME.get(player_disp, player_disp)
                    stats = {
                        "AB": int(AB),
                        "H": int(H),
                        "2B": int(_2B),
                        "3B": int(_3B),
                        "HR": int(HR),
                        "BB": int(BB),
                        "K": int(K),
                        "HBP": int(HBP),
                        "SF": int(SF),
                        "SB": int(SB),
                    }
                    update_hitter_cumulative(csv_name, stats)
                    log_hitting(date, opponent, league_game, csv_name, stats)
                    st.success(f"Hitting stats recorded for {csv_name}.")

            # PITCHING FORM
            with colp:
                st.markdown("### Pitching Stats")
                with st.form("pitching_form"):
                    player_disp_p = st.selectbox("Pitcher", sorted(PLAYERS.keys()), key="pitcher_select")
                    IP = st.number_input("IP (e.g., 5.2)", min_value=0.0, step=0.1)
                    R = st.number_input("R (total runs)", min_value=0, step=1)
                    ER = st.number_input("ER (earned runs)", min_value=0, step=1)
                    SO = st.number_input("SO", min_value=0, step=1)
                    BB_p = st.number_input("BB", min_value=0, step=1)
                    HR_p = st.number_input("HR allowed", min_value=0, step=1)
                    submit_pit = st.form_submit_button("Submit Pitching Stats")

                if submit_pit:
                    csv_name_p = DISPLAY_TO_CSV_NAME.get(player_disp_p, player_disp_p)
                    stats_p = {
                        "IP": float(IP),
                        "R": int(R),
                        "ER": int(ER),
                        "SO": int(SO),
                        "BB_p": int(BB_p),
                        "HR_p": int(HR_p),
                    }
                    update_pitcher_cumulative(csv_name_p, stats_p)
                    log_pitching(date, opponent, league_game, csv_name_p, stats_p)
                    st.success(f"Pitching stats recorded for {csv_name_p}.")
