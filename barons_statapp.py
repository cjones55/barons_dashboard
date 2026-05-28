import pandas as pd
import os
from io import StringIO

# ============================
# 1. PLAYER CLASS
# ============================

class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        
        # Hitting stats (cumulative)
        self.AB = 0
        self.H = 0
        self._2B = 0
        self._3B = 0
        self.HR = 0
        self.BB = 0
        self.K = 0
        self.HBP = 0
        self.SF = 0
        self.SB = 0
        
        # Pitching stats (cumulative)
        self.IP = 0
        self.ER = 0
        self.SO = 0
        self.BB_p = 0
        self.HR_p = 0

    # ============================
    # ADVANCED HITTING METRICS
    # ============================

    def plate_appearances(self):
        return self.AB + self.BB + self.HBP + self.SF

    def batting_average(self):
        return self.H / self.AB if self.AB > 0 else 0

    def obp(self):
        num = self.H + self.BB + self.HBP
        den = self.AB + self.BB + self.HBP + self.SF
        return num / den if den > 0 else 0

    def slg(self):
        singles = self.H - self._2B - self._3B - self.HR
        tb = singles + 2*self._2B + 3*self._3B + 4*self.HR
        return tb / self.AB if self.AB > 0 else 0

    def ops(self):
        return self.obp() + self.slg()

    def woba(self):
        wBB = 0.69
        wHBP = 0.72
        w1B = 0.88
        w2B = 1.247
        w3B = 1.578
        wHR = 2.031

        singles = self.H - self._2B - self._3B - self.HR

        num = (wBB * self.BB +
               wHBP * self.HBP +
               w1B * singles +
               w2B * self._2B +
               w3B * self._3B +
               wHR * self.HR)

        den = self.AB + self.BB + self.HBP + self.SF
        return num / den if den > 0 else 0

    def k_percent(self):
        pa = self.plate_appearances()
        return self.K / pa if pa > 0 else 0

    def bb_percent(self):
        pa = self.plate_appearances()
        return self.BB / pa if pa > 0 else 0

    # ============================
    # ADVANCED PITCHING METRICS
    # ============================

    def era(self):
        if self.IP == 0:
            return 0
        return (self.ER * 9) / self.IP

    def fip(self, constant=3.1):
        if self.IP == 0:
            return 0
        return (13*self.HR_p + 3*self.BB_p - 2*self.SO) / self.IP + constant

    # ============================
    # EXPORT ROWS FOR REPORTS
    # ============================

    def to_hitter_row(self):
        return {
            "Name": self.name,
            "Pos": self.position,
            "AB": self.AB,
            "H": self.H,
            "2B": self._2B,
            "3B": self._3B,
            "HR": self.HR,
            "BB": self.BB,
            "K": self.K,
            "HBP": self.HBP,
            "SF": self.SF,
            "SB": self.SB,
            "AVG": round(self.batting_average(), 3),
            "OBP": round(self.obp(), 3),
            "SLG": round(self.slg(), 3),
            "OPS": round(self.ops(), 3),
            "wOBA": round(self.woba(), 3),
            "K%": round(self.k_percent() * 100, 1),
            "BB%": round(self.bb_percent() * 100, 1)
        }

    def to_pitcher_row(self):
        return {
            "Name": self.name,
            "Pos": self.position,
            "IP": self.IP,
            "ER": self.ER,
            "SO": self.SO,
            "BB": self.BB_p,
            "HR": self.HR_p,
            "ERA": round(self.era(), 3),
            "FIP": round(self.fip(), 3)
        }


# ============================
# 2. GAME LOG MANAGER
# ============================

class GameLogManager:
    def __init__(self, master_log="game_logs.csv", game_dir="logs"):
        self.master_log = master_log
        self.game_dir = game_dir
        os.makedirs(self.game_dir, exist_ok=True)

    def _append_to_master(self, row_dict):
        df_row = pd.DataFrame([row_dict])
        if os.path.exists(self.master_log):
            df_row.to_csv(self.master_log, mode="a", header=False, index=False)
        else:
            df_row.to_csv(self.master_log, mode="w", header=True, index=False)

    def _append_to_game_file(self, game_id, row_dict):
        filename = os.path.join(self.game_dir, f"{game_id}.csv")
        df_row = pd.DataFrame([row_dict])
        if os.path.exists(filename):
            df_row.to_csv(filename, mode="a", header=False, index=False)
        else:
            df_row.to_csv(filename, mode="w", header=True, index=False)

    def log_hitting(self, date, opponent, league_game, player_name, stats):
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
            "ER": 0,
            "SO": 0,
            "BB_p": 0,
            "HR_p": 0
        }
        game_id = f"{date}_{opponent.replace(' ', '_')}"
        self._append_to_master(row)
        self._append_to_game_file(game_id, row)

    def log_pitching(self, date, opponent, league_game, player_name, stats):
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
            "ER": stats["ER"],
            "SO": stats["SO"],
            "BB_p": stats["BB_p"],
            "HR_p": stats["HR_p"]
        }
        game_id = f"{date}_{opponent.replace(' ', '_')}"
        self._append_to_master(row)
        self._append_to_game_file(game_id, row)

    def _load_master(self):
        if not os.path.exists(self.master_log):
            return pd.DataFrame()
        return pd.read_csv(self.master_log)

    # Team totals from logs (overall / league / non-league)
    def team_hitting_totals(self, league_filter=None):
        df = self._load_master()
        if df.empty:
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

    def team_pitching_totals(self, league_filter=None):
        df = self._load_master()
        if df.empty:
            return None

        df = df[df["Type"] == "P"]
        if league_filter is not None:
            df = df[df["LeagueGame"] == (1 if league_filter else 0)]
        if df.empty:
            return None

        agg = df[["IP", "ER", "SO", "BB_p", "HR_p"]].sum()

        IP = agg["IP"]
        ER = agg["ER"]
        SO = agg["SO"]
        BB_p = agg["BB_p"]
        HR_p = agg["HR_p"]

        ERA = (ER * 9) / IP if IP > 0 else 0
        FIP = (13*HR_p + 3*BB_p - 2*SO) / IP + 3.1 if IP > 0 else 0

        return {
            "IP": IP,
            "ER": ER,
            "SO": SO,
            "BB": BB_p,
            "HR": HR_p,
            "ERA": ERA,
            "FIP": FIP
        }


# ============================
# 3. TEAM CLASS
# ============================

class Team:
    def __init__(self, name):
        self.name = name
        self.players = {}

    def add_player(self, player):
        self.players[player.name] = player

    def get_player(self, name):
        return self.players.get(name)

    # ============================
    # PLAYER-LEVEL REPORTS
    # ============================

    def hitter_report(self):
        hitters = []
        for p in self.players.values():
            if p.plate_appearances() > 0:
                hitters.append(p.to_hitter_row())
        return pd.DataFrame(hitters)

    def pitcher_report(self):
        pitchers = []
        for p in self.players.values():
            if p.IP > 0:
                pitchers.append(p.to_pitcher_row())
        return pd.DataFrame(pitchers)

    # ============================
    # SAVE / LOAD CUMULATIVE STATS
    # ============================

    def save(self, filename="ct_barons_stats.csv"):
        hitters = self.hitter_report()
        pitchers = self.pitcher_report()

        with open(filename, "w") as f:
            f.write("=== HITTERS ===\n")
            hitters.to_csv(f, index=False)
            f.write("\n=== PITCHERS ===\n")
            pitchers.to_csv(f, index=False)

        print("\nStats saved successfully.")

    def load(self, filename="ct_barons_stats.csv"):
        if not os.path.exists(filename):
            print("No save file found. Starting fresh.")
            return

        with open(filename, "r") as f:
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

        # Load hitters
        if hitter_lines:
            df_hitters = pd.read_csv(StringIO("\n".join(hitter_lines)))
            for _, row in df_hitters.iterrows():
                name = row["Name"]
                if name in self.players:
                    p = self.players[name]
                    p.AB = row["AB"]
                    p.H = row["H"]
                    p._2B = row["2B"]
                    p._3B = row["3B"]
                    p.HR = row["HR"]
                    p.BB = row["BB"]
                    p.K = row["K"]
                    p.HBP = row["HBP"]
                    p.SF = row["SF"]
                    p.SB = row["SB"]

        # Load pitchers
        if pitcher_lines:
            df_pitchers = pd.read_csv(StringIO("\n".join(pitcher_lines)))
            for _, row in df_pitchers.iterrows():
                name = row["Name"]
                if name in self.players:
                    p = self.players[name]
                    p.IP = row["IP"]
                    p.ER = row["ER"]
                    p.SO = row["SO"]
                    p.BB_p = row["BB"]
                    p.HR_p = row["HR"]

        print("Stats loaded successfully.")

    # ============================
    # TEAM TOTALS (FROM LOGS)
    # ============================

    def print_team_totals(self, log_manager):
        print("\n===== TEAM TOTALS (OVERALL) =====")
        self._print_team_totals_section(log_manager, league_filter=None)

        print("\n===== TEAM TOTALS (LEAGUE GAMES ONLY) =====")
        self._print_team_totals_section(log_manager, league_filter=True)

        print("\n===== TEAM TOTALS (NON-LEAGUE GAMES ONLY) =====")
        self._print_team_totals_section(log_manager, league_filter=False)

    def _print_team_totals_section(self, log_manager, league_filter):
        hit_totals = log_manager.team_hitting_totals(league_filter)
        pit_totals = log_manager.team_pitching_totals(league_filter)

        if hit_totals is None and pit_totals is None:
            print("No data for this section yet.")
            return

        if hit_totals is not None:
            print("\n-- HITTING --")
            print(f"AB: {hit_totals['AB']}, H: {hit_totals['H']}, 2B: {hit_totals['2B']}, 3B: {hit_totals['3B']}, HR: {hit_totals['HR']}")
            print(f"BB: {hit_totals['BB']}, K: {hit_totals['K']}, HBP: {hit_totals['HBP']}, SF: {hit_totals['SF']}, SB: {hit_totals['SB']}")
            print(f"AVG: {hit_totals['AVG']:.3f}, OBP: {hit_totals['OBP']:.3f}, SLG: {hit_totals['SLG']:.3f}, OPS: {hit_totals['OPS']:.3f}")
            print(f"wOBA: {hit_totals['wOBA']:.3f}, K%: {hit_totals['K%']*100:.1f}%, BB%: {hit_totals['BB%']*100:.1f}%")

        if pit_totals is not None:
            print("\n-- PITCHING --")
            print(f"IP: {pit_totals['IP']:.1f}, ER: {pit_totals['ER']}, SO: {pit_totals['SO']}, BB: {pit_totals['BB']}, HR: {pit_totals['HR']}")
            print(f"ERA: {pit_totals['ERA']:.3f}, FIP: {pit_totals['FIP']:.3f}")


# ============================
# 4. INPUT FUNCTIONS
# ============================

def input_game_context():
    date = input("Game date (YYYY-MM-DD): ")
    opponent = input("Opponent: ")
    lg = input("League game? (Y/N): ").strip().upper()
    league_game = (lg == "Y")
    return date, opponent, league_game

def input_hitting_stats(player, log_manager):
    print(f"\nEntering hitting stats for {player.name}")
    date, opponent, league_game = input_game_context()

    AB = int(input("AB: "))
    H = int(input("Hits: "))
    _2B = int(input("Doubles: "))
    _3B = int(input("Triples: "))
    HR = int(input("Home Runs: "))
    BB = int(input("Walks: "))
    K = int(input("Strikeouts: "))
    HBP = int(input("HBP: "))
    SF = int(input("Sac Flies: "))
    SB = int(input("Stolen Bases: "))

    # Update cumulative
    player.AB += AB
    player.H += H
    player._2B += _2B
    player._3B += _3B
    player.HR += HR
    player.BB += BB
    player.K += K
    player.HBP += HBP
    player.SF += SF
    player.SB += SB

    # Log game
    stats = {
        "AB": AB,
        "H": H,
        "2B": _2B,
        "3B": _3B,
        "HR": HR,
        "BB": BB,
        "K": K,
        "HBP": HBP,
        "SF": SF,
        "SB": SB
    }
    log_manager.log_hitting(date, opponent, league_game, player.name, stats)

def input_pitching_stats(player, log_manager):
    print(f"\nEntering pitching stats for {player.name}")
    date, opponent, league_game = input_game_context()

    IP = float(input("Innings Pitched (e.g., 5.2): "))
    ER = int(input("Earned Runs: "))
    SO = int(input("Strikeouts: "))
    BB_p = int(input("Walks: "))
    HR_p = int(input("Home Runs Allowed: "))

    # Update cumulative
    player.IP += IP
    player.ER += ER
    player.SO += SO
    player.BB_p += BB_p
    player.HR_p += HR_p

    # Log game
    stats = {
        "IP": IP,
        "ER": ER,
        "SO": SO,
        "BB_p": BB_p,
        "HR_p": HR_p
    }
    log_manager.log_pitching(date, opponent, league_game, player.name, stats)


# ============================
# 5. MENU LOOP
# ============================

def menu(team, log_manager):
    while True:
        print("\n===== MENU =====")
        print("1. Enter hitting stats")
        print("2. Enter pitching stats")
        print("3. Show hitter report (cumulative)")
        print("4. Show pitcher report (cumulative)")
        print("5. Show team totals (overall / league / non-league)")
        print("6. Save stats")
        print("7. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Player name: ")
            player = team.get_player(name)
            if player:
                input_hitting_stats(player, log_manager)
            else:
                print("Player not found.")

        elif choice == "2":
            name = input("Player name: ")
            player = team.get_player(name)
            if player:
                input_pitching_stats(player, log_manager)
            else:
                print("Player not found.")

        elif choice == "3":
            df = team.hitter_report()
            print("\n===== HITTER REPORT (CUMULATIVE) =====")
            if df.empty:
                print("No hitter data yet.")
            else:
                print(df.to_string(index=False))

        elif choice == "4":
            df = team.pitcher_report()
            print("\n===== PITCHER REPORT (CUMULATIVE) =====")
            if df.empty:
                print("No pitcher data yet.")
            else:
                print(df.to_string(index=False))

        elif choice == "5":
            team.print_team_totals(log_manager)

        elif choice == "6":
            team.save()

        elif choice == "7":
            print("Exiting program.")
            break

        else:
            print("Invalid choice.")


# ============================
# 6. MAIN — CT BARONS ROSTER
# ============================

if __name__ == "__main__":
    team = Team("CT Barons")

    # Infielders
    team.add_player(Player("Oliver Merced", "1B"))
    team.add_player(Player("Antonio Galiza", "1B"))
    team.add_player(Player("Charlie Ellis", "1B"))
    team.add_player(Player("Liam DaSilva", "1B"))
    team.add_player(Player("Henry Silva", "UTIL"))
    team.add_player(Player("Brett Davino", "UTIL"))
    team.add_player(Player("Mason Kuckinski", "UTIL"))
    team.add_player(Player("Nick Dorso", "UTIL"))
    team.add_player(Player("Mo Hood", "UTIL"))

    # Catchers
    team.add_player(Player("Joel Strand", "C"))
    team.add_player(Player("Brandon Skerritt", "C"))
    team.add_player(Player("Antonio Galiza", "C"))
    team.add_player(Player("Liam DaSilva", "C"))

    # Outfielders
    team.add_player(Player("Jack Farnen", "OF"))
    team.add_player(Player("Adien O'Laughlin", "OF"))
    team.add_player(Player("Nick Carlucci", "OF"))
    team.add_player(Player("Mike Fischetti", "OF"))
    team.add_player(Player("Charlie Ellis", "OF"))
    team.add_player(Player("Staller Ball", "OF"))

    # Pitchers
    team.add_player(Player("Tristan Pearl", "P"))
    team.add_player(Player("Nevin Belanger", "P"))
    team.add_player(Player("Tommy Burgers", "P"))
    team.add_player(Player("Niko Christon", "P"))
    team.add_player(Player("Colin D'onofrio", "P"))
    team.add_player(Player("Jack Jenson", "P"))
    team.add_player(Player("Merritt Hole", "P"))
    team.add_player(Player("Nick Hios", "P"))
    team.add_player(Player("James Aselta", "P"))
    team.add_player(Player("Nick Petta", "P"))
    team.add_player(Player("Christan Barboto", "P"))
    team.add_player(Player("Adam Rosenfield", "P"))
    team.add_player(Player("Branden Gaska", "P"))
    team.add_player(Player("Tyler Easterbrook", "P"))

    # Load saved cumulative stats if available
    team.load()

    # Game log manager (master + per-game logs)
    log_manager = GameLogManager(master_log="game_logs.csv", game_dir="logs")

    # Start menu
    menu(team, log_manager)


