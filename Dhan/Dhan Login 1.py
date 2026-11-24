'''
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade

'''

import csv
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import pyotp
import requests
from playwright.sync_api import sync_playwright

# ==========================================
# CONFIGURATION & FILE PATHS
# ==========================================
LOGIN_FILE = r"R:\DhanLogin1.txt"  # Change directory if needed. C:\ or C:\API\
INPUTS_FILE = r"C:\API\Files\DhanInputs 1.csv"

HEADLESS = False   # Keep False so you can see browser actions
WAIT_SECS = 20     # Timeout in seconds for each page step
REDIRECT_WAIT_SECS = 30


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


def start_redirect_capture(page, redirect_url, key="tokenId="):
    """
    Call BEFORE the login steps. Captures the first URL that contains both
    `redirect_url` (the RedirectURL from the inputs CSV, e.g. 'localhost' or
    'http://localhost') and `key`. Serves a blank page for that URL so the
    browser does not show a 'refused to connect' error.
    """
    captured = {"url": None}

    def matches(url):
        return redirect_url in url and "dhan.co" not in url

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


def wait_for_capture(page, captured, timeout):
    """Waits (using Playwright's wait so events fire) until a URL is captured."""
    start = time.time()
    while not captured["url"]:
        if time.time() - start > timeout:
            raise TimeoutError(f"Timed out waiting for redirect URL. Last page URL: {page.url}")
        page.wait_for_timeout(200)
    return captured["url"]


# ==========================================
# DHAN-SPECIFIC FUNCTIONS
# ==========================================

def generate_consent(inputs):
    """Step 1: generate consent and return the browser login URL."""
    url = f"https://auth.dhan.co/app/generate-consent?client_id={inputs['UserID']}"
    headers = {"app_id": inputs["APIKey"], "app_secret": inputs["APISecret"]}
    response = requests.post(url, headers=headers).json()

    if response.get("status") != "success":
        raise Exception(f"Consent API error: {response}")

    login_url = f"https://auth.dhan.co/login/consentApp-login?consentAppId={response['consentAppId']}"
    print("Login URL:", login_url)
    return login_url


def enter_digits(page, boxes, digits, delay_ms):
    """Types one digit into each of the OTP / PIN boxes."""
    for i, digit in enumerate(digits):
        boxes.nth(i).press_sequentially(digit)
        page.wait_for_timeout(delay_ms)


def get_token_id(page, login_url, inputs):
    """Step 2: browser login (mobile -> TOTP -> MPIN). Returns the tokenId from the redirect."""
    timeout = WAIT_SECS * 1000
    captured = start_redirect_capture(page, inputs["RedirectURL"], key="tokenId=")

    page.goto(login_url, wait_until="domcontentloaded")

    # STEP 1: mobile number page
    mobile_field = page.locator("xpath=//input[@placeholder='Enter mobile number']")
    mobile_field.wait_for(state="visible", timeout=timeout)
    print("Mobile number field detected")
    mobile_field.fill(inputs["Mobile"])
    page.locator("xpath=//span[text()='Proceed']").click()

    # STEP 2: TOTP page
    page.locator("xpath=//div[contains(text(),'Enter the TOTP')]").wait_for(state="visible", timeout=timeout)
    print("TOTP page loaded")

    totp = get_safe_totp(inputs["TOTPKey"])
    otp_boxes = page.locator("xpath=//input[@type='tel']")
    if otp_boxes.count() < 6:
        raise Exception("OTP input boxes NOT detected!")
    enter_digits(page, otp_boxes, totp, delay_ms=300)

    # STEP 3: PIN page
    page.locator("xpath=//div[contains(text(), 'Enter')]//span[contains(text(), 'PIN')]").wait_for(
        state="visible", timeout=timeout)
    print("PIN page loaded")
    page.wait_for_timeout(1000)  # let the DOM settle

    pin_boxes = page.locator("xpath=//input[@type='tel' and @autocomplete='one-time-code']")
    print("PIN fields detected:", pin_boxes.count())
    if pin_boxes.count() < 6:
        raise Exception(f"Expected 6 PIN input boxes, but found {pin_boxes.count()}")
    enter_digits(page, pin_boxes, inputs["MPIN"], delay_ms=200)
    print("PIN entered")

    # Wait for the redirect
    url = wait_for_capture(page, captured, REDIRECT_WAIT_SECS)
    print("Redirect URL:", url)

    token_id = parse_qs(urlparse(url).query).get("tokenId", [""])[0]
    if not token_id:
        raise Exception(f"No tokenId found in URL: {url}")
    return token_id


def get_access_token(token_id, inputs):
    """Step 3: exchange tokenId for the access token."""
    url = f"https://auth.dhan.co/app/consumeApp-consent?tokenId={token_id}"
    headers = {"app_id": inputs["APIKey"], "app_secret": inputs["APISecret"]}
    response = requests.get(url, headers=headers).json()
    print(response)

    access_token = response.get("accessToken")
    if not access_token:
        raise Exception(f"No accessToken in response: {response}")
    return access_token


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    try:
        inputs = read_csv_dict(INPUTS_FILE)
        login_url = generate_consent(inputs)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS, args=["--window-size=1200,900"])
            page = browser.new_context().new_page()
            token_id = get_token_id(page, login_url, inputs)
            browser.close()
        print("TOKEN:", token_id)

        access_token = get_access_token(token_id, inputs)
        print("Access Token:", access_token)

        dict_to_csv({
            "access": access_token,
            "date": datetime.now().strftime("%d"),
            "user": inputs["UserID"],
        }, LOGIN_FILE)
        print(f"Login successful! Response saved to {LOGIN_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")
