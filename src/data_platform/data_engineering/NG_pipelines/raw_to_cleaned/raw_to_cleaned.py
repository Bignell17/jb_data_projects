# Databricks notebook source
from pyspark.sql.functions import expr, current_timestamp, substring_index, regexp_replace, input_file_name, col, first, year, month, dayofmonth, date_format, lit
from pyspark.sql.types import *
import requests
import json
from pyspark.sql.streaming import StreamingQueryListener
import os
import time
from pyspark.sql import Row
import uuid
import pandas as pd

# COMMAND ----------

# MAGIC %run /Workspace/data_engineering/utilities/common

# COMMAND ----------

# MAGIC %run /Workspace/data_engineering/utilities/raw_to_cleaned

# COMMAND ----------

environment = spark.conf.get('environment')
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
cluster_id = spark.conf.get("spark.databricks.clusterUsageTags.clusterId")        
current_directory = os.getcwd()

## Data comes from current iteration of workflow task
dbutils.widgets.text("source_name", "x")
dbutils.widgets.text("table_name", "x")

sourceName = dbutils.widgets.get("source_name")
tableName = dbutils.widgets.get("table_name")

print(sourceName)
print(tableName)

# COMMAND ----------

destination_path = get_external_location_path('cleaned')
print(destination_path)

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

dfPivot = dfPipelineMetaData.groupBy('SourceName','TableName').pivot('KeyName').agg(first("Value"))
pandas_df = dfPivot.toPandas()

# COMMAND ----------

# Attach the listener
raw_to_cleaned_listener = CustomStreamingQueryListener()
spark.streams.addListener(raw_to_cleaned_listener)

# COMMAND ----------

# DBTITLE 1,Raw to Cleaned
for index, row in pandas_df.iterrows():
    sourceName  = row.get('SourceName').lower()
    tableName   = row['TableName']
    schema      = row['schema']
    columnList  = [column.strip() for column in row['columnList'].split(',')]
    keys        = row['keys']
    sequence_by  = row['sequence_by']
    z_order_column  = row.get('z_order_column') 
    raw_file_format  = row['raw_file_format']
    raw_file_pattern = row['raw_file_pattern']
    source_storage_location  = row['source_storage_location']
    source_container  = row['source_container']
    source_directory_path  = row['source_directory_path']
    operation_mode  = row['operation_mode']
    table_description = row['table_description']
    transformation_notebooks = row.get('transformation_notebooks')    
    options = row.get('options')

    print(f"sourceName: {sourceName}")
    print(f"tableName: {tableName}")
    print(f"schema: {schema}")
    print(f"columnList: {columnList}")
    print(f"keys: {keys}")
    print(f"z_order_column: {z_order_column}")
    print(f"sequence_by: {sequence_by}")
    print(f"raw_file_format: {raw_file_format}")
    print(f"raw_file_pattern: {raw_file_pattern}")
    print(f"source_storage_location: {source_storage_location}")
    print(f"source_container: {source_container}")
    print(f"source_directory_path: {source_directory_path}")
    print(f"operation_mode: {operation_mode}")
    print(f"table_description: {table_description}")
    print(f"transformation_notebooks: {transformation_notebooks}")
    print(f"options: {options}")

    if transformation_notebooks is None:
        ## If there are no transformation notebooks then process as per metadata
        print(f"Completing simple transformations for `{sourceName}_{tableName}` ")
                          
        # Supports excel files using pandas.read_excel()
        # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_excel.html
        if raw_file_format.startswith("xls"):

            df, checkpointPath = get_source(
                sourceName=sourceName, 
                tableName=tableName,
                file_pattern=raw_file_pattern,
                file_format=raw_file_format
            )

            # Select necessary columns and limit the size of the DataFrame
            df = df.select("sys_file_path")
            #display(df)
                    
            (df.writeStream
                .foreachBatch(batch_read_excel_files(
                    directoryPath=sourceName, 
                    tableName=f"{sourceName}_{tableName}", 
                    operation_mode=operation_mode, 
                    keys=keys,
                    schema=schema,
                    container='cleaned', 
                    table_schema='cleaned', 
                    comment=table_description,
                    options=options,
                    metadata=pandas_df
                )) 
                .option("checkpointLocation", checkpointPath)
                .trigger(availableNow=True)
                .start()
                .awaitTermination()
            )
            
        else:

            df, checkpointPath = load_source(
                sourceName=sourceName, 
                tableName=tableName, 
                schema=schema, 
                options=options,
                file_pattern=raw_file_pattern, 
                file_format=raw_file_format, 
                columnList=columnList
            )
            
            (df.writeStream
                .foreachBatch(batch_write_to_delta(
                    directoryPath=sourceName, 
                    tableName=f"{sourceName}_{tableName}", 
                    operation_mode=operation_mode, 
                    keys=keys, 
                    container='cleaned', 
                    table_schema='cleaned', 
                    comment=table_description,
                    metadata=pandas_df
                )) 
                .option("checkpointLocation", checkpointPath)
                .trigger(availableNow=True)
                .start()
                .awaitTermination()
            )
    else:
        # If transformation notebooks are present then use them instead of metadata
        print(f"Transformation notebooks detected for `{sourceName}_{tableName}` completing complex transformations")

        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().getOrElse(None)

        if raw_file_format != "delta":

            df, checkpointPath = get_source(
                sourceName=sourceName, 
                tableName=tableName, 
                file_pattern=raw_file_pattern,
                file_format=raw_file_format
            )

            # Select necessary columns and limit the size of the DataFrame
            df = df.select("sys_file_path")

            # Start the streaming query with the batch processing
            (df.writeStream
                .foreachBatch(lambda df, epochId: batch_run_transformation_notebook(
                    source_name=sourceName, 
                    table_name=f"{sourceName}_{tableName}",
                    transformation_notebooks=transformation_notebooks,
                    schema=schema,
                    column_list=columnList,
                    operation_mode=operation_mode,
                    options=options,
                    token=token
                )(df, epochId))
                .option("checkpointLocation", checkpointPath)
                .trigger(availableNow=True)
                .start()
                .awaitTermination()
            )
    
        else:
            
            #delta files do not need to be processed using autoloader, and history is kept within the delta metadata so processing is done separately
            sourceDataPath = f"/Volumes/di_{environment}/raw/raw_files/{sourceName}/{tableName}{raw_file_pattern}"
            df = spark.createDataFrame([(sourceDataPath,)], ["sys_file_path"])

            process_batch(
                batch_df=df, 
                batch_id=str(uuid.uuid4()), 
                source_name=sourceName, 
                table_name=f"{sourceName}_{tableName}", 
                transformation_notebooks=transformation_notebooks, 
                schema=schema, 
                column_list=columnList, 
                operation_mode=operation_mode, 
                options=options, 
                workspace_url=workspace_url, 
                token=token
                )

# COMMAND ----------

# DBTITLE 1,CTAS
transformations = check_for_transformations(df=pandas_df, type='ctas')
sourceName = transformations['sourceName']
tableName = transformations['tableName']
ctas_table_name = transformations['ctas_table_name']
filter_language = transformations['filter_language']
filter_logic = transformations['filter_logic']
calculated_column_json = transformations['calculated_column_json']

if filter_logic is not None or (calculated_column_json and len(calculated_column_json) > 0):
    
    print(f"Simple transformations detected for `{sourceName}_{tableName}`")
    # Apply specified transformations
    ctas_transformations(
        source_name  = sourceName, 
        table_name = tableName, 
        ctas_table_name = ctas_table_name, 
        filter_language = filter_language, 
        filter_logic = filter_logic, 
        calculated_column_json = calculated_column_json)
else:
    print(f"No transformations detected for `{sourceName}_{tableName}`")

# COMMAND ----------

# DBTITLE 1,Table optimization
for index, row in pandas_df.iterrows():
    container   = 'cleaned'
    sourceName  = row.get('SourceName').lower()
    tableName   = row['TableName']
    keys        = row['keys']
    z_order_column  = row.get('z_order_column') 

    optimize_table(container, sourceName, tableName, keys, z_order_columns=z_order_column)
