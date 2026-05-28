#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import joblib

# ============================
# CONFIG
# ============================

csv_path = Path("/Users/chrisjones/Desktop/20260410-FordhamUniversity-1_unverified.csv")

pitch_colors = {
    "FB": "#1f77b4",
    "SI": "#17becf",
    "FC": "#ff7f0e",
    "SL": "#d62728",
    "CU": "#9467bd",
    "CH": "#2ca02c",
    "SW": "#8c564b"
}

HEADER_MAROON = "#A00000"

# ============================
# LOAD CSV
# ============================

df = pd.read_csv(csv_path, encoding="latin1", sep=None, engine="python")

fordham_team = df["HomeTeam"].iloc[0]
df = df[df["PitcherTeam"] == fordham_team].copy()
df["Pitcher"] = df["Pitcher"].astype(str).str.strip()

# ============================
# SAFE COLUMN RENAMING
# ============================

rename_map = {
    "RelSpeed": "Velo",
    "InducedVertBreak": "IVB",
    "HorzBreak": "HB",
    "SpinRate": "Spin",
    "RelHeight": "RelH",
    "RelSide": "RelS",
    "Extension": "Ext",
    "VertApprAngle": "VAA",
    "HorzApprAngle": "HAA",
    "ZoneSpeed": "ZONE%",
}
df = df.rename(columns=rename_map)

# ============================
# LOAD MODELS
# ============================

stuff_model = joblib.load("/Users/chrisjones/Desktop/models/stuff_model.pkl")
stuff_scaler = joblib.load("/Users/chrisjones/Desktop/models/stuff_scaler.pkl")

loc_model = joblib.load("/Users/chrisjones/Desktop/models/location_model.pkl")
loc_scaler = joblib.load("/Users/chrisjones/Desktop/models/location_scaler.pkl")

pitch_model = joblib.load("/Users/chrisjones/Desktop/models/pitching_model.pkl")
pitch_scaler = joblib.load("/Users/chrisjones/Desktop/models/pitching_scaler.pkl")

# ============================
# PITCH TYPE NORMALIZATION
# ============================

pitch_map = {
    "Fastball": "FB",
    "FourSeamFastBall": "FB",
    "4-Seam": "FB",
    "FF": "FB",
    "Sinker": "SI",
    "Cutter": "FC",
    "Slider": "SL",
    "Sweeper": "SW",
    "Curveball": "CU",
    "ChangeUp": "CH",
    "Changeup": "CH"
}

df["pitch_abbr"] = df["TaggedPitchType"].map(pitch_map)
df["pitch_abbr"] = df["pitch_abbr"].fillna(
    df["TaggedPitchType"].astype(str).str[:2].str.upper()
)

# ============================
# LOOP THROUGH PITCHERS
# ============================

pitchers = df["Pitcher"].unique()

for pitcher in pitchers:
    pdf = df[df["Pitcher"] == pitcher].copy()

    # ============================
    # GAME LINE
    # ============================

    total_pitches = len(pdf)
    strike_calls = ["StrikeCalled", "StrikeSwinging", "FoulBall", "FoulBallNotFieldable"]

    strikes = pdf["PitchCall"].isin(strike_calls).sum()
    strike_pct = round(strikes / total_pitches * 100, 1) if total_pitches else 0

    whiffs = pdf["PitchCall"].eq("StrikeSwinging").sum()
    walks = pdf["KorBB"].eq("Walk").sum()
    strikeouts = pdf["KorBB"].eq("Strikeout").sum()
    hbp = pdf["PitchCall"].eq("HitByPitch").sum()

    hits = pdf["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"]).sum()
    hr = pdf["PlayResult"].eq("HomeRun").sum()
    runs = pdf["RunsScored"].sum()
    er = runs

    outs_on_play = pdf["OutsOnPlay"].sum()
    total_outs = outs_on_play + strikeouts
    ip = total_outs // 3 + (total_outs % 3) / 10 if total_outs else 0.0

    # ============================
    # FASTBALL BASELINE
    # ============================

    fb = pdf[pdf["pitch_abbr"] == "FB"]
    fb_velo = fb["Velo"].mean()
    fb_ivb = fb["IVB"].mean()
    fb_hb = fb["HB"].mean()
    fb_spin = fb["Spin"].mean()

    pdf["velo_diff"] = pdf["Velo"] - fb_velo
    pdf["ivb_diff"] = pdf["IVB"] - fb_ivb
    pdf["hb_diff"] = pdf["HB"] - fb_hb
    pdf["spin_diff"] = pdf["Spin"] - fb_spin

    # ============================
    # STUFF+
    # ============================

    stuff_features = [
        "Velo", "IVB", "HB", "Spin",
        "RelH", "RelS", "Ext",
        "VAA", "HAA",
        "velo_diff", "ivb_diff", "hb_diff", "spin_diff"
    ]

    Xs = pdf[stuff_features].fillna(0)
    Xs_scaled = stuff_scaler.transform(Xs)
    pdf["stuff_prob"] = stuff_model.predict_proba(Xs_scaled)[:, 1]

    mu = pdf["stuff_prob"].mean()
    sigma = pdf["stuff_prob"].std() if pdf["stuff_prob"].std() else 1
    pdf["Stuff+"] = 100 + 20 * ((pdf["stuff_prob"] - mu) / sigma)

    # ============================
    # LOC+
    # ============================

    loc_features = ["ZONE%", "VAA", "HAA"]
    Xl = pdf[loc_features].fillna(0)
    Xl_scaled = loc_scaler.transform(Xl)
    pdf["loc_prob"] = loc_model.predict_proba(Xl_scaled)[:, 1]

    mu_l = pdf["loc_prob"].mean()
    sigma_l = pdf["loc_prob"].std() if pdf["loc_prob"].std() else 1
    pdf["Loc+"] = 100 + 20 * ((pdf["loc_prob"] - mu_l) / sigma_l)

    # model expects Location+
    pdf["Location+"] = pdf["Loc+"]

    # ============================
    # PITCH+
    # ============================

    pdf["pitch_code"] = pdf["pitch_abbr"].astype("category").cat.codes

    pitch_features = ["Stuff+", "Location+", "pitch_code", "ZONE%"]
    Xp = pdf[pitch_features].fillna(0)
    Xp_scaled = pitch_scaler.transform(Xp)
    pdf["pitch_prob"] = pitch_model.predict_proba(Xp_scaled)[:, 1]

    pdf["pitch_residual"] = pdf["pitch_prob"] - pdf["pitch_prob"].mean()
    mu_r = pdf["pitch_residual"].mean()
    sigma_r = pdf["pitch_residual"].std() if pdf["pitch_residual"].std() else 1
    pdf["Pitch+"] = 100 + 20 * ((pdf["pitch_residual"] - mu_r) / sigma_r)

    # ============================
    # COMBO+
    # ============================

    pdf["Combo+"] = (
        0.45 * pdf["Stuff+"] +
        0.25 * pdf["Loc+"] +
        0.30 * pdf["Pitch+"]
    )

    # ============================
    # FLAGS
    # ============================

    pdf["is_csw"] = pdf["PitchCall"].isin(["StrikeCalled", "StrikeSwinging"])
    pdf["is_whiff"] = pdf["PitchCall"].eq("StrikeSwinging")
    pdf["is_swing"] = pdf["PitchCall"].isin([
        "StrikeSwinging", "FoulBall", "FoulBallNotFieldable",
        "InPlay", "InPlayNoOut", "InPlayOut"
    ])
    pdf["is_strike"] = pdf["PitchCall"].isin(strike_calls)

    pdf["in_zone"] = (
        pdf["PlateLocSide"].between(-0.83, 0.83) &
        pdf["PlateLocHeight"].between(1.5, 3.5)
    )

    # ============================
    # AGGREGATE
    # ============================

    agg = pdf.groupby("pitch_abbr").agg(
        N=("PitchCall", "count"),
        Velo=("Velo", "mean"),
        IVB=("IVB", "mean"),
        HB=("HB", "mean"),
        Spin=("Spin", "mean"),
        RelH=("RelH", "mean"),
        RelS=("RelS", "mean"),
        Ext=("Ext", "mean"),
        VAA=("VAA", "mean"),
        HAA=("HAA", "mean"),
        Stuff_plus=("Stuff+", "mean"),
        Loc_plus=("Loc+", "mean"),
        Pitch_plus=("Pitch+", "mean"),
        Combo_plus=("Combo+", "mean"),
        CSW=("is_csw", "sum"),
        Whiffs=("is_whiff", "sum"),
        Swings=("is_swing", "sum"),
        Strikes=("is_strike", "sum"),
        InZone=("in_zone", "sum")
    ).reset_index()

    total_N = agg["N"].sum()
    agg["Usage%"] = (agg["N"] / total_N * 100).round(1)

    agg["CSW%"] = (agg["CSW"] / agg["N"] * 100).round(1)
    agg["Whiff%"] = np.where(
        agg["Swings"] > 0,
        (agg["Whiffs"] / agg["Swings"] * 100).round(1),
        0.0
    )
    agg["Strike%"] = (agg["Strikes"] / agg["N"] * 100).round(1)
    agg["Zone%"] = (agg["InZone"] / agg["N"] * 100).round(1)

    agg = agg.rename(columns={
        "Stuff_plus": "Stuff+",
        "Loc_plus": "Loc+",
        "Pitch_plus": "Pitch+",
        "Combo_plus": "Combo+"
    })

    # ============================
    # FIGURE LAYOUT
    # ============================

    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor("#1e1e1e")

    title = f"{pitcher} – Fordham vs VCU"
    summary = (
        f"IP: {ip:.1f}  H: {hits}  R: {runs}  ER: {er}  "
        f"BB: {walks}  K: {strikeouts}  HR: {hr}  HBP: {hbp}  "
        f"Whiffs: {whiffs}  Strike%: {strike_pct}%"
    )

    fig.suptitle(title, fontsize=26, fontweight="bold", color=HEADER_MAROON, y=0.97)
    plt.text(0.5, 0.93, summary, ha="center", va="center", color="white", fontsize=14)

    # ============================
    # MOVEMENT (Column 1)
    # ============================

    ax1 = plt.subplot2grid((5, 4), (0, 0), rowspan=2)
    ax1.set_facecolor("#1e1e1e")
    ax1.set_xlim(-25, 25)
    ax1.set_ylim(-25, 25)

    throws = pdf["PitcherThrows"].iloc[0] if "PitcherThrows" in pdf.columns else "Right"
    if throws.upper().startswith("R"):
        arm_side = (0.1, 0.3, 0.6, 0.10)
        glove_side = (0.6, 0.1, 0.1, 0.10)
    else:
        arm_side = (0.6, 0.1, 0.1, 0.10)
        glove_side = (0.1, 0.3, 0.6, 0.10)

    ax1.axvspan(0, 25, facecolor=arm_side)
    ax1.axvspan(-25, 0, facecolor=glove_side)

    ax1.axhline(0, color="white", linestyle=":", linewidth=1.2)
    ax1.axvline(0, color="white", linestyle=":", linewidth=1.2)

    for _, row in agg.iterrows():
        c = pitch_colors.get(row["pitch_abbr"], "white")
        ax1.scatter(row["HB"], row["IVB"], s=row["N"] * 1.5, color=c, edgecolor="white")
        ax1.text(row["HB"], row["IVB"], row["pitch_abbr"], color="white", fontsize=10)

    ax1.set_title("Movement", color="white")

    # ============================
    # MLB-STYLE LOCATION PLOTS
    # ============================

    def draw_mlb_zone(ax):
        ax.set_facecolor("#1e1e1e")
        ax.set_xlim(-2.5, 2.5)
        ax.set_ylim(0, 5)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(False)

        ax.axhline(0, color="white", linestyle=":", linewidth=1)
        ax.axvline(0, color="white", linestyle=":", linewidth=1)

        zone_x = [-0.83, 0.83, 0.83, -0.83, -0.83]
        zone_y = [1.5, 1.5, 3.5, 3.5, 1.5]

        ax.plot(zone_x, zone_y, color="white", linewidth=2.5)
        ax.fill_between([-0.83, 0.83], 1.5, 3.5, color="white", alpha=0.06)

    # LHH (Column 2) — bigger
    axL = plt.subplot2grid((5, 4), (0, 1), rowspan=2)
    draw_mlb_zone(axL)

    LHH = pdf[pdf["BatterSide"] == "Left"]
    for _, row in LHH.iterrows():
        c = pitch_colors.get(row["pitch_abbr"], "white")
        axL.scatter(
            row["PlateLocSide"],
            row["PlateLocHeight"],
            s=85,
            color=c,
            edgecolor="white",
            linewidth=0.7
        )

    axL.set_title("LHH", color="white")

    # RHH (Column 3) — bigger
    axR = plt.subplot2grid((5, 4), (0, 2), rowspan=2)
    draw_mlb_zone(axR)

    RHH = pdf[pdf["BatterSide"] == "Right"]
    for _, row in RHH.iterrows():
        c = pitch_colors.get(row["pitch_abbr"], "white")
        axR.scatter(
            row["PlateLocSide"],
            row["PlateLocHeight"],
            s=85,
            color=c,
            edgecolor="white",
            linewidth=0.7
        )

    axR.set_title("RHH", color="white")

    # ============================
    # RELEASE (Column 4)
    # ============================

    axRel = plt.subplot2grid((5, 4), (0, 3), rowspan=2)
    axRel.set_facecolor("#1e1e1e")
    axRel.set_xlim(-4, 4)
    axRel.set_ylim(3, 7)
    axRel.set_aspect("equal", adjustable="box")

    for _, row in pdf.iterrows():
        c = pitch_colors.get(row["pitch_abbr"], "white")
        axRel.scatter(row["RelS"], row["RelH"], s=25, color=c, edgecolor="white")

    axRel.set_title("Release", color="white")

    # ============================
    # TABLE (Full Width)
    # ============================

    axT = plt.subplot2grid((5, 4), (2, 0), colspan=4, rowspan=2)
    axT.axis("off")

    table_df = agg[[
        "pitch_abbr", "N", "Usage%", "Velo", "IVB", "HB",
        "Spin", "Stuff+", "Loc+", "Pitch+", "Combo+",
        "CSW%", "Whiff%", "Strike%", "Zone%"
    ]].round(2)

    tbl = axT.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        loc="center",
        cellLoc="center",
        bbox=[0, 0, 1, 1]
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)

    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(HEADER_MAROON)
            cell.set_text_props(color="white", weight="bold")
        else:
            pitch = table_df.iloc[r - 1]["pitch_abbr"]
            bg = pitch_colors.get(pitch, "#1e1e1e")
            cell.set_facecolor(bg)
            cell.set_text_props(color="white")

    # ============================
    # FOOTER
    # ============================

    axFooter = plt.subplot2grid((5, 4), (4, 0), colspan=4)
    axFooter.axis("off")

    axFooter.text(
        0.5, 0.5, summary,
        ha="center", va="center",
        fontsize=14, color="white", weight="bold"
    )

    # ============================
    # SAVE
    # ============================

    out = csv_path.parent / f"{pitcher.replace(',','')}_Summary.png"
    plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
    plt.close()

    print(f"Saved: {out}")
