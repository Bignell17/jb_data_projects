# Databricks notebook source
# MAGIC %run /Workspace/Shared/BI/utilities/global_utility

# COMMAND ----------

# MAGIC %pip install pdfplumber

# COMMAND ----------

pip install requests beautifulsoup4

# COMMAND ----------

pip install openpyxl

# COMMAND ----------

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from pyspark.sql.functions import col
import pandas as pd
import openpyxl
import pdfplumber
from io import BytesIO

# COMMAND ----------

base_url = 'https://www.nationalgas.com/about-us/system-operator-incentives/nts-shrinkage'

# Send an HTTP request to the website
response = requests.get(base_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all the <a> tags and extract their href attributes
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Print the links
    for link in links:
        print(link)
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")


# COMMAND ----------

# URL of the website you want to scrape
base_url = 'https://www.nationalgas.com/about-us/system-operator-incentives/nts-shrinkage'

# to change save directory to azure storage
##############################################
# TO UPDATE TO abfss dir
save_directory = "/Workspace/Shared/BI/pipelines/adhoc/natgas_api/"

# Send an HTTP request to the website
response = requests.get(base_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Use regex to find the href that matches the pattern
    # Match any version and dynamic string in the URL
    pattern = re.compile(r"/sites/default/files/documents/NTS Shrinkage Seasonal and Quarter Forecast Gas Volumes FY\d{2}-\d{2} [A-Za-z]+ \d{2}\.pdf|/sites/default/files/documents/NTS Shrinkage Seasonal and Quarter Forecast Gas volumes FY\d{2}-\d{2} [A-Za-z]+ \d{2}\.pdf")

    # Search for the pattern in the page's HTML
    matches = re.findall(pattern, str(soup))
    for match in matches:
        print(match)

    for relative_href in matches:
    # Convert the relative href to an absolute URL
        absolute_url = urljoin(base_url, relative_href)
    
    # Now, we can download the file
        print(f"Downloading file from {absolute_url}")
    
    # Send a GET request to download the file
        file_response = requests.get(absolute_url)
    
    # Check if the file was downloaded successfully
        if file_response.status_code == 200:
            # Extract the file name from the URL
            file_name = os.path.basename(absolute_url)
            
            # Create the file path to save the file in the specified directory
            file_path = os.path.join(save_directory, file_name)
            
            # Save the file locally
            with open(file_path, 'wb') as file:
                file.write(file_response.content)
            print(f"File downloaded: {file_path}")
        else:
            print(f"Failed to download the file from {absolute_url}. Status code: {file_response.status_code}")
    else:
        print("No matches found")
else:
    print("Request failed")

# COMMAND ----------

# Initialize Spark session
spark = SparkSession.builder.appName("PDF to DataFrame Upsert").getOrCreate()

# Define the directory containing the PDFs
directory_path = '/Workspace/Shared/BI/pipelines/adhoc/natgas_api/'

# Initialize an empty list to collect data
extracted_data = []

# Loop through each file in the directory
for filename in os.listdir(directory_path):
    if filename.endswith('.pdf'):
        file_path = os.path.join(directory_path, filename)

        # Open the PDF file using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            # Loop through each page and extract tables
            for page_number, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table_number, table in enumerate(tables):
                    # Print and process each table
                    for row in table:
                        # Append all rows to extracted_data (no filtering on row length or specific columns)
                        extracted_data.append(row)  # Keep all data, even rows with missing/empty values

# Define the column names (adjust this based on your actual data structure)
columns = ['Season', 'Quarter', 'Empty1', 'Covers', 'Published', 'Value']

# Convert the extracted data into a DataFrame
df = spark.createDataFrame(extracted_data, columns)

df_selected = df.select('Season', 'Covers', 'Published', 'Value')

df_cleaned = df_selected.filter(
    (df_selected['Season'].isNotNull()) & (df_selected['Season'] != '') &
    (df_selected['Covers'].isNotNull()) & (df_selected['Covers'] != '') &
    (df_selected['Published'].isNotNull()) & (df_selected['Published'] != '') &
    (df_selected['Value'].isNotNull()) & (df_selected['Value'] != '')
)

# Filter out unclean data
df_filtered = df_cleaned[
    ~((df_cleaned['Season'] == 'Summer 2023') &
       (df_cleaned['Published'] == 'September 2023') &
       (df_cleaned['Value'] == '883 GWh')) &
    (df_cleaned['Value'].isNotNull())
]

# Drop dupes
df_dedup = df_filtered.dropDuplicates()

df_dedup.display()



# COMMAND ----------

df1 = (df_dedup.withColumn('Covers_1', split(col('Covers'), '–').getItem(0))
       .withColumn('Covers_2', split(col('Covers'), '–').getItem(1))
       .withColumn('cover_2_clean', F.regexp_replace(F.col('Covers_2'), r'[\n\r]', ''))
       .withColumn('Start_date', F.to_date(F.trim(F.concat(F.lit('01-'), F.col('Covers_1'))), 'dd-MMMM yyyy'))
       .withColumn('End_date_staging', F.to_date(F.trim(F.concat(F.lit('01-'), F.col('cover_2_clean'))), 'dd-MMMM yyyy'))
       .withColumn('End_Date', F.last_day(F.col('End_date_staging')).cast('date'))
       .withColumn('Season_Formatted', 
                   F.when(F.col('Season').rlike('^Summer'),  # If the season starts with 'Summer'
                          F.concat(F.lit('Sum '), F.col('Season').substr(-2, 2)))  # Extract last 2 characters (year) from 'Season'
                   .when(F.col('Season').rlike('^Q\d'),  # If the season starts with 'Q' (Quarter)
                         F.concat(F.col('Season').substr(0, 2), F.col('Season').substr(-2, 2)))  # Merge 'Q' and year without space
                   .when(F.col('Season').rlike('^Winter'),  # If the season starts with 'Winter'
                         F.concat(F.lit('Win '), F.split(F.col('Season'), '/')[0].substr(-2, 2)))  # Extract year before the slash
                   .otherwise(F.col('Season'))  # Keep the original season if it doesn't match any conditions
                   )
       )
display(df1)

# COMMAND ----------

upsert_data(df_final, HIVE_DATA_SCIENTIST_DB, 'ng_fbwa_shrinkage_api_raw', ['Season', 'Covers', 'Published', 'Value'])
