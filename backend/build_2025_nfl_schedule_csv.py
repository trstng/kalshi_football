# save as build_2025_nfl_schedule_csv.py
# pip install pdfplumber

import re, csv, io, datetime as dt
from zoneinfo import ZoneInfo
import pdfplumber

PDF_PATH = "artifacts/2025-nfl-schedule-by-week (1).pdf"   # put the PDF in the same folder
OUT_PATH = "artifacts/nfl_2025_schedule_corrected.csv"
SEASON = 2025
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

TEAM_ABBR = {
    "Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL","Buffalo Bills":"BUF",
    "Carolina Panthers":"CAR","Chicago Bears":"CHI","Cincinnati Bengals":"CIN","Cleveland Browns":"CLE",
    "Dallas Cowboys":"DAL","Denver Broncos":"DEN","Detroit Lions":"DET","Green Bay Packers":"GB",
    "Houston Texans":"HOU","Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX","Kansas City Chiefs":"KC",
    "Las Vegas Raiders":"LV","Los Angeles Chargers":"LAC","Los Angeles Rams":"LAR","Miami Dolphins":"MIA",
    "Minnesota Vikings":"MIN","New England Patriots":"NE","New Orleans Saints":"NO","New York Giants":"NYG",
    "New York Jets":"NYJ","Philadelphia Eagles":"PHI","Pittsburgh Steelers":"PIT","San Francisco 49ers":"SF",
    "Seattle Seahawks":"SEA","Tampa Bay Buccaneers":"TB","Tennessee Titans":"TEN","Washington Commanders":"WAS"
}

WEEK_RE = re.compile(r"^WEEK\s+(\d{1,2})$")
DATE_HDR_RE = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]+)\s+(\d{1,2}),\s+(20\d{2})$")
GAME_RE = re.compile(
    r"^(?P<away>.+?)\s+(?P<sep>at|vs)\s+(?P<home>.+?)"
    r"(?:\s+\((?P<meta>[^)]*)\))?\s+"
    r"(?P<local>\d{1,2}:\d{2}[ap]|TBD)\s+\([A-Z+]{2,4}\)\s+"
    r"(?P<et>\d{1,2}:\d{2}[ap]|TBD)\s+(?P<network>[A-Za-z0-9/+&. ]+)$"
)
TBD_RE = re.compile(
    r"^(?P<away>.+?)\s+(?P<sep>at|vs)\s+(?P<home>.+?)"
    r"(?:\s+\((?P<meta>[^)]*)\))?\s+TBD\s+TBD\s+(?P<network>[A-Za-z0-9/+&. ]+)$"
)

def parse_et_time(token: str, date: dt.date):
    t = (token or "").strip().lower()
    if t in ("tbd","tba",""): return None
    m = re.match(r"^(\d{1,2}):(\d{2})([ap])$", t)
    if not m: return None
    hh, mm, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == "p" and hh != 12: hh += 12
    if ap == "a" and hh == 12: hh = 0
    return dt.datetime(date.year, date.month, date.day, hh, mm, tzinfo=ET)

def site_type(sep: str): return "neutral" if sep.lower()=="vs" else "home_away"
def abbr(name: str): return TEAM_ABBR.get(name.strip(), name.strip())

rows = []
current_week = None
current_date = None

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        # pdfplumber preserves layout reading order well for this doc
        text = page.extract_text() or ""
        for raw in text.splitlines():
            line = (raw or "").strip()
            if not line:
                continue

            mw = WEEK_RE.match(line)
            if mw:
                current_week = int(mw.group(1))
                current_date = None
                continue

            md = DATE_HDR_RE.match(line)
            if md:
                month, day, year = md.group(2), int(md.group(3)), int(md.group(4))
                current_date = dt.datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
                continue

            if line.startswith("2025 NFL Regular-Season Schedule") or \
               "Games grouped by start times" in line or \
               line == "GAME LOCAL ET TV" or \
               line.startswith("BYES:") or \
               line.startswith("Sheet1"):
                continue

            m = GAME_RE.match(line) or TBD_RE.match(line)
            if m and current_week is not None and current_date is not None:
                away = m.group("away").strip()
                home = m.group("home").strip()
                sep = m.group("sep")
                et_tok = (m.groupdict().get("et") or "TBD").strip()
                network = (m.group("network") or "").strip()

                dt_et = parse_et_time(et_tok, current_date)
                kickoff_utc = dt_et.astimezone(UTC).isoformat() if dt_et else ""

                rows.append({
                    "season": SEASON,
                    "week": current_week,
                    "game_date": current_date.isoformat(),
                    "away_team": away,
                    "home_team": home,
                    "away_abbr": abbr(away),
                    "home_abbr": abbr(home),
                    "kickoff_utc": kickoff_utc,
                    "network": network,
                    "site_type": site_type(sep),
                })

# sort & write
rows.sort(key=lambda r: (r["week"], r["game_date"], r["kickoff_utc"] or r["game_date"], r["home_abbr"]))
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["season","week","game_date","away_team","home_team","away_abbr","home_abbr","kickoff_utc","network","site_type"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {len(rows)} games to {OUT_PATH}")
