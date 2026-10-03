#!/usr/bin/env python3
"""Write the latest 4 and 5 star Google reviews into Website/index.html.

Runs nightly from .github/workflows/reviews.yml. Reads the newest 4 and 5 star
reviews from the review-card Worker, which remembers every review the Make
scenario posts to Facebook (review-card/README.md). If Google Business Profile
API secrets are set, reads Google directly instead; that API needs Google's
approval, which the restaurant does not have yet. Keeps the newest reviews
rated 4 or 5 stars that have written text, and replaces the block between the
reviews:start and reviews:end markers in index.html.

Standard library only. Exits non-zero on any API failure and leaves the page
untouched, so a broken token fails the workflow instead of emptying the section.

Environment:
  REVIEWS_URL    the Worker's /reviews.json (default below)
  GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN   OAuth (connect_google.py sets these)
  GBP_LOCATION   accounts/<id>/locations/<id>  (optional; discovered and printed if unset)

Local check without the API:
  python3 scripts/reviews/fetch_reviews.py --fixture reviews.json --out /tmp/index.html
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "Website" / "index.html"
START = "<!-- reviews:start -->"
END = "<!-- reviews:end -->"

SHOW = 5                 # two columns; the first quote spans both (style.css .quote:first-child)
MAX_CHARS = 180          # longer reviews are cut at a word boundary
STARS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
MAPS_FALLBACK = "https://www.google.com/maps/search/?api=1&query=Hot+Pot+World+Rotary+Federal+Way+WA"
REVIEWS_URL = "https://hotpotworld-review-card.anh-add.workers.dev/reviews.json"


# ---------------------------------------------------------------- Google API

def api(url, token=None, data=None):
    # Cloudflare refuses Python's default User-Agent (error 1010), so name ourselves.
    headers = {"User-Agent": "hotpotworld-reviews/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        sys.exit(f"HTTP {e.code} on {url.split('?')[0]}\n{detail}")


def access_token():
    missing = [k for k in ("GBP_CLIENT_ID", "GBP_CLIENT_SECRET", "GBP_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        sys.exit("Missing " + ", ".join(missing) + ". Run scripts/reviews/connect_google.py first.")
    return api("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["GBP_CLIENT_ID"],
        "client_secret": os.environ["GBP_CLIENT_SECRET"],
        "refresh_token": os.environ["GBP_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })["access_token"]


def find_location(token):
    """accounts/<a>/locations/<l> for the one profile this login manages."""
    accounts = api("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", token).get("accounts", [])
    found = []
    for acct in accounts:
        url = (f"https://mybusinessbusinessinformation.googleapis.com/v1/{acct['name']}/locations"
               "?readMask=name,title&pageSize=100")
        for loc in api(url, token).get("locations", []):
            found.append((f"{acct['name']}/{loc['name']}", loc.get("title", "")))
    if not found:
        sys.exit("This Google login manages no Business Profile locations.")
    for path, title in found:
        print(f"location: {path}  ({title})")
    hot_pot = [p for p, t in found if "hot" in t.lower()]
    if len(hot_pot) != 1:
        sys.exit("Could not pick one Hot Pot World location; set GBP_LOCATION to one of the above.")
    return hot_pot[0]


def fetch(token, location):
    loc_id = location.split("/locations/")[1]
    meta = api(f"https://mybusinessbusinessinformation.googleapis.com/v1/locations/{loc_id}"
               "?readMask=metadata", token).get("metadata", {})
    reviews, page = [], None
    for _ in range(4):  # 4 pages x 50 is far more than we need to find 5 good ones
        q = {"pageSize": 50, "orderBy": "updateTime desc"}
        if page:
            q["pageToken"] = page
        data = api(f"https://mybusiness.googleapis.com/v4/{location}/reviews?" + urllib.parse.urlencode(q), token)
        reviews += data.get("reviews", [])
        summary = {"averageRating": data.get("averageRating"), "totalReviewCount": data.get("totalReviewCount")}
        page = data.get("nextPageToken")
        if not page or len(pick(reviews)) >= SHOW:
            break
    return {"reviews": reviews, **summary, "mapsUri": meta.get("mapsUri")}


# ---------------------------------------------------------------- selection

def english(comment):
    """Google appends machine translations. Keep the English half."""
    c = comment.strip()
    if "(Translated by Google)" in c:
        before, after = c.split("(Translated by Google)", 1)
        if "(Original)" in after:          # "(Translated by Google) EN\n\n(Original)\nXX"
            return after.split("(Original)", 1)[0].strip()
        return after.strip() or before.strip()  # "XX\n\n(Translated by Google) EN"
    return c


def trim(text):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS].rsplit(" ", 1)[0].rstrip(",;:.!?-")
    return cut + "…"


def pick(reviews):
    good = [r for r in reviews
            if STARS.get(r.get("starRating")) in (4, 5) and english(r.get("comment", ""))]
    good.sort(key=lambda r: r.get("createTime", ""), reverse=True)
    return good[:SHOW]


def short_name(name):
    """First name and last initial, which is how the page credits people."""
    parts = (name or "").split()
    if not parts:
        return "A Google reviewer"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


# ---------------------------------------------------------------- render

def render(data):
    picked = pick(data.get("reviews", []))
    if not picked:
        return None
    maps = data.get("mapsUri") or MAPS_FALLBACK
    out = []
    for r in picked:
        n = STARS[r["starRating"]]
        when = datetime.fromisoformat(r["createTime"].replace("Z", "+00:00")).strftime("%B %Y")
        out.append(
            '        <blockquote class="quote">\n'
            f"          <p>{html.escape(trim(english(r['comment'])))}</p>\n"
            '          <footer class="quote__by">'
            f'<span class="quote__stars" aria-label="{n} out of 5 stars">{"★" * n}</span> '
            f"{html.escape(short_name(r.get('reviewer', {}).get('displayName')))}, {when}</footer>\n"
            "        </blockquote>"
        )
    avg, total = data.get("averageRating"), data.get("totalReviewCount")
    summary, link = ((f"{avg:.1f} stars from {total:,} Google reviews.", "See them on Google")
                     if avg and total else ("", "Read every review on Google"))
    return (
        f"{START}\n"
        '      <div class="quotes" data-reveal>\n' + "\n".join(out) + "\n      </div>\n"
        f'      <p class="quotes__more" data-reveal>{summary + " " if summary else ""}'
        f'<a href="{html.escape(maps)}" target="_blank" rel="noopener">{link}</a></p>\n'
        f"      {END}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="render from a saved API response instead of calling Google")
    ap.add_argument("--out", default=str(INDEX), help="where to write the page (default: Website/index.html)")
    args = ap.parse_args()

    if args.fixture:
        data = json.loads(Path(args.fixture).read_text())
    elif not os.environ.get("GBP_REFRESH_TOKEN"):
        data = api(os.environ.get("REVIEWS_URL") or REVIEWS_URL)
    else:
        token = access_token()
        data = fetch(token, os.environ.get("GBP_LOCATION") or find_location(token))

    block = render(data)
    if block is None:
        print("No 4 or 5 star reviews with text came back; leaving the page as it is.")
        return
    page = INDEX.read_text()
    if START not in page or END not in page:
        sys.exit("index.html is missing the reviews:start / reviews:end markers.")
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, page, count=1, flags=re.S)
    Path(args.out).write_text(new)
    print("Reviews block " + ("changed." if new != page else "unchanged."))


if __name__ == "__main__":
    main()
