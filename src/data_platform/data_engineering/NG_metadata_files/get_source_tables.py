# Databricks notebook source
dbutils.widgets.text("source_name", "x")
dbutils.widgets.text("table_name", "x") # table name can be provided if we need select specific tabels

source_name = dbutils.widgets.get("source_name")
table_name = dbutils.widgets.get("table_name")

print(f"source_name: {source_name}")
print(f"table_name: {table_name}")

# COMMAND ----------

environment = spark.conf.get('environment')
catalog_name = f"di_{environment}"

# COMMAND ----------

where_clause = f"meta.SourceName = '{source_name}'"
if table_name not in ['x','','null',None,'None']:
    table_list = ", ".join([f"'{table.strip()}'" for table in table_name.split(',')])
    where_clause += f" AND meta.TableName IN ({table_list})"

sql = (f"""
WITH cte_active AS (
    SELECT DISTINCT SourceName, TableName FROM `{catalog_name}`.`metadata`.`table_metadata`  
    WHERE lower(KeyName) = 'active' AND lower(Value) = 'true'
)       
SELECT DISTINCT
    cte.SourceName,
    cte.TableName
FROM {catalog_name}.metadata.table_metadata meta
INNER JOIN cte_active cte ON  cte.SourceName = meta.SourceName AND cte.TableName = meta.TableName
WHERE {where_clause}
""")

#print(sql)
df = spark.sql(sql)
json_value = df.toPandas().to_json(orient='records')

#print(sql)
df = spark.sql(sql)
json_value = df.toPandas().to_json(orient='records')

# COMMAND ----------

json_value

# COMMAND ----------

dbutils.jobs.taskValues.set(key="sources", value=json_value)
