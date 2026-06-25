from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import pandas as pd
import json
import io
import os


# =============================
# ENV + AUTH
# =============================
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

client_id = os.getenv("AZURE_CLIENT_ID", "").strip()
tenant_id = os.getenv("AZURE_TENANT_ID", "").strip()
client_secret = os.getenv("AZURE_CLIENT_SECRET", "").strip()

account_name = "jtbstorage001"

credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

service_client = DataLakeServiceClient(
    account_url=f"https://{account_name}.dfs.core.windows.net",
    credential=credential
)


# =============================
# HELPERS
# =============================

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "webp"}


def _get_buffer(file_client):
    """Download file and return BytesIO buffer."""
    data = file_client.download_file().readall()
    return BytesIO(data), data


# =============================
# JSON HANDLERS
# =============================
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

        if isinstance(raw, dict):
            for key in ["data", "results", "items"]:
                if isinstance(raw.get(key), list):
                    return pd.DataFrame(raw[key])
            return pd.DataFrame([raw])

        if isinstance(raw, list):
            return pd.DataFrame(raw)

    except Exception:
        return None


# =============================
# IMAGE HANDLER (ML SAFE)
# =============================
def _read_image(file_name: str, raw_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(raw_bytes))

        return {
            "file_name": file_name,
            "format": img.format.lower() if img.format else None,
            "width": img.width,
            "height": img.height,
            "size_bytes": len(raw_bytes),
            "bytes": raw_bytes,
            "pil_image": img
        }

    except Exception as e:
        raise ValueError(f"Invalid image file: {file_name}") from e


def _is_image(file_name: str):
    return file_name and file_name.lower().split(".")[-1] in IMAGE_EXTENSIONS


def _is_csv(file_name: str):
    return file_name and file_name.lower().endswith(".csv")


def _is_json(file_name: str):
    return file_name and file_name.lower().endswith(".json")


# =============================
# MAIN READER
# =============================
def read_adls_file(file_client, file_name: str = None):
    """
    Unified ADLS file reader.

    Returns:
        - pd.DataFrame for CSV/JSON
        - dict for images (ML-ready)
    """

    buffer, raw_bytes = _get_buffer(file_client)

    # -------------------------
    # IMAGE
    # -------------------------
    if _is_image(file_name):
        return _read_image(file_name, raw_bytes)

    # -------------------------
    # CSV
    # -------------------------
    if _is_csv(file_name):
        buffer.seek(0)
        return pd.read_csv(buffer)

    # -------------------------
    # JSON
    # -------------------------
    if _is_json(file_name):
        df = _try_records_json(buffer)
        if df is not None:
            return df

        df = _try_ndjson(buffer)
        if df is not None:
            return df

        df = _try_nested_json(buffer)
        if df is not None:
            return df

        raise ValueError(f"Unable to parse JSON: {file_name}")

    raise ValueError(f"Unsupported file type: {file_name}")