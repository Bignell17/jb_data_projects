import streamlit as st

CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
TENANT_ID = st.secrets["TENANT_ID"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPES = [
    "User.Read"
]

################### PRODUCTION ####################
# import os
# import streamlit as st


# def get_config_value(name):
#     value = os.environ.get(name)

#     if value is not None:
#         return value

#     return st.secrets.get(name)


# CLIENT_ID = get_config_value("CLIENT_ID")
# CLIENT_SECRET = get_config_value("CLIENT_SECRET")
# TENANT_ID = get_config_value("TENANT_ID")
# REDIRECT_URI = get_config_value("REDIRECT_URI")

# if not CLIENT_ID:
#     raise RuntimeError("CLIENT_ID is not configured")

# if not CLIENT_SECRET:
#     raise RuntimeError("CLIENT_SECRET is not configured")

# if not TENANT_ID:
#     raise RuntimeError("TENANT_ID is not configured")

# if not REDIRECT_URI:
#     raise RuntimeError("REDIRECT_URI is not configured")


# AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# SCOPES = [
#     "User.Read"
# ]

