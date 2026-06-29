# Databricks notebook source
# DBTITLE 1,Installing MSAL
pip install msal

# COMMAND ----------

# DBTITLE 1,Installing openpyxl
pip install openpyxl

# COMMAND ----------

# MAGIC %run /Workspace/Shared/BI/utilities/global_utility

# COMMAND ----------

# DBTITLE 1,importing libraries
import os
import requests
import msal
import base64
from io import BytesIO
import pandas as pd
from pandas import DataFrame
from pyspark.sql import DataFrame
from typing import List

# COMMAND ----------

# DBTITLE 1,Tenant/App variables & obtaining access token
# Step 1: Set up your Azure app registration values

tenant_id = fetch_key_vault_secret('auto_email_sending_tenant_id', '80hg-tenant-id')
client_id = fetch_key_vault_secret('auto_email_sending_client_id', 'auto-email-send-client-id')
client_secret = fetch_key_vault_secret('auto_email_sending_client_secret', 'auto-email-send-client-secret')

scopes = ['https://graph.microsoft.com/.default']

# Set up the confidential client application
app = msal.ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret
)

# Get an access token using the client credentials flow
token_response = app.acquire_token_for_client(scopes=scopes)

# Check if the token was successfully acquired
if "access_token" in token_response:
    access_token = token_response["access_token"]
    print("Access token obtained successfully!")
else:
    print("Error obtaining access token:", token_response.get("error_description"))



# COMMAND ----------

# DBTITLE 1,Obtaining Azure user id
def get_user_id_from_email(access_token, user_email):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data['id']
    elif response.status_code == 403:
        print("Permission issue: Insufficient privileges to fetch user ID.")
    else:
        print(f"Error fetching user ID: {response.status_code}, {response.text}")
    return None

# COMMAND ----------

# DBTITLE 1,Obtaining Azure group id
def get_group_id_from_name(access_token, group_name):
    url = f"https://graph.microsoft.com/v1.0/groups?$filter=displayName eq '{group_name}'"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        groups = response.json().get('value', [])
        if groups:
            # Assuming the first group matches the name
            return groups[0]['id']
        else:
            print("Group not found.")
    else:
        print(f"Error fetching group ID: {response.status_code}, {response.text}")
    return None


# COMMAND ----------

# DBTITLE 1,Verifying user id is in group id
def check_user_in_group(access_token, user_id, group_id):
    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{user_id}/$ref"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 204:
        return True  # User is in the group
    elif response.status_code == 200:
        return True  # User is in the group
    elif response.status_code == 404:
        return False  # User is not in the group
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False


# COMMAND ----------

# DBTITLE 1,Send email without attachment
def send_email_no_attachment(access_token: str, from_email: str, to_email: List[str], email_subject: str, content_type: str, content_body: str):
    
    # Prepare the email message
    group_name = 'Corp_DataEng_AutomatedEmail'  # do not change
    group_id = get_group_id_from_name(access_token, group_name)
    print("Group ID:", group_id)
    
    user_id = get_user_id_from_email(access_token, from_email)
    print("User ID: ", user_id)

    # Handle multiple recipients dynamically
    to_recipients = [
        {
            "emailAddress": {
                "address": recipient
            }
        }
        for recipient in to_email  # Loop through the list of recipients
    ]
    
    email_message = {
        "message": {
            "subject": f"{email_subject}",
            "body": {
                "contentType": f"{content_type}",
                "content": f"{content_body}"
            },
            "toRecipients": to_recipients  # Add the dynamically created list of recipients
        }
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Check if the user is in the group
    if check_user_in_group(access_token, user_id, group_id) == True:
        # Microsoft Graph API endpoint to send the email
        url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"

        # Send the email
        response = requests.post(url, json=email_message, headers=headers)

        # Handle the response
        if response.status_code == 202:
            print("Email sent successfully!")
        else:
            print(f"Error sending email: {response.status_code} - {response.text}")
    else:
        print("Email not sent: User is not in the group")


# COMMAND ----------

# DBTITLE 1,Send email with attachment
def send_email_with_attachments(access_token: str, from_email: str, to_email: List[str], email_subject: str, content_type: str, content_body: str, dfs: List[DataFrame] = None, attachment_names: List[str] = None, file_paths: List[str] = None, attachment_format: str = 'xlsx'):
    # Initialize a list to store the attachments
    attachments = []
    
    # Handle PySpark DataFrames if provided
    if dfs is not None and attachment_names is not None:
        for i, df in enumerate(dfs):
            if df is not None:  # Check if the DataFrame is not None
                # Convert DataFrame to Pandas
                pandas_df = df.toPandas()
                
                if attachment_format == 'xlsx':
                    # Create an in-memory Excel file from the DataFrame
                    excel_file = BytesIO()
                    pandas_df.to_excel(excel_file, index=False, engine='openpyxl')  # Using openpyxl for Excel format
                    excel_file.seek(0)  # Reset pointer to the beginning of the BytesIO stream

                    # Encode the Excel file in base64
                    base64_file_content = base64.b64encode(excel_file.read()).decode('utf-8')

                    # Add the attachment to the list
                    attachments.append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f"{attachment_names[i]}.xlsx",
                        "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "contentBytes": base64_file_content
                    })
                elif attachment_format == 'csv':
                    # Create an in-memory CSV file from the DataFrame
                    csv_file = BytesIO()
                    pandas_df.to_csv(csv_file, index=False)  # Using pandas to write as CSV
                    csv_file.seek(0)  # Reset pointer to the beginning of the BytesIO stream

                    # Encode the CSV file in base64
                    base64_file_content = base64.b64encode(csv_file.read()).decode('utf-8')

                    # Add the attachment to the list
                    attachments.append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f"{attachment_names[i]}.csv",
                        "contentType": "text/csv",
                        "contentBytes": base64_file_content
                    })
    
    # Handle Excel file paths if provided (already in .xlsx format)
    if file_paths is not None:
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.endswith(('.xlsx', '.xls', '.csv')):
                # Read the file and encode it in base64
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    base64_file_content = base64.b64encode(file_content).decode('utf-8')

                # Get the file name from the file path
                file_name = os.path.basename(file_path)

                # Add the attachment to the list
                attachments.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": file_name,
                    "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_name.endswith('.xlsx') else "text/csv",
                    "contentBytes": base64_file_content
                })
    
    # Prepare the email message
    group_name = 'Corp_DataEng_AutomatedEmail'  # do not change
    group_id = get_group_id_from_name(access_token, group_name)
    print("Group ID:", group_id)
    
    user_id = get_user_id_from_email(access_token, from_email)
    print("User ID: ", user_id)

    # Handle multiple recipients dynamically
    to_recipients = [
        {
            "emailAddress": {
                "address": recipient
            }
        }
        for recipient in to_email  # Loop through the list of recipients
    ]
    
    email_message = {
        "message": {
            "subject": f"{email_subject}",
            "body": {
                "contentType": f"{content_type}",
                "content": f"{content_body}"
            },
            "toRecipients": to_recipients  # Add the dynamically created list of recipients
        }
    }

    # If there are attachments, add them to the email message
    if attachments:
        email_message["message"]["attachments"] = attachments

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Check if the user is in the group
    if check_user_in_group(access_token, user_id, group_id) == True:
        # Microsoft Graph API endpoint to send the email
        url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"

        # Send the email
        response = requests.post(url, json=email_message, headers=headers)

        # Handle the response
        if response.status_code == 202:
            print("Email sent successfully!")
        else:
            print(f"Error sending email: {response.status_code} - {response.text}")
    else:
        print("Email not sent: User is not in the group")


# COMMAND ----------

# DBTITLE 1,Email Format
# send_email(access_token,                  # Access token - DO NOT CHANGE
#            'DataAnalytics@80hg.io',       # From Email - DO NOT CHANGE
#             ['Email_1, 'Email_2'...],     # To Email - Changeable
#             'Subject Name',               # Subject Name - Changeable
#             'HTML/Text/',                 # Content type (HTML or Text) - Changeable
#             email_message,                # Content Body - Changeable
#             [df1, df2],                   # Dataframe Attachments converts to xlsx
#             ['Test attachment Name 1', 'Test Attachment Name 2'])     # Attachment name in order of dataframes attached


# send_email(
#     access_token=access_token,                                          #ACCESS TOKEN
#     from_email='DataAnalytics@80hg.io',                                 #FROM RECIPIENT
#     to_email=['jordan.bignell@80hg.io', 'joe.bloggs@correla.com'],      #TO RECIPIENTS 
#     email_subject='Test Subject',                                       #SUBJECT OF EMAIL
#     content_type='HTML',                                                #TYPE OF CONTENT (Text or HTML)
#     content_body='Body of Message',                                     #MESSAGE BODY
#     dfs=[df1, df2],                                                     #LIST OF DATAFRAMES
#     attachment_names=['Test Name 1', 'Test Name 2'],                    #DATAFRAME ATTACHMENTS NAMES
#     file_paths=["/path/to/excel_file.xlsx"],                            #FILE PATH LIST OF EXCEL FILE
#     attachment_format='xlsx'                                            #ATTACHMENT FORMAT
# )

############
## FORMAT ##
############
