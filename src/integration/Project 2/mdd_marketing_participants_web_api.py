# Databricks notebook source
# MAGIC %run /Workspace/Shared/BI/utilities/global_utility

# COMMAND ----------

# MAGIC %run /Workspace/Shared/BI/utilities/constants

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
import pandas as pd
import openpyxl

# COMMAND ----------

# URL of the website you want to scrape
url = 'https://www.xoserve.com/products-services/market-participant-data/market-domain-data-mdd/'

# Send an HTTP request to the website
response = requests.get(url)

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

import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Start a Spark session
spark = SparkSession.builder.appName('DownloadAndLoadData').getOrCreate()

# Base URL of the website (e.g., the domain)
base_url = 'https://www.xoserve.com/products-services/market-participant-data/market-domain-data-mdd/'

# Send an HTTP request to the website
response = requests.get(base_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Use regular expression to find the href that matches the pattern
    # Match any version and dynamic string in the URL
    pattern = r'href="(/media/[\w-]+/mdd-market-participants-xos-[\w-]+\.xlsx)"'
    
    # Search for the pattern in the page's HTML
    matches = re.findall(pattern, str(soup))
    
    if matches:
        # If there are multiple matches, get the first one (or modify logic to handle multiple)
        relative_href = matches[0]
        
        # Convert the relative href to an absolute URL
        absolute_url = urljoin(base_url, relative_href)
        
        # Now, we can download the file
        print(f"Downloading file from {absolute_url}")
        
        # Send a GET request to download the file
        file_response = requests.get(absolute_url)
        
        # Check if the file was downloaded successfully
        if file_response.status_code == 200:
            # Save the file locally
            file_name = os.path.basename(absolute_url)  # Extract the file name from the URL
            file_path = os.path.join("/Workspace/Shared/BI/pipelines/mdd_market_participants/00_api", file_name)  # Save in a fixed directory
            
            with open(file_path, 'wb') as file:
                file.write(file_response.content)
            print(f"File downloaded: {file_path}")
            
            # Load the downloaded file into a PySpark DataFrame
            if file_name.endswith('.xlsx'):
                # Use pandas to read the Excel file
                pandas_df = pd.read_excel(file_path, sheet_name='Market Participants', usecols="A:R", nrows=600)

                # Ensure proper types in pandas before converting to PySpark
                pandas_df['Org ID'] = pandas_df['Org ID'].astype(float)  # Ensuring 'Org ID' is float
                pandas_df['MDD Release Effective Date'] = pd.to_datetime(pandas_df['MDD Release Effective Date'], errors='coerce')  # Convert to datetime
                pandas_df['UKL Closure Date'] = pd.to_datetime(pandas_df['UKL Closure Date'], errors='coerce')  # Convert to datetime

                # Define schema for PySpark DataFrame
                schema = StructType([
                    StructField("Org_Name", StringType(), True),
                    StructField("Company_Number", StringType(), True),
                    StructField("Org_ID", DoubleType(), True),
                    StructField("Short_code", StringType(), True),
                    StructField("Live_Closed", StringType(), True),
                    StructField("MDD_Release_Effective_Date", TimestampType(), True),
                    StructField("UKL_Go_Live_Date", StringType(), True),
                    StructField("UKL_Closure_Date", TimestampType(), True),
                    StructField("Industry_End_Date", StringType(), True),
                    StructField("Shipper", StringType(), True),
                    StructField("Trader", DoubleType(), True),
                    StructField("Supplier", StringType(), True),
                    StructField("MAM", StringType(), True),
                    StructField("MAP", StringType(), True),
                    StructField("SMSO", StringType(), True),
                    StructField("Network_Operator", StringType(), True),
                    StructField("IGT", StringType(), True),
                    StructField("ASP", StringType(), True)
                ])

                # Convert the pandas DataFrame to a PySpark DataFrame with the defined schema
                spark_df = spark.createDataFrame(pandas_df, schema=schema)

            else:
                print("The downloaded file is not in a supported format for loading into PySpark.")
        else:
            print(f"Failed to download the file. Status code: {file_response.status_code}")
    else:
        print("Could not find any valid links matching the pattern.")
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")


# COMMAND ----------

display(spark_df)

# COMMAND ----------

load_data(spark_df, HIVE_DATA_SCIENTIST_DB, "mdd_market_participants_raw", merge_schema=True)
