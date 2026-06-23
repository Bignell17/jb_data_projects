# pip install pandas pyarrow azure-identity azure-storage-blob
# pip install azure-storage-file-datalake

from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import pandas as pd
import io

# Authenticate
tenant_id = "04040e37-4101-439a-9e6d-dd85f8a880cb"
client_id = "9d8f92ef-a39c-4cbb-aaf3-ba31f3d18f25"
client_secret = "~lj8Q~~EmOWvYXT693mSMY7gQJSgPYRzBSXMudkV"
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