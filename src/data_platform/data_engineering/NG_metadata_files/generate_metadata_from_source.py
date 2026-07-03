# Databricks notebook source
import yaml
import pandas as pd
from pyspark.sql.types import StringType, StructField, StructType
import os

# COMMAND ----------

# Custom classes to enforce styles for schema and columnList
class LiteralStr(str): pass
class FoldedStr(str): pass

def create_yaml_metadata(
    source_name, 
    source_storage_location, 
    source_container, 
    source_directory_path, 
    table_name, 
    operation_mode,
    landing_file_pattern, 
    raw_file_pattern,
    raw_file_format,
    file_path,
    df,
    options=None   
):
    
    def validate_file_format(file_name):
        # Extract file extension and validate if it's supported by Autoloader
        file_extension = os.path.splitext(file_name)[1].lower().replace('.', '')
        
        # Supported file types by Databricks Autoloader
        supported_formats = {"csv", "json", "parquet", "orc", "avro", "text", "delta", "xml"}

        if file_extension in supported_formats:
            return file_extension
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats are: {', '.join(supported_formats)}")   
         
    # Detect file format
    file_name = os.path.basename(file_path)
    if raw_file_format == "delta":
        raw_file_format = raw_file_format
    else:
        raw_file_format = validate_file_format(file_name)

    # Infer the schema from the dataframe and format as a multi-line string
    schema_str = "[\n" + ",\n".join(
        f"    StructField('{field.name}', {type(field.dataType).__name__}(), {str(field.nullable)})"
        for field in df.schema.fields
    ) + "\n]\n"  # Adding an extra newline at the end

    # Create the column list as a multi-line string for better readability
    column_list = ",\n".join(field.name for field in df.schema.fields) + "\n"  # Adding an extra newline at the end

    # Construct the metadata dictionary
    metadata = {
        'sources': {
            source_name: {
                'source_storage_location': source_storage_location,
                'source_container': source_container,
                'source_directory_path': source_directory_path,
                'active': 'true',
                'tables': {
                    table_name: {
                        'table_description': '',
                        'landing_file_pattern': landing_file_pattern,
                        'remove_file': 'true',
                        'raw_file_pattern': raw_file_pattern,
                        'raw_file_format': raw_file_format,
                        'operation_mode': operation_mode,
                        'schema': LiteralStr(schema_str),  # Use LiteralStr to ensure `|` style
                        'columnList': FoldedStr(column_list),  # Use FoldedStr to ensure `>` style
                        'keys': '',
                        'sequence_by': ''
                        'z_order_column': ''
                    }
                }
            }
        }
    }

    if options:
        metadata['sources'][source_name]['tables'][table_name]['options'] = options

    # Custom representers for the YAML library
    def literal_str_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    def folded_str_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')

    # Register the representers
    yaml.add_representer(LiteralStr, literal_str_representer)
    yaml.add_representer(FoldedStr, folded_str_representer)

    # Convert the data to a YAML string with custom formatting
    yaml_string = yaml.dump(
        metadata,
        sort_keys=False,
        default_flow_style=False,
        indent=4,
        allow_unicode=True
    )

    yaml_string = yaml_string.replace('\n\n', '\n')
    
    return yaml_string

# COMMAND ----------

def generate_metadata_from_source_file(
    source_name,
    source_storage_location,
    source_container,
    source_directory_path,
    table_name,
    operation_mode,
    landing_file_pattern,
    raw_file_pattern,
    file_format,
    file_path,
    options,
    dry_run
):

    if options == "":
        options = None

    metadata_file_path = f"table_metadata_files/{source_name}/{source_name}_{table_name}.yaml"

    if options:
        df = (spark.read.format(file_format)
            .options(**options)
            .load(file_path)
        )
    else:
        df = (spark.read.format(file_format)
            .load(file_path)
        )

    # Create the directory if it doesn't exist
    directory = os.path.dirname(metadata_file_path)
    os.makedirs(directory, exist_ok=True)

    yaml_string = create_yaml_metadata(
        source_name=source_name,
        source_storage_location=source_storage_location,
        source_container=source_container,
        source_directory_path=source_directory_path,
        table_name=table_name,
        operation_mode=operation_mode,
        landing_file_pattern=landing_file_pattern,
        raw_file_pattern=raw_file_pattern,
        raw_file_format=file_format,
        file_path=file_path,
        options=options,
        df=df
    )

    if dry_run:
        print(f"Dry run for `{metadata_file_path}`:")
        print(yaml_string)
    else:
        with open(metadata_file_path, "w+") as file:
            file.write(yaml_string) 
        print(f"Created `{metadata_file_path}`")
