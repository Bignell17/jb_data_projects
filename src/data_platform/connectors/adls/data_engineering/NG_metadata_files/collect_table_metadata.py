# Databricks notebook source
# MAGIC %run /Workspace/data_engineering/utilities/common

# COMMAND ----------

import yaml 
import os
from pyspark.sql.types import *
from delta.tables import *
import os
import json
import csv
from io import StringIO

# COMMAND ----------

spark.conf.set("spark.databricks.delta.properties.defaults.autoOptimize.optimizeWrite", "true")
spark.conf.set("spark.databricks.delta.properties.defaults.autoOptimize.autoCompact", "true")

# COMMAND ----------

environment = spark.conf.get('environment')

# COMMAND ----------

# get the external location path based on container name
destination_path = get_external_location_path('metadata')
print(destination_path)

# COMMAND ----------

query = f"""
    CREATE TABLE IF NOT EXISTS di_{environment}.metadata.table_metadata
    (
            SourceName string,
            TableName string,
            KeyName string,
            Value string
    )
    USING DELTA
    LOCATION '{destination_path}table_metadata'    
"""
#print(query)
spark.sql(query)

# COMMAND ----------

# Function to loop through all sources and extract details
def extract_metadata(d):
    table_details = []
    notebook_names = []

    for source_key, source_value in d.get('sources', {}).items():
        print(f"Processing source: {source_key}")  # Debugging: Show current source

        # Extract fields from the source level
        source_storage_location = source_value.get('source_storage_location', None)
        source_container = source_value.get('source_container', None)
        source_directory_path = source_value.get('source_directory_path', None)
        active = source_value.get('active', None)
        allow_same_filename = source_value.get('allow_same_filename', 'false')

        tables = source_value.get('tables', {})  # Get the tables dictionary
        for table_key, table_value in tables.items():
            print(f"Processing table: {table_key}")  # Debugging: Show current table
            if isinstance(table_value, dict):
                # Use the table_key as the table_name
                table_name = table_key

                # Process all the table details
                for key in [
                    'schema', 'columnList', 'keys', 'sequence_by', 'has_headers', 
                    'landing_file_pattern', 'raw_file_pattern', 'raw_file_format', 
                    'operation_mode', 'table_description','filter_logic','filter_language',
                    'remove_file', 'z_order_columns'
                ]:
                    if key in table_value:
                        table_details.append({
                            'SourceName': source_key,
                            'TableName': table_name,
                            'KeyName': key,
                            'Value': table_value[key]
                        })

                # Add source-level details
                for key, value in [
                    ('source_storage_location', source_storage_location),
                    ('source_container', source_container),
                    ('source_directory_path', source_directory_path),
                    ('active', active),
                    ('allow_same_filename', allow_same_filename)
                ]:
                    table_details.append({
                        'SourceName': source_key,
                        'TableName': table_name,
                        'KeyName': key,
                        'Value': value
                    })

                # Add options as a dictionary
                if 'options' in table_value:
                    options = table_value['options']
                    # Convert options dictionary to a JSON string for storage
                    options_json = json.dumps(options, indent=4)
                    table_details.append({
                        'SourceName': source_key,
                        'TableName': table_name,
                        'KeyName': 'options',
                        'Value': options_json  # Store as JSON string
                    })
                    
                # Add validation as a dictionary
                if 'validation' in table_value:
                    validation = table_value['validation']
                    # Convert validation dictionary to a JSON string for storage
                    validation_json = json.dumps(validation, indent=4)
                    table_details.append({
                        'SourceName': source_key,
                        'TableName': table_name,
                        'KeyName': 'validation',
                        'Value': validation_json  # Store as JSON string
                    })    

                # Transformation Notebooks
                if 'transformation_notebooks' in table_value:
                    notebooks = table_value['transformation_notebooks']
                    
                    # Convert list of notebook names to a CSV string
                    notebooks_csv = ', '.join(notebooks)
                    
                    table_details.append({
                        'SourceName': source_key,
                        'TableName': table_name,
                        'KeyName': 'transformation_notebooks',
                        'Value': notebooks_csv  # Store as CSV string
                    })

                # Process calculated columns if available
                calculated_columns = table_value.get('calculated_columns', {})
                for column_key, column_value in calculated_columns.items():
                    column_metadata = {
                        'language': column_value.get('column_language'),
                        'logic': column_value.get('column_logic'),
                        'description': column_value.get('column_description')
                    }
                    column_metadata = {k: v for k, v in column_metadata.items() if v is not None}
                    if column_metadata:
                        table_details.append({
                            'SourceName': source_key,
                            'TableName': table_name,
                            'KeyName': f"calculated_column_{column_key}",
                            'Value': json.dumps(column_metadata, indent=4)  # Store as JSON string
                        })

                # Process calculated columns if available
                ctas = table_value.get('ctas', {})
                if ctas is not None and len(ctas) > 1:
                    raise ValueError(f"CTAS definition contains more than one entry for `{source_key}` and `{table_name}`")
                elif ctas is not None and len(ctas) == 1:
                    ctas_table_name = next(iter(ctas))

                    table_details.append({
                        'SourceName': source_key,
                        'TableName': table_name,
                        'KeyName': 'ctas_table_name',
                        'Value': ctas_table_name
                    })       

                    # Get filter logic if it exists
                    for key in [
                        'filter_logic','filter_language'
                    ]:
                        if key in ctas.get(ctas_table_name, {}):
                            table_details.append({
                                'SourceName': source_key,
                                'TableName': table_name,
                                'KeyName': f'ctas_{key}',
                                'Value': ctas.get(ctas_table_name, {}).get(key)
                            })                    

                    # Get calculated columns if the exist
                    calculated_columns = ctas.get(ctas_table_name, {}).get('calculated_columns')
                    if calculated_columns:
                        for column_key, column_value in calculated_columns.items():
                            column_metadata = {
                                'language': column_value.get('column_language'),
                                'logic': column_value.get('column_logic'),
                                'description': column_value.get('column_description')
                            }
                            column_metadata = {k: v for k, v in column_metadata.items() if v is not None}
                            if column_metadata:
                                table_details.append({
                                    'SourceName': source_key,
                                    'TableName': table_name,
                                    'KeyName': f"ctas_calculated_column_{column_key}",
                                    'Value': json.dumps(column_metadata, indent=4)  # Store as JSON string
                                })

            else:
                print(f"Skipping table {table_key} as it does not contain the expected structure.")

    return table_details

# COMMAND ----------

def list_files_in_directory(directory_path):
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d != 'example']  # Ignore 'example' folder
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

# COMMAND ----------

def upsert_metadata(table_details_list):
    # Convert the extracted details into a list of tuples for Spark DataFrame
    if table_details_list:
        data_list = [(item['SourceName'], item['TableName'], item['KeyName'], item['Value']) 
                    for item in table_details_list]

        # Create the final Spark DataFrame
        spark_df = spark.createDataFrame(data_list, ['SourceName', 'TableName', 'KeyName', 'Value'])

        # Define the target table
        delta_table = DeltaTable.forName(spark, f"di_{environment}.metadata.table_metadata")
        
        # Perform the merge
        delta_table.alias("target").merge(
            source=spark_df.alias("source"),
            condition="""
                target.SourceName = source.SourceName AND 
                target.TableName = source.TableName AND 
                target.KeyName = source.KeyName
            """ 
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).execute()

        print("Data successfully upserted into the Unity Catalog table.")

    else:
        
        print("No data was extracted. Please check the YAML structure and extraction logic.")    

# COMMAND ----------

# DBTITLE 1,Process Ingestion Metadata

current_directory = os.getcwd()
file_path = f"{current_directory}/table_metadata_files/"
metadata_files = list_files_in_directory(file_path)

metadata_list = []

for metadata_file in metadata_files:
    with open(metadata_file, 'r') as file:
        metadata = yaml.safe_load(file)

    table_details_list = [{**detail, 'TableName': str(detail.get('TableName', ''))} for detail in extract_metadata(metadata)]
    metadata_list.extend(table_details_list) 

display(metadata_list)
upsert_metadata(metadata_list)
