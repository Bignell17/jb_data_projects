# Databricks notebook source
# MAGIC %run /Workspace/data_engineering/metadata/generate_metadata_from_source

# COMMAND ----------

dry_run = False
data = [
    {
        "file_path": "/Volumes/di_dev/landing/gso-external/Joule/joule_mar_product_date/mar_product_date.csv",    
        "source_name": "joule",
        "table_name": "mar_product_date",
        "source_storage_location": "dlz",
        "source_container": "gso-external",
        "source_directory_path": "Joule/joule_mar_product_date/",
        "landing_file_pattern": "mar_product_date.csv",
        "raw_file_pattern": "mar_product_date.csv",
        "file_format": "csv",
        "options": {"inferSchema" :"true", "header": "true", "delimiter": ","},
        "operation_mode": "overwrite"
    }
]

# COMMAND ----------

df = spark.createDataFrame(data)
display(df)

# COMMAND ----------


for row in df.collect():
    generate_metadata_from_source_file(
        source_name=row['source_name'],
        table_name=row['table_name'].lower(),
        source_storage_location=row['source_storage_location'],
        source_container=row['source_container'],
        source_directory_path=row['source_directory_path'],
        landing_file_pattern=row['landing_file_pattern'],
        raw_file_pattern=row['raw_file_pattern'],
        file_format=row['file_format'],
        operation_mode=row['operation_mode'],
        file_path=row['file_path'],
        options=row['options'],
        dry_run=dry_run
    )
