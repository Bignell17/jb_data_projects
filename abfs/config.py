from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

# Credentials
client_id = os.getenv("AZURE_CLIENT_ID", "").strip()
tenant_id = os.getenv("AZURE_TENANT_ID", "").strip()
client_secret = os.getenv("AZURE_CLIENT_SECRET", "").strip()

account_name = "jtbstorage001"

# Auth object
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

# Service client (reusable everywhere)
service_client = DataLakeServiceClient(
    account_url=f"https://{account_name}.dfs.core.windows.net",
    credential=credential
)

import json
import pandas as pd
from io import BytesIO


def _try_records_json(buffer):
    try:
        buffer.seek(0)
        return pd.read_json(buffer, orient="records")
    except Exception:
        return None


def _try_ndjson(buffer):
    try:
        buffer.seek(0)
        return pd.read_json(buffer, lines=True)
    except Exception:
        return None


def _try_nested_json(buffer):
    try:
        buffer.seek(0)
        raw = json.load(buffer)

        # common pattern: {"data": [...]}
        if isinstance(raw, dict):
            for key in ["data", "results", "items"]:
                if key in raw and isinstance(raw[key], list):
                    return pd.DataFrame(raw[key])

            # single object fallback
            return pd.DataFrame([raw])

        # list fallback
        if isinstance(raw, list):
            return pd.DataFrame(raw)

    except Exception:
        return None


def read_adls_file_to_df(file_client, file_type="json"):
    """
    Reads a file from ADLS Gen2 using a file_client and returns a pandas DataFrame.

    Parameters:
        file_client: Azure DataLake file client
        file_type: 'json' or 'csv'

    Returns:
        pandas.DataFrame
    """
    download = file_client.download_file()
    data = download.readall()

    buffer = BytesIO(data)

    if file_type == "json":

        df = _try_records_json(buffer)
        if df is not None:
            return df

        df = _try_ndjson(buffer)
        if df is not None:
            return df

        df = _try_nested_json(buffer)
        if df is not None:
            return df

        raise ValueError("Unable to parse JSON in any known format")

    raise ValueError(f"Unsupported file type: {file_type}")

