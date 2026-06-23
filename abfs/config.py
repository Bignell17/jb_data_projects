# pip install pandas pyarrow azure-identity azure-storage-blob
# pip install azure-storage-file-datalake

from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import pandas as pd
import io

# Authenticate
tenant_id = "Stored in Notepad Temporarily" # Find way to store securely and then read securely
client_id = "Stored in Notepad Temporarily" # Find way to store securely and then read securely
client_secret = "Stored in Notepad Temporarily" # Find way to store securely and then read securely
account_name = "jtbstorage001"

credential = ClientSecretCredential(tenant_id, client_id, client_secret)

service_client = DataLakeServiceClient(
    account_url=f"https://{account_name}.dfs.core.windows.net",
    credential=credential
)



#Upload data to ABFS
file_system = service_client.get_file_system_client("jb-test-container")
file_client = file_system.get_file_client("api_data/data.json")

data = '{"name": "Alice", "id": 1}'

file_client.upload_data(data, overwrite=True)