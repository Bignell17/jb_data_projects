import streamlit as st
import json
from random import randint
from datetime import datetime
import time
from adls_ingestion import azure_blob_ingest_json, azure_blob_append_rag_dictionary, azure_blob_update_source_file, get_max_approval_id
import os

CATEGORY_LABELS = [
"FAQ",
"Definition",
"Process",
"Reporting",
"Troubleshooting",
"Issue"
]

SUBJECT_LABELS = [
    "PAFA",
    "AUGE",
    "AQ",
    "Shipperless Sites",
    "MPRN",
    "Data Requests",
    "Data Delivery",
    "Data Anonymisation",
    "Teams / Collaboration",
    "Risk Register",
    "DESNZ",
    "Other"
]

categories = CATEGORY_LABELS
subjects = SUBJECT_LABELS
st.set_page_config(initial_sidebar_state="collapsed")


def update_variables(segment_json, is_empty: bool):

    if is_empty:
        st.session_state.id = None
        st.session_state.category = None
        st.session_state.subject_area = None
        st.session_state.question = ""
        st.session_state.answer = ""
        st.session_state.source = ""
        st.session_state.current_segment_content = "No segments awaiting review."
        st.session_state.edit_segment_properties = False
        st.session_state.edit_question = ""
        st.session_state.edit_answer = ""

    else:
        st.session_state.id = segment_json["review_id"]
        st.session_state.question = segment_json["question"]
        st.session_state.answer = segment_json["answer"]
        st.session_state.category = segment_json["category"]
        st.session_state.subject_area = segment_json["subject_area"]
        st.session_state.source = segment_json["source"]

        st.session_state.current_segment_content = (
            "Question:\n"
            + segment_json["question"]
            + "\n\nAnswer:\n"
            + segment_json["answer"]
        )

        st.session_state.edit_segment_properties = False
        st.session_state.edit_question = segment_json["question"]
        st.session_state.edit_answer = segment_json["answer"]

if "result" not in st.session_state:

    st.session_state.all_segments_json, st.session_state.current_segment_name = (
        azure_blob_ingest_json()
    )

    # Handle a missing or empty JSON file
    if not st.session_state.all_segments_json:
        st.session_state.filtered_segments_json = []
        st.session_state.segment_counter = 0
        update_variables(None, True)
        st.session_state.is_empty = True

    else:
        # Keep only unreviewed segments
        st.session_state.filtered_segments_json = [
            x for x in st.session_state.all_segments_json
            if x.get("reviewed", False) is False
        ]

        st.session_state.segment_counter = 0

        # Check whether any unreviewed segments remain
        if st.session_state.filtered_segments_json:

            segment_json = st.session_state.filtered_segments_json[0]

            st.session_state.result = None
            update_variables(segment_json, False)
            st.session_state.is_empty = False

        else:
            # All segments have already been reviewed
            st.session_state.segment_counter = 0
            update_variables(None, True)
            st.session_state.is_empty = True

    st.session_state.approved_by = ""
    st.session_state.action_message = None


if "user" not in st.session_state:
    st.switch_page("app.py")
 
user = st.session_state["user"]



def action_segment(segment_verdict:str):

    # Approving a segment sends the approved json to the rag dict as well as a reviewed_processed json

    reviewed = True

    if segment_verdict == "for_review":
        reviewed = False

    approved_segment = {
    "approval_id": get_max_approval_id()+1,
    "review_id": st.session_state.id,
    "category": st.session_state.category,
    "subject_area": st.session_state.subject_area,
    "question": st.session_state.question, 
    "answer": st.session_state.answer,        
    "source": st.session_state.source,
    "reviewed_by": st.session_state["user"]["name"],
    "reviewed_at": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    }

    if segment_verdict != "review_audit":
        approved_segment.pop("approval_id")

    current_index = next(
        i for i, term in enumerate(st.session_state.all_segments_json)
            if term["review_id"] == st.session_state.id
    )

    if segment_verdict != "for_review":

        st.session_state.all_segments_json[current_index]["reviewed"] = True
        update_msg = azure_blob_update_source_file(file_name=st.session_state.current_segment_name,updated_json=st.session_state.all_segments_json)
        return_msg = azure_blob_append_rag_dictionary(approved_segment,segment_verdict)

    st.session_state.segment_counter += 1

    if st.session_state.segment_counter < len(st.session_state.filtered_segments_json):            

        segment_json = st.session_state.filtered_segments_json[st.session_state.segment_counter]
        update_variables(segment_json,False)

    else:
        
        st.session_state.all_segments_json, st.session_state.current_segment_name = azure_blob_ingest_json()

        if st.session_state.all_segments_json:

            st.session_state.filtered_segments_json = [x for x in st.session_state.all_segments_json if x["reviewed"] == False]
            st.session_state.segment_counter = 0

            segment_json = st.session_state.filtered_segments_json[0]
            update_variables(segment_json,False)

        else:
            update_variables(None,True)
            st.session_state.is_empty = True


spacer_col, refresh_col = st.columns([9, 1])
 

title_col, spacer_col, refresh_col = st.columns([6, 3, 1])
 
with title_col:
    st.title("Review Form")
 
with refresh_col:
    if st.button(
        "",
        key="refresh_data",
        help="Refresh data from Azure Storage",
        icon=":material/refresh:",
        use_container_width=True,
    ):
        st.session_state["refresh_clicked"] = True
        st.session_state.pop("result", None)
        st.rerun()
 
# Display confirmation after the refresh
if st.session_state.pop("refresh_clicked", False):
    st.toast("Data refreshed successfully from Azure Storage!", icon="✅")
     

if st.session_state.is_empty:
    st.info("No segments awaiting review.")
else:
    st.markdown(
        f"Review ID: {st.session_state.id}  \n"
        f"Interview Source: {st.session_state.source}  \n"
        f"Segment ({st.session_state.segment_counter + 1}/"
        f"{len(st.session_state.filtered_segments_json)})"
    )


with st.container(border=True):

    segment_edit = st.text_area(label="Segment Edit",
                                label_visibility="collapsed",
                                value=st.session_state.current_segment_content,
                                height="content",
                                disabled=st.session_state.is_empty)

# -----------------------------
# Category / Subject Area row
# -----------------------------
# index=categories.index(st.session_state.category)

cat_label, subject_label = st.columns(
    [2.5, 2.7]
)

cat_col, subject_col = st.columns(
    [2.5, 2.7]
)

with cat_label:
    st.text("Category:")

with cat_col:
    category = st.selectbox(
        "Category",
        categories,
        label_visibility="collapsed",
        disabled=st.session_state.is_empty,
        index=(
            categories.index(st.session_state.category)
            if st.session_state.category in categories
            else 0
        )
    )

with subject_label:
    st.text("Subject Area:")

with subject_col:
    subject_area = st.selectbox(
        "Subject Area",
        subjects,
        label_visibility="collapsed",
        disabled=st.session_state.is_empty,
        index=(
            subjects.index(st.session_state.subject_area)
            if st.session_state.subject_area in subjects
            else 0
        )
    )

approve_col, reject_col, review_col = st.columns(
    [1.2, 1.2, 1.5]
)

with approve_col:
    if st.button(
        "Approve",
        use_container_width=True,
        disabled=st.session_state.is_empty
    ):
        # If the user has edited the segment, use the edited values
        if st.session_state.edit_segment_properties:
            st.session_state.question = st.session_state.edit_question
            st.session_state.answer = st.session_state.edit_answer

        rag_dict_output = {
            "approval_id": get_max_approval_id() + 1,
            "review_id": st.session_state.id,
            "input": st.session_state.question,
            "output": st.session_state.answer,
            "category": category,
            "subject_area": subject_area
        }

        return_msg = azure_blob_append_rag_dictionary(
            rag_dict_output,
            "approved"
        )

        action_segment("review_audit")
        st.session_state.action_message = f"{st.session_state.id} Approved"
        st.rerun()


with reject_col:
    if st.button(
        "Reject",
        use_container_width=True,
        disabled=st.session_state.is_empty
    ):
        action_segment("rejected")
        st.session_state.action_message = f"{st.session_state.id} Rejected"
        st.rerun()


with review_col:
    if st.button(
        "Further Review",
        use_container_width=True,
        disabled=st.session_state.is_empty
    ):
        action_segment("for_review")
        st.session_state.action_message = f"{st.session_state.id} Sent for review"
        st.rerun()

# Edit the segment properties

if st.session_state.action_message:
    st.info(st.session_state.action_message)

if st.checkbox("Edit Segment Properties", key="edit_segment_properties", disabled=st.session_state.is_empty):

    st.text_area(
        "Question",
        value=st.session_state.question,
        key="edit_question",
        height=200,
        disabled=st.session_state.is_empty
    )

    st.text_area(
        "Answer",
        value=st.session_state.answer,
        key="edit_answer",
        height=300,
        disabled=st.session_state.is_empty
    )


if st.button("Logout"):

    st.session_state.clear()
    st.switch_page("app.py")