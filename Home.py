import streamlit as st
import boto3
import os
import pandas as pd
from dotenv import load_dotenv

# Define pages and their navigation logic
PAGES = {
    "Home": "Home.py",
    # "Main": "main.py",
    "Predictions": "pages/Predictions.py",
    "Results": "pages/Results.py",
    "Standings": "pages/Standings.py"
}

load_dotenv()

# Retrieve AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# aws_region = os.getenv('AWS_DEFAULT_REGION')

# Initialize an S3 client
s3_client = boto3.client('s3')

# Function to handle authentication
def authenticate():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

def get_participants_from_s3():
    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), 
                                        Key=os.getenv('PARTICIPANTS_FILE'))
        # Read the content into a pandas DataFrame
        participants_df = pd.read_csv(response['Body'])
        return participants_df
    except Exception as e:
        st.error(f"Error reading file from S3: {e}")
        return pd.DataFrame()

# Function to show the login page
def login():
    st.title("Login")
    st.markdown("Please log in to access the 2025 F1 WPC.")
    participants_df = get_participants_from_s3().dropna()
    username = st.selectbox("Username",options=participants_df.Username.unique(),
                            index=None,help="You chose these, not me")
    password = st.text_input("Password", type="password",
                             help="Put that pigeon brain to good use. It's case sensitive.")

    if st.button("Log in"):
        if password == participants_df.loc[participants_df.Username==username,'Password'].values[0]:
            st.session_state["authenticated"] = True
            st.session_state["user"] = participants_df.loc[participants_df.Username==username,'Name'].values[0]
            st.success("Login successful! Redirecting...")
            st.session_state["page"] = "Main"  # Set page to Main after login
            st.rerun()  # Re-run the app to go to the Main page
        else:
            st.error(f"Incorrect password! Hint: {participants_df.loc[participants_df.Username==username,'Hint'].values[0]}")
            

# Function to show the main page after login
def main_page():
    if not st.session_state["authenticated"]:
        st.warning("Please log in first!")
        st.stop()  # Stop further execution until user is authenticated
    
    st.title("Home Page")
    
    st.markdown(f"""Hi, **{st.session_state.user}**! Welcome to the home page for the F1 WPC 2025! Here you can view, edit, or make new predictions,
                view the results of past races, or check the current season standings.""")

    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Predictions",use_container_width=True):
            st.switch_page(PAGES['Predictions'])  # Set page to Predictions
    
    with col2:
        if st.button("Results",use_container_width=True):
            st.switch_page(PAGES['Results'])  # Set page to Results
    
    with col3:
        if st.button("Standings",use_container_width=True):
            st.switch_page(PAGES['Standings'])

    with col4:
        if st.button("Log Out",use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()

# Function to handle page access
def app():
    authenticate()  # Check authentication state

    if not st.session_state["authenticated"]:
        login()  # Show login page if not authenticated
    else:
        main_page()

if __name__ == "__main__":
    app()
