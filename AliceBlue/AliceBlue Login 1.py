import csv
import hashlib
import json
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import pyotp
import requests
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURATION & FILE PATHS
# ==========================================
LOGIN_FILE = r"R:\AliceBlueLogin1.txt"
INPUTS_FILE = r"C:\API\Files\AliceBlueInputs 1.csv"
SESSION_URL = "https://a3.aliceblueonline.com/open-api/od/v1/vendor/getUserDetails"

#HEADLESS = False   # Keep False so you can see browser actions
WAIT_SECS = 20     # Timeout in seconds


# ==========================================
# COMMON UTILITY FUNCTIONS
# ==========================================

#Read CSV as Dictonary
def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            key, value = row
            data_dict[key] = value
    return data_dict


def dict_to_csv(dictionary, out_file):
    """Writes a dictionary to a key,value CSV file."""
    with open(out_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        for key, value in dictionary.items():
            writer.writerow([key, value])


def get_safe_totp(totp_secret, wait_margin=55):
    """Waits out the last seconds of the minute, then returns a fresh TOTP."""
    while True:
        sec = datetime.now().second
        if sec < wait_margin:
            break
        print(f"Current second = {sec} -> waiting for fresh TOTP window...")
        time.sleep(1)

    code = pyotp.TOTP(totp_secret).now()
    print("Generated Safe TOTP:", code)
    return code


def make_redirect_matcher(redirect_url):
    """Returns a function that is True for any URL under the RedirectURL from the inputs CSV."""
    base = urlparse(redirect_url)
    base_path = base.path or "/"

    def matches(url):
        u = urlparse(url)
        return (u.scheme == base.scheme
                and u.netloc == base.netloc
                and (u.path or "/").startswith(base_path))

    return matches


def start_redirect_capture(page, redirect_url, key="authCode="):
    """
    Call BEFORE page.goto(). Captures the first URL that is under `redirect_url`
    and contains `key`. Also serves a blank page for that URL so the browser
    does not show a 'refused to connect' error.
    """
    matches = make_redirect_matcher(redirect_url)
    captured = {"url": None}

    def check(url):
        if url and key in url and matches(url) and not captured["url"]:
            captured["url"] = url

    def on_route(route, request):
        check(request.url)
        route.fulfill(status=200, content_type="text/html", body="OK")

    page.context.route(matches, on_route)
    page.context.on("request", lambda r: check(r.url))
    page.on("framenavigated", lambda f: check(f.url))
    return captured


def wait_for_capture(page, captured, timeout=WAIT_SECS):
    """Waits (using Playwright's wait so events fire) until the URL is captured."""
    start = time.time()
    while not captured["url"]:
        if time.time() - start > timeout:
            raise TimeoutError(f"Timed out waiting for redirect URL. Last page URL: {page.url}")
        page.wait_for_timeout(200)
    return captured["url"]


def get_query_param(url, name, default=None):
    """Returns a single query parameter from a URL."""
    return parse_qs(urlparse(url).query).get(name, [default])[0]


def get_user_session(user_id, auth_code, api_secret, session_url):
    """Exchanges the auth code for a user session / access token."""
    checksum = hashlib.sha256((user_id.upper() + auth_code + api_secret).encode()).hexdigest()

    response = requests.post(
        session_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"checkSum": checksum}),
    )
    data = response.json()

    if response.status_code == 200:
        if data.get("stat") == "Ok" and data.get("userSession"):
            return data["userSession"]
        if data.get("status") == "Ok" and data.get("result"):
            result = data["result"]
            if isinstance(result, list) and result and result[0].get("accessToken"):
                return result[0]["accessToken"]

    raise Exception(f"Error getting user session: {data}")


# ==========================================
# ALICEBLUE-SPECIFIC FUNCTIONS
# ==========================================

def get_auth_code(page, inputs):
    """AliceBlue browser login. Returns (auth_code, user_id)."""
    captured = start_redirect_capture(page, inputs["RedirectURL"], key="authCode=")

    page.goto(f"https://ant.aliceblueonline.com/?appcode={inputs['AppCode']}",
              wait_until="domcontentloaded")
    page.fill("#new_login_userId", inputs["UserID"])
    page.fill("#new_login_password", inputs["Password"])
    page.click("#buttonLabel_Next")

    page.wait_for_selector("#new_login_otp", timeout=WAIT_SECS * 1000)
    page.fill("#new_login_otp", get_safe_totp(inputs["TOTPKey"]))

    url = wait_for_capture(page, captured)
    print("Captured Redirect URL:", url)

    auth_code = get_query_param(url, "authCode")
    if not auth_code:
        raise Exception(f"No authCode found in URL: {url}")
    return auth_code, get_query_param(url, "userId", inputs["UserID"])


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    try:
        inputs = read_csv_dict(INPUTS_FILE)

        if inputs["BrowserShow"].lower() == 'yes':
            HEADLESS = False
        else:
            HEADLESS = True
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS, args=["--window-size=1200,900"])
            page = browser.new_context().new_page()
            auth_code, user_id = get_auth_code(page, inputs)
            browser.close()

        token = get_user_session(user_id, auth_code, inputs["AppSecret"], SESSION_URL)
        dict_to_csv({            
            "date": datetime.now().strftime("%d"),
            "user": user_id,
            "token": token,
        }, LOGIN_FILE)
        print(f"Login successful! Response saved to {LOGIN_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")
