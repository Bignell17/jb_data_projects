# import azure.identity
from azure.storage.blob import BlobServiceClient
import time
import os
import json
import streamlit as st

##################### PRODUCTION CODE Commented out ########################
# def get_config_value(name):
#     value = os.environ.get(name)

#     if value is not None:
#         return value

#     return st.secrets.get(name)


# account_url = get_config_value("ACCOUNT_URL")
# creds = get_config_value("CREDENTIALS")

# if not account_url:
#     raise RuntimeError("ACCOUNT_URL is not configured")

# if not creds:
#     raise RuntimeError("CREDENTIALS is not configured")

# account_url = os.environ.get("ACCOUNT_URL", st.secrets.get("ACCOUNT_URL"))
# creds = os.environ.get("CREDENTIALS", st.secrets.get("CREDENTIALS"))

###########################################################################
account_url = st.secrets['ACCOUNT_URL']
creds = st.secrets['CREDENTIALS']

def move_reviewed_transcript(blob_name:str):

    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")

    source_client = container_client.get_blob_client(blob=blob_name)
    destination_name = "for_review/"+blob_name.split("/")[1]

    destination_client = container_client.get_blob_client(blob=destination_name)

    print(source_client.blob_name)

    copy = destination_client.start_copy_from_url(source_url=source_client.url)

    while True:
        props = destination_client.get_blob_properties()
        if props.copy.status == "success":
            break
        elif props.copy.status == "failed":
            raise Exception("Copy Failed")
        time.sleep(1)

    source_client.delete_blob()


def azure_blob_ingest():

    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("transcripts")

    transcript_files = container_client.list_blobs(name_starts_with="full_transcripts/")

    for tf in transcript_files:
        blob_client = container_client.get_blob_client(blob=tf.name)
        text_file = blob_client.download_blob().readall()
        transcript = text_file.decode("utf-8")

        return transcript, tf.name


def azure_blob_items_check():

    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")

    transcript_files = container_client.list_blobs(name_starts_with="for_review/")

    if transcript_files:
        return True
    else:
        return False


def azure_blob_ingest_json():

    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")

    transcript_files = container_client.list_blobs(name_starts_with="for_review/")

    for tf in transcript_files:

        blob_client = container_client.get_blob_client(blob=tf.name)
        json_file = blob_client.download_blob().readall()
        transcript = json.loads(json_file)

        if all(x["reviewed"] == True for x in transcript):
            # move_reviewed_transcript(tf.name)
            continue

        return transcript, tf.name

    return None, "Empty Folder"   


def get_max_approval_id():

    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")
    approved_blob = container_client.get_blob_client(blob="approved/approved.jsonl")

    stream = approved_blob.download_blob().readall().decode("utf-8")

    if stream:
    
        approval_id_list = [
            json.loads(x)["approval_id"]
            for x in stream.splitlines()
            ]

        return max(approval_id_list)

    else:
        return 0


def azure_blob_append_rag_dictionary(new_addition,segment_verdict:str):


    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")

    rag_blob = container_client.get_blob_client(blob=f"{segment_verdict}/{segment_verdict}.jsonl")

    stream = rag_blob.download_blob().readall().decode("utf-8")

    rag_dict = [
        json.loads(x) 
        for x in stream.splitlines()
        ]
    rag_dict.append(new_addition)


    new_jsonl = "\n".join(
        json.dumps(record)
        for record in rag_dict
    )

    try:
        rag_blob.upload_blob(
            data=new_jsonl.encode("utf-8"),
            overwrite=True
        )

        return "Successfully Appended Segment"
    except Exception as e:
        return f"Failed to Append Segment: {repr(e)}" 


def azure_blob_update_source_file(file_name:str,updated_json):


    blob_service_client = BlobServiceClient(account_url=account_url,credential=creds)
    container_client = blob_service_client.get_container_client("processed")

    json_blob = container_client.get_blob_client(blob=file_name)

    try:
        json_blob.upload_blob(
            data=json.dumps(updated_json,indent=2),
            overwrite=True
        )

        return "Successfully Updated File"
    except Exception as e:
        return f"Failed to Update File: {repr(e)}" 