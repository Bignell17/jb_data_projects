import streamlit as st

from auth import get_auth_url, acquire_token

st.set_page_config(page_title="Review Portal")


# ---------------------------------
# OAuth callback
# ---------------------------------

query = st.query_params

if "code" in query:

    result = acquire_token(query["code"])

    if "id_token_claims" in result:

        st.session_state["user"] = result["id_token_claims"]

        # Remove ?code=... from the browser URL
        st.query_params.clear()

        st.switch_page("pages/Review.py")

    else:
        st.error(
            result.get(
                "error_description",
                "Authentication failed."
            )
        )

    st.stop()


# ---------------------------------
# Already authenticated
# ---------------------------------

if "user" in st.session_state:

    user = st.session_state["user"]

    st.success(
        f"Welcome {user.get('name', 'User')}"
    )

    st.write(
        user.get("preferred_username", "")
    )

    if st.button("Continue to Review"):
        st.switch_page("pages/Review.py")

    st.stop()


# ---------------------------------
# Login screen
# ---------------------------------

import streamlit as st
import html
 
st.title("Review Portal")
 
st.write(
    "Sign in using your Microsoft company account."
)
 
if "auth_url" not in st.session_state:
    st.session_state["auth_url"] = get_auth_url()
 
auth_url = html.escape(
    st.session_state["auth_url"],
    quote=True
)
 
st.html(
    f"""
    <a href="{auth_url}" target="_self"
       style="
           display: inline-block;
           padding: 0.5rem 1rem;
           background-color: #2563eb;
           color: white;
           text-decoration: none;
           border-radius: 0.5rem;
           font-weight: 600;
       ">
        Sign in with Microsoft
    </a>
    """
)



# if st.button("Sign in with Microsoft"):
    
#     st.markdown(
#     f"""
#     <script>
#     window.location.href = "{st.session_state["auth_url"]}";
#     </script>
#     """,
#     unsafe_allow_html=True,
#     )
