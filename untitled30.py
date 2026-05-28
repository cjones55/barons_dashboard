#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ftplib import FTP_TLS
from pathlib import Path
from dotenv import load_dotenv
import os

# ============================
# LOAD CREDENTIALS FROM .env
# ============================

load_dotenv()  # loads TM_FTP_USER and TM_FTP_PASS

def connect_trackman():
    """
    Connect to TrackMan FTPS using credentials from .env
    """
    user = os.getenv("Fordham")
    pwd  = os.getenv("y6kRFtz?5w")

    if not user or not pwd:
        raise RuntimeError("TM_FTP_USER or TM_FTP_PASS not found in .env file.")

    ftp = FTP_TLS()
    ftp.connect("ftp.trackmanbaseball.com", 21)
    ftp.auth()      # upgrade to TLS
    ftp.prot_p()    # secure data channel
    ftp.login(user, pwd)

    print(f"Connected to TrackMan FTP as {user}")
    return ftp


def download_years(ftp, years, base_dir):
    """
    Download all CSV files for the given years into base_dir/YYYY/MM/DD/
    """
    base_dir.mkdir(exist_ok=True)

    for year in years:
        print(f"\n=== YEAR {year} ===")
        for month in range(1, 13):
            for day in range(1, 32):

                remote_path = f"/v3/{year}/{month:02d}/{day:02d}/CSV"

                try:
                    ftp.cwd(remote_path)
                except Exception:
                    continue  # skip missing days

                local_day_dir = base_dir / year / f"{month:02d}" / f"{day:02d}"
                local_day_dir.mkdir(parents=True, exist_ok=True)

                try:
                    files = ftp.nlst()
                except Exception:
                    continue

                for filename in files:
                    if not filename.lower().endswith(".csv"):
                        continue

                    local_path = local_day_dir / filename

                    # Skip if already downloaded
                    if local_path.exists():
                        print(f"Already exists, skipping: {local_path}")
                        continue

                    with open(local_path, "wb") as f:
                        ftp.retrbinary(f"RETR {filename}", f.write)

                    print(f"Downloaded: {local_path}")


def main():
    # Where to store all raw TrackMan CSVs
    base_dir = Path.home() / "Desktop" / "fordham_raw_data"

    # Years to pull
    years = ["2025", "2026"]

    ftp = connect_trackman()

    try:
        download_years(ftp, years, base_dir)
    finally:
        ftp.quit()
        print("\nDisconnected from TrackMan FTP.")

    print("\nAll files downloaded successfully.")
    print(f"Saved under: {base_dir}")


if __name__ == "__main__":
    main()
