import streamlit as st

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated

st.title("F1 Fantasy Pool")

st.write("Welcome! Choose an option below:")

# Navigation buttons
if st.button("Submit Predictions"):
    st.switch_page("pages/predictions.py")

if st.button("View Race Results"):
    st.switch_page("pages/results.py")

if st.button("View Season Standings"):
    st.switch_page("pages/standings.py")
