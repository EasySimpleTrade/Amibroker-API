'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

#Required Libraries
import requests
import base64
import jwt
import csv
from datetime import datetime

# Input
consumer_key = 'vgkwQ1RhuILR3xPdgm2jlP57Jeka' #Change consumer key
consumer_secret = 'NYUV_P5_D9xtMoyynYfafDrJgqQa' #Change consumer secret
api_user_name = 'client12345' #Change api portal user name
api_pass_word = 'api_password' #Change api portal password
mobile_number = '+919876543210' #Change your registered mobile number with +91 to login
pass_word = 'acc_password' #Change your kotak account password
login_file = r'R:\KotakLogin1.txt' #Change the file path to save response file if required
access_token_url = 'https://napi.kotaksecurities.com/oauth2/token'
validate_url = 'https://gw-napi.kotaksecurities.com/login/1.0/login/v2/validate'
generate_url = 'https://gw-napi.kotaksecurities.com/login/1.0/login/otp/generate'

#Functions

#Write Dictionary to CSV
def dict_to_csv(dictionary, out_file):
    with open(out_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        for key, value in dictionary.items():
            writer.writerow([key, value])

#Access token
def get_access_token(consumer_key, consumer_secret, access_token_url, api_user_name, api_pass_word):    
    auth_string = f"{consumer_key}:{consumer_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        'Authorization': f'Basic {auth_base64}'
    }

    data = {
        'grant_type': 'password',
        'username': api_user_name,
        'password': api_pass_word
    }

    response = requests.post(access_token_url, headers=headers, data=data)

    if response.status_code == 200:
        response_json = response.json()
        access_token = response_json.get('access_token')
        return access_token
    else:                
        print(f"Response: {response.text}")
        return None

#Generate OTP
def generate_otp(validate_url, generate_url, access_token, mobile_number, pass_word):
    
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    validate_payload = {
        "mobileNumber": mobile_number,
        "password": pass_word
    }

    validate_response = requests.post(validate_url, headers=headers, json=validate_payload)
    
    validate_json = validate_response.json()
    if 'data' not in validate_json:
        print("Error:", validate_json)
        return
    
    validate_data = validate_json.get('data', {})
    
    view_token = validate_data.get('token')
    hs_server_id = validate_data.get('hsServerId')
    sid = validate_data.get('sid')

    if validate_data.get('isUserPwdExpired', True):
        print("Password expired, please change the password.")
        return

    decoded_token = jwt.decode(view_token, options={"verify_signature": False})  
    user_id = decoded_token.get('sub')

    otp_payload = {
        "userId": user_id,
        "sendEmail": True,
        "isWhitelisted": True
    }

    otp_response = requests.post(generate_url, headers=headers, json=otp_payload)
   
    if otp_response.status_code == 201:
        return view_token, sid, hs_server_id, user_id
        #print("OTP generated successfully.")
    else:
        print(f"Failed to generate OTP: {otp_response.status_code} - {otp_response.text}")
       
def session_token(validate_url, SID, view_token, access_token, user_id, login_file, otp=None, mpin=None):
    
    headers = {
        "accept": "*/*",
        "sid": SID,
        "Auth": view_token, 
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    session_payload = {
        "userId": user_id,
    }
    
    if otp:
        session_payload['otp'] = otp
    elif mpin:
        session_payload['mpin'] = mpin
    else:
        raise ValueError("Either OTP or MPIN must be provided.")

    session_response = requests.post(validate_url, headers=headers, json=session_payload)
    
    if session_response.status_code == 201:
        print(session_response.text)
        session_data = session_response.json().get('data', {})
        session_token = session_data.get('token')
        sid = session_data.get('sid')
        hs_server_id = session_data.get('hsServerId')
        ucc_id = session_data.get('ucc')
        today_date = datetime.now().strftime('%d')

        login_data = {'access':access_token, 'session': session_token, 'sid': sid, 'hsServerId': hs_server_id, 'date': today_date, 'user': ucc_id}
        
            
        dict_to_csv(login_data, login_file)

        print(f"Session validated successfully, response saved to {login_file}")
    else:
        print(f"Failed to validate session: {session_response.text}")
        input("Press any Key to Exit...")



# Get access token
access_token = get_access_token(consumer_key, consumer_secret, access_token_url, api_user_name, api_pass_word)
#print(f"Access Token: {access_token}")

#Generate OTP
if access_token:    
    view_token, sid, hs_server_id, user_id = generate_otp(validate_url, generate_url, access_token, mobile_number, pass_word)
    
#print(f"View Token: {view_token}")  
#print(f"SID: {sid}")
#print(f"Server ID : {hs_server_id}") 
#print(f"User ID (sub): {user_id}")

#otp = input('Enter OTP: ')
mpin = '123456' #Change MPIN Here

if access_token:
    session_token(validate_url,sid, view_token, access_token, user_id, login_file, mpin=mpin)# for otp change mpin=mpin to otp=otp    
