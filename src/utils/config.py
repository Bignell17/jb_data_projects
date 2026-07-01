import json
import os
import io
from io import BytesIO
from pathlib import Path
from PIL import Image
import pandas as pd
from dotenv import load_dotenv
import boto3
from botocore.client import Config

# Imports for Key Vault
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.filedatalake import DataLakeServiceClient

# =============================
# ENV + AUTH
# =============================
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

# Fetch Key Vault details from local .env
tenant_id = os.getenv("AZURE_TENANT_ID", "").strip()
kv_client_id = os.getenv("AZURE_KEY_VAULT_CLIENT_ID", "").strip()
kv_client_secret = os.getenv("AZURE_KEY_VAULT_CLIENT_SECRET", "").strip()
key_vault_url = os.getenv("KEY_VAULT_URL", "").strip()

account_name = "jtbstorage001"

# Authenticate to Key Vault
kv_credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=kv_client_id,
    client_secret=kv_client_secret
)
kv_client = SecretClient(vault_url=key_vault_url, credential=kv_credential)

try:
    # Retrieve the ABFS/Storage credentials dynamically from Key Vault
    storage_client_id = kv_client.get_secret("jtbstorage001-container-abfs-client-id").value
    storage_client_secret = kv_client.get_secret("jtbstorage001-container-abfs-client-secret").value
except Exception as e:
    raise RuntimeError(f"Failed to fetch storage credentials from Key Vault: {e}")

# Authenticate to ADLS Gen2 using the secrets retrieved from Key Vault
storage_credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=storage_client_id,
    client_secret=storage_client_secret
)

service_client = DataLakeServiceClient(
    account_url=f"https://{account_name}.dfs.core.windows.net",
    credential=storage_credential
)

#################################
# read_adls_file ################
#################################
# =============================
# HELPERS
# =============================

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

def _try_json_parsers(buffer):
    """Tries parsing standard records, NDJSON (lines), and nested structures sequentially."""
    # 1. Standard or NDJSON records
    for lines_flag in [False, True]:
        try:
            buffer.seek(0)
            return pd.read_json(buffer, lines=lines_flag)
        except Exception:
            continue
            
    # 2. Nested JSON fallback with list extraction (Fixed original unreachable bug)
    try:
        buffer.seek(0)
        raw = json.load(buffer)
        if isinstance(raw, dict):
            for key in ["data", "results", "items"]:
                if isinstance(raw.get(key), list):
                    return pd.DataFrame(raw[key])
            return pd.DataFrame([raw])
        return pd.DataFrame(raw) if isinstance(raw, list) else None
    except Exception:
        return None

def read_adls_file(file_client, file_name: str = ""):
    """Unified ADLS file reader. Returns pd.DataFrame or ML-ready image dictionary."""
    data = file_client.download_file().readall()
    buffer = io.BytesIO(data)
    ext = pathlib.Path(file_name or "").suffix.lower()

    # 1. Handle Images
    if ext in IMAGE_EXTENSIONS:
        try:
            img = Image.open(buffer)
            return {
                "file_name": file_name, "bytes": data, "pil_image": img,
                "format": img.format.lower() if img.format else None,
                "width": img.width, "height": img.height, "size_bytes": len(data),
            }
        except Exception as e:
            raise ValueError(f"Invalid image file: {file_name}") from e

    # 2. Handle CSV
    if ext == ".csv":
        return pd.read_csv(buffer)

    # 3. Handle JSON
    if ext == ".json":
        df = _try_json_parsers(buffer)
        if df is not None:
            return df
        raise ValueError(f"Unable to parse JSON: {file_name}")

    raise ValueError(f"Unsupported file type: {file_name}")

#####################################################
# Read ALL files in a folder directory ##############
#####################################################

def read_adls_folder(service_client, container_name, folder_path: str):
    container_client = service_client.get_file_system_client(container_name)

    results = []

    for p in container_client.get_paths(path=folder_path):
        file_client = container_client.get_file_client(p.name)

        results.append(
            read_adls_file(file_client, file_name=p.name)
        )

    return results

########################################################################
# Read File from Docker (AWS S3 Storage facility) ######################
########################################################################

def read_docker_file(bucket_name: str, file_key: str) -> io.BytesIO:
    """
    Acts as an ingestion UDF. Connects to the local Docker MinIO 
    container and downloads a file into an in-memory byte buffer.
    """
    # Map to your Docker Desktop container port 9000
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',   # Local host on 
        aws_access_key_id='minioadmin',         # Default MinIO credentials
        aws_secret_access_key='minioadmin',     # Default MinIO credentials
        config=Config(signature_version='s3v4') #Uses AWS S3 storage
    )
    
    # Download the file object straight into memory buffer
    file_buffer = io.BytesIO()
    s3_client.download_fileobj(bucket_name, file_key, file_buffer)
    file_buffer.seek(0) # Reset buffer pointer to the beginning
    
    return file_buffer