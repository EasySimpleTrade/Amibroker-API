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
LOGIN_FILE = r"R:\ShoonyaLogin1.txt"
INPUTS_FILE = r"C:\API\Files\ShoonyaInputs 1.csv"
TOKEN_URL = "https://api.shoonya.com/NorenWClientAPI/GenAcsTok"

#HEADLESS = False
CODE_WAIT_SECS = 60

FIELDS = "input:visible:not([type='hidden']):not([type='checkbox']):not([type='radio'])"
LOGIN_BTN = "xpath=//button[normalize-space()='LOGIN']"


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


def wait_for_capture(page, captured, timeout):
    """Waits (using Playwright's wait so events fire) until a URL is captured."""
    start = time.time()
    while not captured["url"]:
        if time.time() - start > timeout:
            raise TimeoutError(f"Timed out waiting for code. Last page URL: {page.url}")
        page.wait_for_timeout(200)
    return captured["url"]


# ==========================================
# SHOONYA-SPECIFIC FUNCTIONS
# ==========================================

def start_shoonya_capture(page):
    """
    Captures the first URL containing code= and 'shoonya'. Watches requests,
    navigations and redirect Location headers, so the code is caught even if
    the final page ("access only for API users") does not show it.
    """
    captured = {"url": None}

    def check(url):
        if url and "code=" in url and "shoonya" in url.lower() and not captured["url"]:
            captured["url"] = url

    def on_response(response):
        check(response.url)
        try:
            check(response.headers.get("location"))
        except Exception:
            pass

    page.context.on("request", lambda r: check(r.url))
    page.context.on("response", on_response)
    page.on("framenavigated", lambda f: check(f.url))
    return captured


def submit_credentials(page, inputs, otp):
    """Fills user id, password, OTP and clicks LOGIN."""
    fields = page.locator(FIELDS)
    fields.nth(0).fill(inputs["UserID"])
    fields.nth(1).fill(inputs["Password"])
    fields.nth(2).fill(otp)
    page.locator(LOGIN_BTN).click()


def get_auth_code(page, inputs):
    """Shoonya browser login. Retries once with a fresh OTP only if the login form is still showing."""
    user_id = inputs["UserID"]
    client_id = user_id + "_U"
    login_url = (f"https://trade.shoonya.com/OAuthlogin/investor-entry-level/login"
                 f"?api_key={client_id}&route_to={user_id}")

    captured = start_shoonya_capture(page)
    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_selector("input[type='password']", timeout=30000)
    page.wait_for_timeout(1000)

    url = None
    for attempt in (1, 2):
        submit_credentials(page, inputs, get_safe_totp(inputs["TOTPKey"]))
        print(f"Credentials submitted (attempt {attempt}). Capturing auth code...")
        try:
            url = wait_for_capture(page, captured, CODE_WAIT_SECS)
            break
        except TimeoutError as e:
            print(e)
            # If the login form is gone we are on another page; retrying would not help.
            if attempt == 2 or page.locator(LOGIN_BTN).count() == 0:
                raise Exception(f"Could not capture auth code. Page URL: {page.url}")
            print("Login form still showing, retrying with a fresh OTP...")

    print("Captured URL:", url)
    code = parse_qs(urlparse(url).query).get("code", [None])[0]
    if not code:
        raise Exception(f"No code found in URL: {url}")
    return code


def generate_access_token(auth_code, inputs):
    """Exchanges auth code for the Shoonya session token and saves it."""
    user_id = inputs["UserID"]
    client_id = user_id + "_U"
    checksum = hashlib.sha256((client_id + inputs["APISecret"] + auth_code).encode()).hexdigest()

    payload = "jData=" + json.dumps({"code": auth_code, "checksum": checksum, "uid": user_id})
    response = requests.post(
        TOKEN_URL, data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    print("Raw Response:", response.text)
    res = response.json()

    if "access_token" not in res:
        raise Exception(f"Token generation failed: {res}")

    emsg = res.get("emsg", "")
    dict_to_csv({
        "token": res.get("susertoken", ""),
        "stat": res.get("stat", ""),
        "emsg": emsg,
        "dmsg": emsg,
        "date": datetime.now().strftime("%d"),
        "user": user_id,
    }, LOGIN_FILE)
    print(f"Logged in successfully, response saved to {LOGIN_FILE}")


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
            browser = p.chromium.launch(headless=HEADLESS, args=["--window-size=1920,1080"])
            page = browser.new_context().new_page()
            auth_code = get_auth_code(page, inputs)
            browser.close()

        generate_access_token(auth_code, inputs)
    except Exception as e:
        print(f"An error occurred: {e}")
