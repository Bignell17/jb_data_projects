from src.utils.config import service_client, read_adls_file

file_system = service_client.get_file_system_client("jb-test-container")
file_client = file_system.get_file_client("api_data/data.json")

df = read_adls_file(file_client, file_name="data.json")
print(df.head())