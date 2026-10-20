import requests
import pandas as pd
import xmltodict
from tqdm import tqdm
import aiohttp
import asyncio
import retrying
import numpy as np
import json
from datetime import datetime, timedelta
import time
import warnings
import re
warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)

juniper_user = 'xxxxxxx'
juniper_password = 'xxxxxxxx'
orgId = 'xxxxxxx'

keywords = ["HCN Inquiry","HCN Request","HCN Update","HCN Required","hcn needed","Need Hotel Confirmation Number","HCN RQ","Need HCN","Reconfirmation number",
           "Booking Confirmation Required","Confirmation Number Request","Kind Attention: Reservation","Reconfirm Booking","Urgent HCN","HCN urgent",
           "Reconfirmation of Booking","Booking confirmation Requires","Unconfirmed Booking","Kind Attn: Reservation","RECONFIRMATION","hc needed",
           "Online Hotel Booking - Auto Confirmed","HCN REQUST","HCN-Request","request for HCN","Inquiry confirmation number","HCN REQ",
           "Require Hotel Confirmation","Asking for HCN","Request for Hotel Confirmation","Confirmation Number Request","ASK FOR HCN"]
           
def return_book_code(subject):
    global keywords
    for k in keywords:
        if k.lower() in subject.lower():
            return(list(set(re.findall(r'\b[A-Z0-9]{6}\b',subject))))
            break
     
def renewAccessToken2():
    URL = "https://accounts.zoho.com/oauth/v2/token"

    access_token = 'xxxxxxx'
    code = ""
    client_id = "xxxxxxx"
    client_secret = "xxxxxx"
    grant_type = "authorization_code"
    refresh_token = "xxxxxx"

    params_refresh_token = {"refresh_token": refresh_token,"client_id": client_id,
        "client_secret": client_secret,"scope": ["Desk.tickets.ALL", "Desk.tickets.UPDATE", "Desk.tickets.CREATE", "Desk.search.READ", "Desk.tickets.READ"],
        "grant_type": "refresh_token"}

    while True:
        try:
            access_token_refresh = requests.post(url=URL, params=params_refresh_token)
            access_token_refresh_dict = json.loads(access_token_refresh.text)
            new_access_token = access_token_refresh_dict['access_token']
            return new_access_token
            break
        except Exception as e:
            print(e)
            pass
            
def GetBookingData(code):
    url = "https://www.eetglobal.com/wsExportacion/wsBookings.asmx"
    headers = {
        'content-type': 'text/xml',
        'SOAPAction': "http://juniper.es/getBookings",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "*",
        "Connection": "keep-alive"
    }
    body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <getBookings xmlns="http://juniper.es/">
              <user>{juniper_user}</user>
              <password>{juniper_password}</password>
              <BookingCode>{code}</BookingCode>
            </getBookings>
          </soap:Body>
        </soap:Envelope>"""
    try:
        response = requests.post(url, data=body, headers=headers)
        responseDict = xmltodict.parse(response.text)
        
        AllBookings = responseDict['soap:Envelope']['soap:Body']['getBookingsResponse']['getBookingsResult']['wsResult']['Bookings']['Booking']
        
        if isinstance(AllBookings['Lines']['Line'], list):
            try:
                if isinstance(AllBookings['Lines']['Line'][0]['roomlist']['room'],list):
                    remark = AllBookings['Lines']['Line'][0]['roomlist']['room'][0]['confirmationreference']
                else:
                    remark = AllBookings['Lines']['Line'][0]['roomlist']['room']['confirmationreference']
            except:
                remark = None
            row = [code,
                   remark,
                   AllBookings['Lines']['Line'][0]['ProductGroupName'],
                   AllBookings['Lines']['Line'][0]['BeginTravelDate'][:10],
                   AllBookings['@Status'],
                   AllBookings['Customer']['Name']
                  ]
        else:
            try:
                if isinstance(AllBookings['Lines']['Line']['roomlist']['room'],list):
                    remark = AllBookings['Lines']['Line']['roomlist']['room'][0]['confirmationreference']
                else:
                    remark = AllBookings['Lines']['Line']['roomlist']['room']['confirmationreference']
            except:
                remark = None
            row = [code,
                   remark,
                   AllBookings['Lines']['Line']['ProductGroupName'],
                   AllBookings['Lines']['Line']['BeginTravelDate'][:10],
                   AllBookings['@Status'],
                   AllBookings['Customer']['Name']
                  ]
        #print(code,remark)
        return row
    except Exception as e:
        #print(code, e)
        return None


def reply_with_hcn(ticket_id,HCN,email):
    content = f"""
    <head>
    <style>
        body {{font-family: "Times New Roman", Times, serif;margin: 0;padding: 0;font-size: 12px;color: #000;}}
        .container {{margin: 0;padding: 0;}}
        .footer {{background-color: #f7f7f7;padding: 10px;text-align: center;font-size: 11px;}}
    </style>
    </head>
    <body>
    <div class="container">
        <p>Dear Partner,</p>
    
        <p>Greetings from EET Global.</p>
    
        <p>
            This is an automated message to inform you that your booking has been successfully confirmed & paid under confirmation number: <strong>{HCN}</strong>.
        </p>
    
        <p>
            This will be the final response on this ticket.<br><br>
            If this message does not fully address your inquiry or you require further assistance,
            kindly create a new ticket. With new subject line & new inquiry without mentioned HCN.<br><br>
            Please note that replying again to this ticket will not be monitored. Our support team will be happy to assist you via a new ticket.
        </p>
    
        <p>Thank you for choosing EET Global.</p>
    </div>
    
    <div class="footer">
        <p><strong>Customer Care – EET Global Team</strong></p>
        <p>Tel: +202-33080700 | +202-33057373 (Ext: 1350)</p>
        <p>1st &amp; 2nd Floor, 94 Shehab St., Mohandeseen, Giza, Egypt</p>
    </div>
    </body>
    """
    ticket_data={"channel" : "EMAIL","content":content,"contentType":'html',"to":email
             ,'fromEmailAddress':"customer.care@eetglobal.net"
             ,"cc":"customer.care@eetglobal.net"}

    request=requests.post(f'https://desk.zoho.com/api/v1/tickets/{ticket_id}/sendReply?sendImmediately=true', headers=headers,data=json.dumps(ticket_data))

def reply_without_hcn(ticket_id,BC,email):
    content = f"""
    <head>
    <style>
        body {{font-family: "Times New Roman", Times, serif;margin: 0;padding: 0;font-size: 12px;color: #000;}}
        .container {{margin: 0;padding: 0;}}
        .footer {{background-color: #f7f7f7;padding: 10px;text-align: center;font-size: 11px;}}
    </style>
    </head>
    <body>
    <div class="container">
        <p>Dear Partner,</p>
    
        <p>Greetings from EET Global.</p>
    
        <p>
            This is an automated message to inform you that your booking has been successfully confirmed under our allotment with reference number : {BC}.
            We are currently working to obtain the hotel’s direct confirmation number, and once it is updated, it will be shared automatically.
        </p>
    
        <p>
            If this message does not fully address your inquiry or you require further assistance,
            kindly create a new ticket. With new subject line & new inquiry without mentioned HCN, 
            as this may result in repeated automated emails. our support team will be happy to assist you. 
        </p>
    
        <p>Thank you for choosing EET Global.</p>
    </div>
    
    <div class="footer">
        <p><strong>Customer Care – EET Global Team</strong></p>
        <p>Tel: +202-33080700 | +202-33057373 (Ext: 1350)</p>
        <p>1st &amp; 2nd Floor, 94 Shehab St., Mohandeseen, Giza, Egypt</p>
    </div>
    </body>
    """
    ticket_data={"channel" : "EMAIL","content":content,"contentType":'html',"to":email
             ,'fromEmailAddress':"customer.care@eetglobal.net"
             ,"cc":"customer.care@eetglobal.net"}

    request=requests.post(f'https://desk.zoho.com/api/v1/tickets/{ticket_id}/sendReply?sendImmediately=true', headers=headers,data=json.dumps(ticket_data))

def ticket_update(ticket_id,BC,HCN,ProductGroup,BeginDate,email,customer):
    ticket_data={"email":email,"cf" : 
             {"cf_closed_by":"Auto Confirmation","cf_action":"Auto Confirmation","cf_booking_reference":BC,"cf_confirmation_number":HCN,
             "cf_check_in_date":BeginDate,"cf_product_group":ProductGroup,"cf_customer_name":customer}}
    #print(ticket_id)
    request=requests.patch(f'https://desk.zoho.com/api/v1/tickets/{ticket_id}', headers=headers,data=json.dumps(ticket_data))

def get_transitions(ticket_id):
    blueprint_data = ''
    url = f"https://desk.zoho.com/api/v1/tickets/{ticket_id}/blueprint"
    
    response = requests.get(url, headers=headers)
    
    blueprint_data = response.json()
    
    current_status = blueprint_data['state']['name']
    all_transitions = pd.DataFrame(blueprint_data['transitions'])
    return current_status, all_transitions

def close_ticket(ticket_id, transaction_id):

    url = f"https://desk.zoho.com/api/v1/tickets/{ticket_id}/transitions/{transaction_id}/perform"
   
    response = requests.post(url,headers=headers,data = json.dumps({}))

while True:       
    accessToken = renewAccessToken2()
    headers = {
        "Authorization": f"Zoho-oauthtoken {accessToken}",
        "orgId": orgId,
        "contentType": "application/json; charset=utf-8"}

    ticketsData = []
    ticketsIds = set()
    threadIds = []

    url = 'https://desk.zoho.com/api/v1/tickets/search?'
    #for i in tqdm(range(0, 100, 100)):
    try:
        params = f"from=0&limit=100&departmentId=766285000000006907&sortBy=-modifiedTime"#&id=766285000489257948&sortBy=-modifiedTime&modifiedTimeRange={(datetime.now()).strftime('%Y-%m-%dT00:00:00.000Z')},{datetime.now().strftime('%Y-%m-%dT%H:00:00.000Z')}"
        ticketResponse = requests.get(url, params=params, headers=headers)
        ticketsData += ticketResponse.json()["data"]
    except Exception as e:
            pass

    df = pd.DataFrame(ticketsData)

    if len(df) > 0:

        #df['direction'] = df['lastThread'].apply(lambda x : x['direction'])
        df['direction'] = df['lastThread'].apply(lambda x: x['direction'] if isinstance(x, dict) else None)
        df['ConfirmationNumber'] = df['customFields'].apply(lambda x : x['Confirmation Number'] if isinstance(x, dict) else None)
        df = df[
                (df['direction']=='in') &
                (~df['ConfirmationNumber'].str.contains(
                'confirmation|confrimation|conformation',case=False,na=False
                ))
             ]

        df['booking_code'] = df['subject'].apply(lambda x:return_book_code(x))
        
        BC_df = df[df['booking_code'].apply(lambda x: bool(x))]
        
        if len(BC_df) > 0:

            for i, r in tqdm(BC_df.iterrows(), total = len(BC_df)):
        
                for k in r['booking_code']:
                    hcn = None
                    book_code = None
                    product_group = None
                    beginDate = None
                    status = None
                    customer = None
                    x = GetBookingData(k)

                    if x and len(x) > 1 and isinstance(x[1], str):
                        desc = x[1].lower()
                        if any(word in desc for word in ['confirmation', 'confrimation', 'conformation']):
                            hcn = x[1]
                        book_code = x[0]
                        product_group = x[2]
                        beginDate = x[3]
                        status = x[4]
                        customer = x[5]
                        break
                    elif x and len(x) > 1:
                        book_code = x[0]
                        product_group = x[2]
                        beginDate = x[3]
                        status = x[4]
                        customer = x[5]
                        break  

                BC_df.at[i, 'HCN'] = hcn
                BC_df.at[i, 'BC'] = book_code
                BC_df.at[i, 'ProductGroup'] = product_group
                BC_df.at[i, 'BeginDate'] = beginDate
                BC_df.at[i, 'Status'] = status
                BC_df.at[i, 'Customer'] = customer

            final_df = BC_df[['subject','id','HCN','BC','ProductGroup','BeginDate','email','Status','Customer']]
            final_df = final_df[final_df['ProductGroup'].notna()].copy()
            final_df['Status'] = final_df['Status'].astype(str)
            final_df = final_df[final_df['Status'].str.contains('ok|con',case=False, na=False)].copy()
            final_df['BeginDate'] = pd.to_datetime(final_df['BeginDate'])
            final_df = final_df[ final_df['BeginDate'] >= pd.Timestamp.today().normalize() ].copy()
            final_df['BeginDate'] = final_df['BeginDate'].dt.strftime("%Y-%m-%d")
            final_df = final_df[~final_df['subject'].str.contains('cancel|amend|waive|modify|modification|refund',case=False,na=False)]
            final_df.reset_index(drop=True, inplace=True)

            if len(final_df) > 0:
                for index, row in final_df.iterrows():

                    if pd.isna(row['HCN']) or str(row['HCN']).strip() == "":
                        reply_without_hcn(row['id'],row['BC'],row['email']) 
                    else:
                        reply_with_hcn(row['id'],row['HCN'],row['email'])
                        
                    ticket_update(row['id'],row['BC'],row['HCN'],row['ProductGroup'],row['BeginDate'],row['email'],row['Customer'])
                    
                    current_status, transitions_df = get_transitions(row['id'])
                    if current_status != 'Closed':
                        transition_id = transitions_df[(transitions_df['fromState']==current_status) & (transitions_df['toState']=='Closed')]['id'].values[0]
                        close_ticket(row['id'], transition_id)
                    print(f"Done at {datetime.now()}- {row['id']}")
            else:
                print(f"No Booking to Reply at {datetime.now()}")
        else:
            print(f"No HCN Tickets to Reply at {datetime.now()}")
        time.sleep(300)
    else:
        print(f"No Tickets Received or May be an issue in search API at {datetime.now()}")
        time.sleep(300)