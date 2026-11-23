import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/app.py", title="Login"),
        st.Page("pages/review.py", title="Review")
    ],
    position="hidden"
)

pg.run()

