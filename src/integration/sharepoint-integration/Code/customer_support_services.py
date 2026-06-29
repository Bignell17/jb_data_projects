# Databricks notebook source
#install pip libraries onto cluster

# COMMAND ----------

pip install Office365-REST-Python-Client

# COMMAND ----------

pip install openpyxl

# COMMAND ----------

pip install requests msal

# COMMAND ----------

pip install requests_oauthlib

# COMMAND ----------

# MAGIC %run /Workspace/Shared/BI/utilities/global_utility

# COMMAND ----------

from urllib import response
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.files.file import File
import urllib
import os
import pandas as pd
import openpyxl
from io import StringIO, BytesIO
import msal
from msal import ConfidentialClientApplication
import requests
import json
import logging
from io import StringIO
from urllib.parse import quote

# COMMAND ----------

tenant_id = fetch_key_vault_secret('sharepoint_tenant_id', 'sp-tenant-id')
client_id = fetch_key_vault_secret('sharepoint_customersupportservices_client_id', 'sp-custsuppserv-client-id')
client_secret = fetch_key_vault_secret('sharepoint_customersupportservices_client_secret', 'sp-custsuppserv-client-secret')
site_id = fetch_key_vault_secret('sharepoint_customersupportservices_site_id', 'sp-custsuppserv-site-id')
drive_id = fetch_key_vault_secret('sharepoint_customersupportservices_drive_id', 'sp-custsuppserv-drive-id')

# Define the scope for Microsoft Graph API
scope = ["https://graph.microsoft.com/.default"]

# Create a confidential client application for authentication
app = msal.ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=f"https://login.microsoftonline.com/{tenant_id}" )

# Get the token
result = app.acquire_token_for_client(scopes=scope)
if 'access_token' in result:
    access_token = result['access_token']
    print("Success: Access Token obtained")
else:
    print("Error obtaining access token:", result.get("error_description"))

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
# print(result)

# file_path = 'Business Intelligence Team/Data Engineering/test/gl_key.csv'
file_path = 'Business Intelligence Team/Data Engineering/test/wbs_lookup.xlsx'
encoded_file_path = quote(file_path)
# print(encoded_file_path)
# Construct the API URL using the encoded file path
url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_file_path}:/content"

# Request to download the file
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Assuming it's a CSV file, you can read it as follows:

    # Convert the response content into a CSV using pandas
    # csv_data = StringIO(response.text)
    # df = pd.read_excel(csv_data, openpyxl=True)
    
    try:
        # Load the workbook from the response content (binary data)
        wb = openpyxl.load_workbook(filename=BytesIO(response.content))

        # Select the active worksheet (or specify by name)
        sheet = wb.active  # Or wb['Sheet1']

        # Convert the sheet data to a list of lists
        data = []
        for row in sheet.iter_rows(values_only=True): #values_only to get values not cell objects
            data.append(row)

        df = pd.DataFrame(data[1:], columns=data[0]) #data[1:] for skipping header row
        print(df.head())
    except openpyxl.utils.exceptions.InvalidFileException as e:
        print(f"Error: Invalid Excel file format: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    
    # # Now, you can work with the dataframe
    # print(df.head())
else:
    print(f"Error: {response.status_code} - {response.text}")

# COMMAND ----------

df.head(20)

# COMMAND ----------

import jwt

# Assuming `access_token` is the token you've acquired
decoded_token = jwt.decode(access_token, options={"verify_signature": False})

# Print the claims (you can inspect the `scp` claim)
print(json.dumps(decoded_token, indent=4))


# COMMAND ----------

response.json()

# COMMAND ----------

# Initial and target values
initial_value = 2.9565217391304347826086956521739
target_value = 100881

# Calculate the scaling factor
scaling_factor = target_value / initial_value

# Print the scaling factor
print(f"Scaling factor: {scaling_factor}")
