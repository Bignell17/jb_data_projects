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

# Micrsoft Graph Method
tenant_id = fetch_key_vault_secret('sharepoint_tenant_id', 'sp-tenant-id')
client_id = fetch_key_vault_secret('sharepoint_financialreporting_client_id', 'sp-financialreporting-client-id')
client_secret = fetch_key_vault_secret('sharepoint_financialreporting_client_secret', 'sp-financialreporting-client-secret')
site_id = fetch_key_vault_secret('sharepoint_financialreporting_site_id', 'sp-financialreporting-site-id')
drive_id = fetch_key_vault_secret('sharepoint_financialreporting_drive_id', 'sp-financialreporting-drive-id')

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

file_path = "Correla/FPA/Reporting/PowerBI/Master Lookup.xlsx"
encoded_file_path = quote(file_path)

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
        sheet = wb['Vertical PL'] # wb.active  # Or wb['Sheet1']

        # Convert the sheet data to a list of lists
        data = []
        for row in sheet.iter_rows(values_only=True): #values_only to get values not cell objects
            data.append(row)

        # Create a pandas DataFrame
        df = pd.DataFrame(data[1:], columns=data[0]) #data[1:] for skipping header row
        print(df.head())
    except openpyxl.utils.exceptions.InvalidFileException as e:
        print(f"Error: Invalid Excel file format: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

else:
    print(f"Error: {response.status_code} - {response.text}")

# COMMAND ----------

spark = SparkSession.builder.appName("PandasToSpark").getOrCreate()

spark_df = spark.createDataFrame(df)

format_df = spark_df.select([F.when(F.isnan(c), None).otherwise(F.col(c)).alias(c) for c in spark_df.columns])

rename_df = format_df.select(
    "Title",
    F.col("Vertical PL Lines").alias("Vertical_PL_Lines"),
    "Active"
    )
display(rename_df)

# COMMAND ----------

load_data(rename_df, HIVE_SAP_4_HANA, "s4h_vertical_key_lookup")

# COMMAND ----------

