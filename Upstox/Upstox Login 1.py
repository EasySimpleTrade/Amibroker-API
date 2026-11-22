

import os
import time
import json
import requests
import pyotp
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import csv
import sys
import tempfile

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================================
# CONFIG
# ============================================================================

inputs_file = r'C:\API\Files\UpstoxInputs 1.csv'


def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                key, value = row[0], row[1]
                data_dict[key] = value
    return data_dict


login_dict = read_csv_dict(inputs_file)

CLIENT_ID = login_dict['APIKey']
CLIENT_SECRET = login_dict['APISecret']
PIN = login_dict['Pin']
user_id = login_dict['UserID']
MOBILE_NUMBER = login_dict['Mobile']
TOTP_SECRET = login_dict['TOTPKey']
REDIRECT_URI = login_dict['RedirectURL']

# Do not print secrets in normal operation.
print("Upstox credentials loaded from CSV.")

if login_dict["BrowserShow"].lower() == 'yes':
    HEADLESS = False
else:
    HEADLESS = True

USE_PROFILE = True
#HEADLESS = False
TOTP_INTERVAL = 60  # Upstox OTP window; generation uses pyotp.TOTP(...).now()
TOTP_ENTRY_DELAY = 2

STATE = "abcd"

AUTH_DIALOG_URL = (
    f"https://api.upstox.com/v2/login/authorization/dialog"
    f"?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={STATE}"
)

TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"

login_file = r"R:\UpstoxLogin1.txt"

# --- Browser state ---------------------------------------------------------


# Everything browser-related lives in one folder under the Windows temp
# directory (%TEMP%), e.g. C:\Users\<you>\AppData\Local\Temp\upstox_login
APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), "upstox_login")
os.makedirs(APP_TEMP_DIR, exist_ok=True)

CHROME_PROFILE_DIR = os.path.join(APP_TEMP_DIR, "chrome_profile")

# Saved session (cookies + localStorage). This is what actually lets the next
# run skip the mobile/TOTP pages.
SESSION_FILE = os.path.join(APP_TEMP_DIR, "session.json")


WAIT_SECS = 20
SCREEN_DETECT_SECS = 15   # how long to wait to see PIN or mobile screen after goto

# Prints cookie names (never values) and whether they are session/persistent.
DEBUG_COOKIES = False #False True


# ============================================================================
# SELECTORS
# ============================================================================

PIN_SELECTOR = "#pinCode"

MOBILE_SELECTORS = [
    "input[id='mobileNum']:visible",
    "input[placeholder*='Mobile' i]:visible",
    "input[placeholder*='mobile' i]:visible",
    "input[type='tel']:visible",
]

OTP_SELECTORS = [
    "input[id='otpNum']:visible",
    "input[placeholder*='OTP' i]:visible",
    "input[autocomplete='one-time-code']:visible",
    "input[inputmode='numeric']:visible",
]

CONTINUE_BUTTON_SELECTORS = [
    "button:has-text('Continue'):visible",
    "button:has-text('Verify'):visible",
    "button:has-text('Submit'):visible",
]


def first_visible(page, selectors):
    """Return the first visible locator from a selector list."""
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible():
                return locator
        except Exception:
            pass
    return None


def visible_inputs(page):
    """Return all currently visible input elements."""
    return page.locator("input:visible")


def print_visible_inputs(page):
    """Diagnostic output useful if Upstox changes its login DOM again."""
    print("\nVisible input fields:")

    inputs = visible_inputs(page)
    count = inputs.count()

    for i in range(count):
        el = inputs.nth(i)
        try:
            print(
                f"  [{i}] "
                f"type={el.get_attribute('type')!r}, "
                f"id={el.get_attribute('id')!r}, "
                f"name={el.get_attribute('name')!r}, "
                f"placeholder={el.get_attribute('placeholder')!r}, "
                f"inputmode={el.get_attribute('inputmode')!r}"
            )
        except Exception:
            pass

    print()


def enter_otp(page, code):
    """
    Enter OTP/TOTP robustly.

    Handles:
      1. One visible OTP input.
      2. Six separate OTP boxes.
      3. A visible one-time-code/numeric input.
    """

    # Give the OTP screen a moment to finish rendering.
    page.wait_for_timeout(500)

    # First try explicit OTP-like fields.
    otp = first_visible(page, OTP_SELECTORS)

    if otp is not None:
        try:
            otp.click()
            otp.press_sequentially(code, delay=80)
            return
        except Exception:
            pass

    # If Upstox renders six individual boxes, use the visible numeric inputs.
    inputs = visible_inputs(page)

    numeric_inputs = []

    for i in range(inputs.count()):
        el = inputs.nth(i)

        try:
            input_type = (el.get_attribute("type") or "").lower()
            input_mode = (el.get_attribute("inputmode") or "").lower()
            placeholder = (el.get_attribute("placeholder") or "").lower()

            if (
                input_type in ("text", "tel", "number", "")
                or input_mode == "numeric"
            ):
                # Avoid accidentally selecting a mobile-number field.
                if "mobile" not in placeholder and "phone" not in placeholder:
                    numeric_inputs.append(el)

        except Exception:
            pass

    # Six OTP boxes.
    if len(numeric_inputs) >= 6:
        print("Detected separate OTP input boxes.")

        numeric_inputs[0].click()

        # Keyboard typing lets the page's own auto-advance logic move
        # between six separate OTP boxes.
        page.keyboard.type(code)

        return

    # Last fallback: focus the first visible input and type the code.
    if inputs.count() == 1:
        inputs.first.click()
        page.keyboard.type(code)
        return

    #print_visible_inputs(page)

    raise Exception(
        "Could not identify the Upstox OTP input field. "
        "The login page DOM may have changed."
    )


# ============================================================================
# SESSION SAVE / RESTORE
# ============================================================================

def save_session(context, label=""):
    """Save cookies + localStorage, including session cookies."""
    try:
        context.storage_state(path=SESSION_FILE)
        print(f"Session saved{label}.")
    except Exception as e:
        print("Could not save session:", e)


def restore_cookies(context):
    """Load saved cookies into a persistent-profile context."""
    if not os.path.exists(SESSION_FILE):
        print("No saved session file yet - full login will be needed.")
        return

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        cookies = state.get("cookies", [])
        if cookies:
            context.add_cookies(cookies)

        print(f"Restored {len(cookies)} saved cookies.")
    except Exception as e:
        print("Could not restore saved cookies:", e)


def print_cookie_summary(context):
    """Names only, never values. Shows which cookies die when the browser closes."""
    print("\nCookies in browser context:")
    try:
        for c in context.cookies():
            kind = "session" if c.get("expires", -1) == -1 else "persistent"
            print(f"  {c['domain']:<32} {c['name']:<32} {kind}")
    except Exception as e:
        print("  (could not read cookies)", e)
    print()


def open_browser(p):
    """Returns (browser_or_None, context)."""
    launch_args = ["--no-first-run", "--no-default-browser-check"]
    viewport = {"width": 1200, "height": 900}

    if USE_PROFILE:
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            headless=HEADLESS,
            viewport=viewport,
            args=launch_args,
        )
        restore_cookies(context)
        return None, context

    browser = p.chromium.launch(headless=HEADLESS, args=launch_args)

    if os.path.exists(SESSION_FILE):
        try:
            context = browser.new_context(
                viewport=viewport,
                storage_state=SESSION_FILE,
            )
            print("Loaded saved session state.")
            return browser, context
        except Exception as e:
            print("Saved session file unusable, starting clean:", e)

    return browser, browser.new_context(viewport=viewport)


def wait_for_pin_or_mobile(page, timeout_secs):
    """Return 'pin', 'mobile', or None - whichever screen shows up first."""
    deadline = time.time() + timeout_secs

    while time.time() < deadline:
        try:
            if page.locator(PIN_SELECTOR).is_visible():
                return "pin"
        except Exception:
            pass

        if first_visible(page, MOBILE_SELECTORS) is not None:
            return "mobile"

        page.wait_for_timeout(250)

    return None


# ============================================================================
# PLAYWRIGHT LOGIN
# ============================================================================

def get_auth_code():
    with sync_playwright() as p:

        browser, context = open_browser(p)

        page = context.pages[0] if context.pages else context.new_page()

        # Upstox redirects after PIN to https://localhost/?code=...
        # We capture that exact navigation request. The localhost page itself
        # does not need to load successfully.
        redirect_code_url = {"url": None}

        try:
            print("Opening Upstox authorization dialog...")

            page.goto(
                AUTH_DIALOG_URL,
                wait_until="domcontentloaded",
                timeout=WAIT_SECS * 1000,
            )

            # ------------------------------------------------------------
            # Which screen did we land on? PIN (session alive) or mobile.
            # ------------------------------------------------------------
            screen = wait_for_pin_or_mobile(page, SCREEN_DETECT_SECS)
            print(f"Landed on: {screen} screen  ({page.url})")

            if screen == "pin":
                print("Session already active - went straight to PIN.")

            elif screen == "mobile":

                if not MOBILE_NUMBER:
                    raise Exception(
                        "Landed on the mobile-number screen but MOBILE_NUMBER "
                        "is not set in CSV."
                    )

                # --------------------------------------------------------
                # MOBILE
                # --------------------------------------------------------
                print("Mobile-number screen detected.")

                mobile_field = first_visible(page, MOBILE_SELECTORS)

                if mobile_field is None:
                    print_visible_inputs(page)
                    raise Exception(
                        "Could not find the visible Upstox mobile-number field."
                    )

                mobile_field.fill(MOBILE_NUMBER)

                # Click the actual Get OTP button, not a generic Continue.
                get_otp = page.get_by_role(
                    "button",
                    name="Get OTP",
                    exact=True
                )

                try:
                    get_otp.wait_for(
                        state="visible",
                        timeout=5000,
                    )
                    get_otp.click()

                except PlaywrightTimeoutError:
                    # Fallback only if Upstox has changed the button text.
                    get_otp = page.locator(
                        "button:visible"
                    ).filter(
                        has_text="Get OTP"
                    ).first

                    get_otp.click()

                print("Get OTP clicked.")

                # --------------------------------------------------------
                # WAIT FOR OTP OR PIN
                # --------------------------------------------------------
                otp_ready = False
                pin_ready = False

                deadline = time.time() + WAIT_SECS

                while time.time() < deadline:

                    try:
                        if page.locator(PIN_SELECTOR).is_visible():
                            pin_ready = True
                            break
                    except Exception:
                        pass

                    if first_visible(page, OTP_SELECTORS) is not None:
                        otp_ready = True
                        break

                    # Also detect six individual OTP boxes.
                    inputs = visible_inputs(page)

                    if inputs.count() >= 6:
                        otp_ready = True
                        break

                    page.wait_for_timeout(250)

                # --------------------------------------------------------
                # OTP / TOTP
                # --------------------------------------------------------
                if otp_ready:

                    if TOTP_SECRET:
                        print(
                            f"OTP screen detected - waiting "
                            f"{TOTP_ENTRY_DELAY}s before entering TOTP..."
                        )

                        time.sleep(TOTP_ENTRY_DELAY)

                        # Avoid entering during seconds 55-59 of the
                        # 60-second window because the OTP is too close
                        # to expiry.
                        while True:
                            second_in_minute = int(time.time()) % 60

                            if second_in_minute < 55:
                                break

                            remaining = 60 - second_in_minute
                            print(
                                f"Near OTP boundary "
                                f"({second_in_minute:02d}s) - "
                                f"waiting {remaining}s for a fresh window..."
                            )
                            time.sleep(1)

                        code = pyotp.TOTP(TOTP_SECRET).now()

                        print(
                            f"Generated TOTP: {code} "
                            f"at second {int(time.time()) % 60:02d}"
                        )

                        print("Entering TOTP...")
                        enter_otp(page, code)
                        print("TOTP entered.")

                    else:
                        input(
                            "SMS OTP sent. Enter it in the browser window, "
                            "then press Enter here to continue..."
                        )

                    # Click Continue on the OTP screen. If the TOTP is
                    # invalid, Upstox stays on this page, so we must NOT
                    # proceed to the PIN screen blindly.
                    page.wait_for_timeout(300)

                    otp_continue_clicked = False

                    button = page.get_by_role(
                        "button",
                        name="Continue",
                        exact=True
                    ).first

                    try:
                        button.wait_for(
                            state="visible",
                            timeout=3000,
                        )
                        button.click()
                        otp_continue_clicked = True
                        print("OTP Continue clicked.")
                    except PlaywrightTimeoutError:
                        pass

                    if not otp_continue_clicked:
                        for selector in CONTINUE_BUTTON_SELECTORS:
                            button = page.locator(selector).first

                            try:
                                if button.is_visible():
                                    button.click()
                                    otp_continue_clicked = True
                                    print("OTP Continue clicked.")
                                    break
                            except Exception:
                                pass

                    if not otp_continue_clicked:
                        raise Exception(
                            "OTP was entered, but the Continue button "
                            "could not be clicked."
                        )

                elif not pin_ready:
                    print_visible_inputs(page)

                    raise Exception(
                        "Neither OTP nor PIN screen appeared after "
                        "clicking Get OTP."
                    )

                # --------------------------------------------------------
                # WAIT FOR PIN SCREEN
                # --------------------------------------------------------
                try:
                    page.locator(PIN_SELECTOR).wait_for(
                        state="visible",
                        timeout=WAIT_SECS * 1000,
                    )
                except PlaywrightTimeoutError:
                    print(
                        "PIN screen did not appear. "
                        "Upstox may have rejected the OTP/TOTP."
                    )
                    print_visible_inputs(page)
                    raise

                print("PIN screen detected.")

            else:
                print_visible_inputs(page)
                raise Exception(
                    f"Neither the mobile nor the PIN screen appeared within "
                    f"{SCREEN_DETECT_SECS}s. Current URL: {page.url}"
                )

            # ------------------------------------------------------------
            # PIN screen reached = Upstox session is established.
            # Save it now so the next run can skip mobile + TOTP.
            # ------------------------------------------------------------
            if DEBUG_COOKIES:
                print_cookie_summary(context)

            save_session(context, " (PIN screen reached)")

            # ------------------------------------------------------------
            # PIN
            # ------------------------------------------------------------
            pin_field = page.locator(PIN_SELECTOR)

            pin_field.wait_for(
                state="visible",
                timeout=WAIT_SECS * 1000,
            )

            pin_field.fill(PIN)

            # Start waiting for the redirect BEFORE clicking so the very
            # fast redirect cannot be missed.
            redirect_predicate = (
                lambda request:
                request.url.startswith(REDIRECT_URI)
                and "code=" in request.url
            )

            try:
                pin_continue = page.get_by_role(
                    "button",
                    name="Continue",
                    exact=True
                ).first

                pin_continue.wait_for(
                    state="visible",
                    timeout=5000,
                )

                with page.expect_request(
                    redirect_predicate,
                    timeout=WAIT_SECS * 1000
                ) as redirect_info:
                    pin_continue.click(no_wait_after=True)

                redirect_request = redirect_info.value
                redirect_code_url["url"] = redirect_request.url

            except PlaywrightTimeoutError:
                # Fallback for changed button markup.
                button = page.locator(
                    "button:visible"
                ).filter(
                    has_text="Continue"
                ).first

                with page.expect_request(
                    redirect_predicate,
                    timeout=WAIT_SECS * 1000
                ) as redirect_info:
                    button.click(no_wait_after=True)

                redirect_request = redirect_info.value
                redirect_code_url["url"] = redirect_request.url

            print("PIN submitted.")

            # ------------------------------------------------------------
            # REDIRECT WITH ?code=
            # ------------------------------------------------------------
            final_url = redirect_code_url["url"]

            if not final_url:
                raise Exception(
                    "OAuth authorization code redirect was not captured."
                )

            print("Redirect URL:", final_url)

            parsed = urlparse(final_url)
            qs = parse_qs(parsed.query)

            code = qs.get("code", [None])[0]

            if not code:
                error = qs.get("error", [None])[0]
                error_description = qs.get(
                    "error_description",
                    [None]
                )[0]

                if error:
                    raise Exception(
                        f"Upstox OAuth error: {error}"
                        + (
                            f" - {error_description}"
                            if error_description
                            else ""
                        )
                    )

                raise Exception(
                    f"No 'code' found in redirect URL: {final_url}"
                )

            # Refresh the saved session once more, in case cookies were
            # updated during PIN submission.
            save_session(context, " (after redirect)")

            return code

        except Exception:
            try:
                screenshot = r"R:\Upstox_login_error.png"
                page.screenshot(path=screenshot, full_page=True)
                print(f"Login diagnostic screenshot saved to: {screenshot}")
            except Exception:
                pass

            raise

        finally:
            try:
                context.close()
            except Exception:
                pass

            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass


# ============================================================================
# TOKEN EXCHANGE
# ============================================================================

def get_access_token(auth_code: str) -> str:

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(
        TOKEN_URL,
        headers=headers,
        data=data,
        timeout=30,
    )

    response_data = response.json()

    if response.status_code == 200 and "access_token" in response_data:
        return response_data["access_token"]

    raise Exception(
        f"Error getting access token: {response_data}"
    )


# ============================================================================
# WRITE DICTIONARY TO CSV
# ============================================================================

def dict_to_csv(dictionary, out_file):

    with open(out_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        for key, value in dictionary.items():
            writer.writerow([key, value])


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "test-totp":

        if not TOTP_SECRET:
            print("TOTP_SECRET is empty - nothing to test.")

        else:
            totp = pyotp.TOTP(
                TOTP_SECRET,
                interval=TOTP_INTERVAL
            )

            code = totp.now()
            remaining = TOTP_INTERVAL - (time.time() % TOTP_INTERVAL)

            print(
                f"Code: {code}  "
                f"(valid for {remaining:.0f}s more, "
                f"interval={TOTP_INTERVAL}s)"
            )

            print(
                "Compare this against your authenticator app right now."
            )

        sys.exit(0)

    try:
        print("Auth dialog URL:", AUTH_DIALOG_URL)

        auth_code = get_auth_code()
        print("Auth code:", auth_code)

        access_token = get_access_token(auth_code)

        print("Access Token:", access_token)

        today_date = datetime.now().strftime('%d')

        login_data = {
            'token': access_token,
            'date': today_date,
            'user': user_id
        }

        dict_to_csv(login_data, login_file)

        print(f"Access token saved to {login_file}")

        time.sleep(2)

    except Exception as e:

        print("Login failed:", str(e))
        input("Press Enter here to exit...")
