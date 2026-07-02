# Databricks notebook source
import os
import json
import zipfile
import shutil
import uuid
import io
import logging
from datetime import datetime
import urllib.parse

from pyspark.sql import functions as F
from pyspark.sql.functions import (
    expr,
    current_timestamp,
    substring_index,
    regexp_replace,
    input_file_name,
    col,
    first,
    year,
    month,
    dayofmonth,
    date_format,
    lit
)
from pyspark.sql.types import *


# COMMAND ----------

environment = spark.conf.get('environment')

## Data comes from current iteration of workflow task
dbutils.widgets.text("source_name", "x")
dbutils.widgets.text("table_name", "x")
sourceName = dbutils.widgets.get("source_name")
tableName = dbutils.widgets.get("table_name")

print(sourceName)
print(tableName)

# COMMAND ----------

spark.conf.set("spark.sql.files.ignoreMissingFiles", "true")
spark.conf.set("spark.sql.shuffle.partitions", "200")

# COMMAND ----------

def load_source(sourceName, tableName, file_pattern, source_directory_path, source_storage_location, source_container, allowSameFilename):

        # Modify the file pattern to escape special characters
        print(f"file_pattern: {file_pattern}")
        
        raw_file_pattern = file_pattern
        filter_file_pattern = file_pattern.replace("*", "%")
        
        # Overwrite the behaviour to process files with same name in every execution
        allowOverwrites = allowSameFilename
        
        raw_file_pattern = urllib.parse.quote(raw_file_pattern, safe="%*")  # Encodes pattern to allow special characters        
        filter_file_pattern = urllib.parse.quote(filter_file_pattern, safe="%*")  # Encodes pattern to allow special characters        

        # Define the source and destination paths
        sourceFolderPath = f"/Volumes/di_{environment}/landing/{source_container}/{source_directory_path}"
        sourceDataPath = f"{sourceFolderPath}/{raw_file_pattern}"
        destinationDataPath = f"/Volumes/di_{environment}/raw/raw_files/{sourceName}/{tableName}"
        checkpointPath = f"/Volumes/di_{environment}/metadata/checkpoints/raw/{sourceName}/{tableName}"
        sourceDataPath = urllib.parse.unquote(sourceDataPath)

        if not os.path.exists(sourceFolderPath):
            raise FileNotFoundError(f"Source data path does not exist: {sourceFolderPath}")

        print(f"sourceFolderPath: {sourceFolderPath}")
        print(f"sourceDataPath: {sourceDataPath}")
        print(f"destinationDataPath: {destinationDataPath}")
        print(f"checkpointPath: {checkpointPath}")
        print(f"raw_file_pattern: {raw_file_pattern}")
        print(f"filter_file_pattern: {filter_file_pattern}")

        # copies file detected by autoloader as a binary file
        df = (spark.readStream
                .format("cloudFiles")
                .option("cloudFiles.format", "binaryFile") 
                .option("cloudFiles.includeExistingFiles", "true")
                .option("cloudFiles.allowOverwrites", allowOverwrites)
                .option("cloudFiles.maxFilesPerTrigger", 1)
                .load(sourceDataPath)
                .filter(f"_metadata['file_name'] like '{filter_file_pattern}'")
                )        
         
        # Add derived columns for file metadata
        df = (df.selectExpr("*", "_metadata['file_name'] as sys_source_file", "_metadata['file_path'] as sys_file_path")
                .withColumn("sys_window_path", 
                        regexp_replace(
                                substring_index(substring_index("sys_source_file", "/", -6), "/", 5), 
                                r'[A-z]*=', '')  # Adjust regex pattern if needed
                )
                .withColumn("sys_insert_time_utc", current_timestamp())
        )
        
        return df, destinationDataPath, checkpointPath

# COMMAND ----------

# DBTITLE 1,Copy and Unzip Files with Structured Timestamps
def copy_file(batch_df, batch_id, destination_path, remove_file):
    
    files = batch_df.select("path", "modificationTime").distinct().collect()

    for file in files:
        raw_file_path = file["path"]
        raw_file_path = urllib.parse.unquote(raw_file_path)
        local_file_path = raw_file_path.replace("dbfs:/", "/")  # Convert to local path
        file_name = local_file_path.split("/")[-1]  # Extract the file name from the full path
        print(f"raw_file_path: {raw_file_path}")

        # Get the file's modification time 
        modified_time_dt = file["modificationTime"]

        # Extract year, month, day, etc. from the modification time
        year = modified_time_dt.year
        month = f"{modified_time_dt.month:02d}"  
        day = f"{modified_time_dt.day:02d}"      
        hour = f"{modified_time_dt.hour:02d}"    
        minute = f"{modified_time_dt.minute:02d}"
        second = f"{modified_time_dt.second:02d}"

        # Step 2: Copy the file to the destination using shutil
        final_target_dir = f"{destination_path}/{year}/{month}/{day}/{year}{month}{day}_{hour}{minute}{second}"
        final_target_path = f"{final_target_dir}/{file_name}"
        print(f"final_target_path: {final_target_path}")

        # Ensure the final destination directory exists (create if doesn't exist)
        if not os.path.exists(final_target_dir):
            os.makedirs(final_target_dir)

        # Use shutil to copy the file from DBFS to the final destination
        shutil.copy2(local_file_path, final_target_path)
        print(f"Copied from {raw_file_path} to {final_target_path}")

        # unzip the file if it is a .zip
        if file_name.endswith(".zip"):
            zipfile.ZipFile(final_target_path).extractall(f"{final_target_dir}/uncompressed")
            print(f"Unzipped `{final_target_path}` to `{final_target_dir}/uncompressed`")
                                                      
        if remove_file in ['true','True', True]:
            # if True then remove the file from landing
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
                print(f"Removed file: `{local_file_path}`")
            else:
                print(f"File does not exist: `{local_file_path}`")        

# COMMAND ----------

CHUNK_SIZE = 1000  # Adjust as necessary

# COMMAND ----------

# DBTITLE 1,Batch Processing Copy of Zip Files in Python
def batch_copy_files(destination_path, remove_file):
    def process_batch(batch_df, batch_id):
        batch_df.printSchema()

        # Get the total number of rows in the batch DataFrame
        total_rows = batch_df.count()
        
        # Process the batch in chunks
        for offset in range(0, total_rows, CHUNK_SIZE):
            # Create a chunk of the DataFrame
            chunk_df = batch_df.limit(CHUNK_SIZE).offset(offset)  # Using offset to get the chunk
            copy_file(chunk_df, batch_id, destination_path, remove_file)

    return process_batch

# COMMAND ----------

dfPipelineMetaData = spark.sql(f"""
    WITH cte_active AS (
    SELECT DISTINCT SourceName, TableName FROM `di_{environment}`.`metadata`.`table_metadata`  
    WHERE lower(KeyName) = 'active' AND lower(Value) = 'true'
    )
    SELECT meta.SourceName, meta.TableName, meta.KeyName, meta.Value
    FROM `di_{environment}`.`metadata`.`table_metadata` meta
    INNER JOIN cte_active cte ON  cte.SourceName = meta.SourceName AND cte.TableName = meta.TableName
    WHERE cte.SourceName = '{sourceName}' AND cte.TableName = '{tableName}'
  """)

# COMMAND ----------

dfPivot = dfPipelineMetaData.groupBy('SourceName', 'TableName').pivot('KeyName').agg(first("Value"))
pandas_df = dfPivot.toPandas()

# COMMAND ----------

for index, row in pandas_df.iterrows():
    sourceName = row['SourceName'].lower()
    tableName = row['TableName']
    landing_file_pattern = row['landing_file_pattern']
    source_storage_location = row['source_storage_location']
    source_container = row['source_container']
    source_directory_path = row['source_directory_path'].rstrip('/')
    remove_file = row.get('remove_file', 'true') # if remove file attribute is not present in metadata, default to true
    allow_same_filename = row['allow_same_filename']
    
    print(f"sourceName: {sourceName}")
    print(f"tableName: {tableName}")
    print(f"landing_file_pattern: {landing_file_pattern}")
    print(f"source_storage_location: {source_storage_location}")
    print(f"source_container: {source_container}")
    print(f"source_directory_path: {source_directory_path}")
    print(f"remove_file: {remove_file}")
    print(f"allowSameFilename: {allow_same_filename}")

    logging.info(f"Processing source: {sourceName}, table: {tableName}")

    df, destinationDataPath, checkpointPath = load_source(
        sourceName=sourceName, 
        tableName=tableName, 
        file_pattern=landing_file_pattern,
        source_storage_location=source_storage_location, 
        source_container=source_container, 
        source_directory_path=source_directory_path,
        allowSameFilename=allow_same_filename,
    )

    # Select necessary columns and limit the size of the DataFrame
    df = df.select("path", "modificationTime", "length")
    #display(df)
    
    # Start the streaming query with the batch processing
    (df.writeStream
        .foreachBatch(lambda df, epochId: batch_copy_files(destinationDataPath, remove_file)(df, epochId)) 
        .option("checkpointLocation", checkpointPath)
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )
