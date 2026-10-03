#!/usr/bin/env python3
"""One-time: sign in as the Google account that manages the Business Profile,
then store the credentials as GitHub secrets for the nightly reviews job.

  python3 scripts/reviews/connect_google.py [path/to/client_secret.json]

The client file is the Desktop OAuth client downloaded from Google Cloud
(defaults to the newest ~/Downloads/client_secret_*.json). Nothing secret is
printed: values go straight from this process into `gh secret set` on stdin.
The client file is moved to the Trash afterwards, since GitHub now holds it.
"""

import http.server
import json
import secrets
import shutil
import subprocess
import sys
import urllib.parse
import webbrowser
from pathlib import Path

REPO = "hotpotworldrotary/website"
SCOPE = "https://www.googleapis.com/auth/business.manage"
HERE = Path(__file__).resolve().parent


def client_file():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser()
    found = sorted(Path.home().joinpath("Downloads").glob("client_secret_*.json"),
                   key=lambda p: p.stat().st_mtime)
    if not found:
        sys.exit("No ~/Downloads/client_secret_*.json found. Pass the path to the downloaded OAuth client.")
    return found[-1]


def sign_in(client):
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] != state:
                self.send_response(400); self.end_headers(); return
            result.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<p style='font:18px system-ui'>Signed in. You can close this tab.</p>".encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client["client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
    })
    print("Opening Google sign-in in your browser. Sign in with the account that manages Hot Pot World Rotary.")
    webbrowser.open(url)
    while "code" not in result and "error" not in result:
        server.handle_request()
    if "error" in result:
        sys.exit(f"Sign-in did not finish: {result['error']}")

    body = urllib.parse.urlencode({
        "code": result["code"], "client_id": client["client_id"], "client_secret": client["client_secret"],
        "redirect_uri": redirect, "grant_type": "authorization_code",
    }).encode()
    import urllib.request
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", data=body, timeout=30) as r:
        tokens = json.load(r)
    if "refresh_token" not in tokens:
        sys.exit("Google returned no refresh token. Remove the app's access at myaccount.google.com/permissions and run this again.")
    return tokens


def set_secret(name, value):
    subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value.encode(), check=True,
                   stdout=subprocess.DEVNULL)
    print(f"  stored {name}")


def main():
    path = client_file()
    client = json.loads(path.read_text()).get("installed")
    if not client:
        sys.exit(f"{path.name} is not a Desktop app client. Create the OAuth client as type 'Desktop app'.")

    tokens = sign_in(client)
    print(f"Storing credentials in {REPO}:")
    set_secret("GBP_CLIENT_ID", client["client_id"])
    set_secret("GBP_CLIENT_SECRET", client["client_secret"])
    set_secret("GBP_REFRESH_TOKEN", tokens["refresh_token"])

    shutil.move(str(path), str(Path.home() / ".Trash" / path.name))
    print(f"  moved {path.name} to the Trash")

    # Find the location now if Google has approved API access; otherwise this waits.
    sys.path.insert(0, str(HERE))
    import fetch_reviews
    try:
        location = fetch_reviews.find_location(tokens["access_token"])
    except SystemExit as e:
        print(f"Location lookup did not work yet (expected until Google approves API access):\n  {e}")
        return
    subprocess.run(["gh", "variable", "set", "GBP_LOCATION", "-R", REPO, "--body", location], check=True)
    print(f"  stored GBP_LOCATION = {location}")
    print("Done. Run the 'Refresh Google reviews' workflow to publish the first batch.")


if __name__ == "__main__":
    main()
