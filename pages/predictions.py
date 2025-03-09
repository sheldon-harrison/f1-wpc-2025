import streamlit as st
import pandas as pd
import boto3
from io import StringIO
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated

# AWS S3 configuration
S3_BUCKET_NAME = 'f1-wpc-2025'  # Replace with your actual bucket name
S3_FILE_KEY = 'predictions.csv'  # The file key for the predictions file

# Load environment variables from .env file
load_dotenv()

# Retrieve AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# aws_region = os.getenv('AWS_DEFAULT_REGION')

# Initialize an S3 client
s3_client = boto3.client('s3')

# Function to read the CSV file from S3
def read_predictions_from_s3():
    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_KEY)
        # Read the content into a pandas DataFrame
        predictions_df = pd.read_csv(response['Body'])
        return predictions_df
    except Exception as e:
        st.error(f"Error reading file from S3: {e}")
        return pd.DataFrame()

# Function to save the updated CSV back to S3
def save_predictions_to_s3(predictions_df):
    try:
        # Convert DataFrame to CSV in memory
        csv_buffer = StringIO()
        predictions_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Upload the CSV file to S3
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_KEY, Body=csv_buffer.getvalue())
        st.success("Predictions saved successfully!")
    except Exception as e:
        st.error(f"Error saving file to S3: {e}")

# Function to get the list of drivers from the F1 API
def get_drivers():
    url = "https://api.jolpi.ca/ergast/f1/2025/drivers/?format=json"  # API endpoint for 2025 drivers
    response = requests.get(url)
    data = response.json()
    
    # Extract the list of driver names
    drivers = [f"{driver['givenName']} {driver['familyName']}" for driver in data['MRData']['DriverTable']['Drivers']]
    
    return drivers

# Function to get the race list from the F1 API
def get_race_list():
    url = "https://api.jolpi.ca/ergast/f1/2025/races/"  # New API endpoint for 2025 race schedule
    response = requests.get(url)
    data = response.json()
    
    # Extract the list of race names
    race_names = [race['raceName'] for race in data['MRData']['RaceTable']['Races']]
    
    return race_names

# Function to get the race start time from the F1 API
def get_race_start_time(race_location):
    url = "https://api.jolpi.ca/ergast/f1/2025/races/"  # New API endpoint for 2025 race schedule
    response = requests.get(url)
    data = response.json()
    
    # Loop through the races and find the race matching the race_location
    for race in data['MRData']['RaceTable']['Races']:
        if race['raceName'] == race_location:
            race_start_time = race['date'] + "T" + race['time']
            return datetime.strptime(race_start_time, "%Y-%m-%dT%H:%M:%SZ")  # Parse to datetime object
    
    return None

# Function to update predictions
def update_predictions(new_predictions, name, race_location):
    # Read the current predictions from S3
    predictions_df = read_predictions_from_s3()

    # Check if the user has predictions for this race
    user_predictions = predictions_df[(predictions_df['Name'] == name) & (predictions_df['Race'] == race_location)]
    
    # If the user already has predictions, update them, otherwise add new row
    if not user_predictions.empty:
        predictions_df.loc[(predictions_df['Name'] == name) & (predictions_df['Race'] == race_location), 
                            ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']] = new_predictions
    else:
        new_row = {
            'Name': name,
            'Race': race_location,
            'P1': new_predictions[0],
            'P2': new_predictions[1],
            'P3': new_predictions[2],
            'P4': new_predictions[3],
            'P5': new_predictions[4],
            'P6': new_predictions[5],
            'P7': new_predictions[6],
            'P8': new_predictions[7],
            'P9': new_predictions[8],
            'P10': new_predictions[9],
        }
        predictions_df = predictions_df.append(new_row, ignore_index=True)

    # Save the updated predictions to S3
    save_predictions_to_s3(predictions_df)

# Streamlit UI for predictions
def predictions_page():
    st.title("Make Your Predictions")

    name = st.text_input("Enter your name")
    race_location = st.selectbox("Select the race", get_race_list())  # Replace with actual race locations

    # Get the race start time from the F1 API
    race_start_time = get_race_start_time(race_location)
    
    if race_start_time:
        st.write(f"The race start time for {race_location} is {race_start_time.strftime('%Y-%m-%d %I:%M %p')} (Eastern Time).")
    else:
        st.error(f"Could not retrieve race start time for {race_location}.")
        return

    # Get the list of drivers from the API
    drivers = get_drivers()

    # Read previous predictions
    predictions_df = read_predictions_from_s3()
    user_predictions = predictions_df[(predictions_df['Name'] == name) & (predictions_df['Race'] == race_location)]

    col1, col2 = st.columns(2)

    with col1:
        # New predictions drop downs
        st.write("Select your predictions for the top 10 drivers:")
        previous_predictions = [""] * 10  # Initialize with empty values if no previous predictions exist

        if not user_predictions.empty:
            # If previous predictions exist, use them
            previous_predictions = user_predictions.iloc[0][['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']].tolist()

        predictions = [st.selectbox(f"Predicted P{i+1}", drivers, index=drivers.index(previous_predictions[i]) if previous_predictions[i] else 0) for i in range(10)]
        
    with col2:
        # Display the existing predictions if available
        if not user_predictions.empty:
            st.write("Your previous predictions:")
            st.dataframe(user_predictions[['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']].T.rename(columns={0:'Driver'}))

    # Check if the current time is before the race start time
    current_time = datetime.now()
    if current_time > race_start_time:
        st.error("The race has already started. You cannot submit predictions anymore.")
        return

    if st.button("Submit Predictions"):
        # Update the predictions with new data
        update_predictions(predictions, name, race_location)

# Show the predictions page
predictions_page()
