import streamlit as st
import pandas as pd
import boto3
from io import StringIO
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import requests
from zoneinfo import ZoneInfo

# Load environment variables from .env file
load_dotenv()

# Retrieve AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# aws_region = os.getenv('AWS_DEFAULT_REGION')

# Initialize an S3 client
s3_client = boto3.client('s3')

# F1 scoring dict, anything beyond 10 gets 0 points
f1_scoring_dict = {
    1:25,
    2:18,
    3:15,
    4:12,
    5:10,
    6:8,
    7:6,
    8:4,
    9:2,
    10:1
}

# Function to read the CSV file from S3
def read_predictions_from_s3():
    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=os.getenv('PREDICTIONS_FILE'))
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
        s3_client.put_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=os.getenv('PREDICTIONS_FILE'), Body=csv_buffer.getvalue())
        st.success("Predictions saved successfully!")
    except Exception as e:
        st.error(f"Error saving file to S3: {e}")

# Function to get the list of drivers from the F1 API
def get_drivers(round):
    url = f"https://api.jolpi.ca/ergast/f1/2025/{round}/drivers/?format=json"  # API endpoint for 2025 drivers
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
    race_list = [race['raceName'] for race in data['MRData']['RaceTable']['Races']]
    race_dict = {item: index for index, item in enumerate(race_list, start=1)}
    return race_list,race_dict

# Function to get the race start time from the F1 API
def get_race_start_time(race_location):
    url = "https://api.jolpi.ca/ergast/f1/2025/races/"  # New API endpoint for 2025 race schedule
    response = requests.get(url)
    data = response.json()
    
    # Loop through the races and find the race matching the race_location
    for race in data['MRData']['RaceTable']['Races']:
        if race['raceName'] == race_location:
            race_start_time = race['date'] + "T" + race['time']
            utc_dt = datetime.strptime(race_start_time, "%Y-%m-%dT%H:%M:%SZ")
            return utc_dt
    
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
        new_row = [{
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
        }]
        predictions_df = pd.concat([predictions_df,
                                    pd.DataFrame(new_row)],
                                    axis=0,
                                    ignore_index=True)

    # Save the updated predictions to S3
    save_predictions_to_s3(predictions_df)

# Function to get the race results from the F1 API
def get_race_results(round):
    url = f"https://api.jolpi.ca/ergast/f1/2025/{round}/results/?format=json"
    
    response = requests.get(url)
    data = response.json()
    race_results = data['MRData']['RaceTable']['Races'][0]['Results']
    results_dict = {}
    for result in race_results:
        position = int(result['position'])  # Position is a string, so convert to int
        driver_name = f"{result['Driver']['givenName']} {result['Driver']['familyName']}"
        results_dict[position] = driver_name
    return results_dict

def calculate_scores(user_predictions, race_results):
    user_scores = []
    predicted_pos = 1
    for drop_col in ['Race','Name']:
        if drop_col in user_predictions.columns:
            user_predictions = user_predictions.drop(columns=drop_col)
    for position in user_predictions.columns:
        driver = user_predictions[position].values[0]
        try:
            real_pos = race_results[race_results['Driver'] == driver].index.tolist()[0]
            user_scores.append(max(0,(10 - abs(real_pos-predicted_pos))))
        except:
            user_scores.append(0)
        predicted_pos += 1
    
    user_predictions = user_predictions.reset_index(drop=True).T.rename(columns={0:'Driver'})
    user_predictions['Points'] = user_scores
    return user_predictions

def apply_f1_scoring(user_scores_df):
    """
    user_scores_df: DataFrame with columns ['Predictor', 'Score']
    Returns: DataFrame with columns ['Predictor', 'Score', 'Points', 'Place']
    Handles ties: tied users get full points for that place, next place(s) are skipped.
    """
    # Sort by Score descending
    user_scores_df = user_scores_df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    user_scores_df['Place'] = None
    user_scores_df['Points'] = 0

    place = 1
    i = 0
    n = len(user_scores_df)
    while i < n:
        # Find all users with this score (tie group)
        score = user_scores_df.loc[i, 'Score']
        tie_indices = user_scores_df.index[user_scores_df['Score'] == score].tolist()
        tie_count = len(tie_indices)
        # Assign place and F1 points to all in tie group
        for idx in tie_indices:
            user_scores_df.at[idx, 'Place'] = place
            user_scores_df.at[idx, 'Points'] = f1_scoring_dict.get(place, 0)
        # Move to next group, skipping places for ties
        i += tie_count
        place += tie_count

    user_scores_df['Place'] = user_scores_df['Place'].astype(int)
    return user_scores_df

def get_all_user_scores(predictions_df, race_results):
    """
    Returns DataFrame with columns: Predictor, Score, Points, Place
    """
    all_scores = []
    for this_user in predictions_df.Name.unique():
        this_user_predictions = predictions_df[predictions_df['Name'] == this_user]
        user_score = calculate_scores(this_user_predictions, race_results).Points.sum()
        all_scores.append({'Predictor': this_user, 'Score': user_score})
    user_scores_df = pd.DataFrame(all_scores)
    user_scores_df = apply_f1_scoring(user_scores_df)
    return user_scores_df