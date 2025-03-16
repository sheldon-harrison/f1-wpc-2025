import streamlit as st
import pandas as pd
import utils
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated

# Streamlit UI for predictions
def predictions_page():
    st.title("Make Your Predictions")
    st.markdown("Enter your predictions here! You can also edit past predictions, as long as it's before the scheduled race start time.")
    race_list,race_dict = utils.get_race_list()

    name = st.text_input("Enter your name",value=st.session_state.user,disabled=True)
    race_location = st.selectbox("Select the race", race_list)  # Replace with actual race locations

    # Get the race start time from the F1 API
    race_start_time = utils.get_race_start_time(race_location)
    race_start_time_et = race_start_time.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Toronto"))
    if race_start_time:
        st.write(f"The race start time for {race_location} is {race_start_time_et.strftime('%A %b %d %I:%M %p')} (Eastern Time).")
    else:
        st.error(f"Could not retrieve race start time for {race_location}.")
        return

    # Get the list of drivers from the API
    drivers = utils.get_drivers(race_dict[race_location])

    # Read previous predictions
    predictions_df = utils.read_predictions_from_s3()
    user_predictions = predictions_df[(predictions_df['Name'] == name) & (predictions_df['Race'] == race_location)]
    user_predictions = user_predictions.drop_duplicates(subset='Race',keep='last').reset_index(drop=True)

    col1, col2 = st.columns(2)

    with col1:
        # New predictions drop downs
        st.write("Select your predictions for the top 10 drivers:")
        previous_predictions = [""] * 10  # Initialize with empty values if no previous predictions exist

        if not user_predictions.empty:
            # If previous predictions exist, use them
            previous_predictions = user_predictions.iloc[0][['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']].tolist()

        predictions = [st.selectbox(f"Predicted P{i+1}", drivers, index=drivers.index(previous_predictions[i]) if previous_predictions[i] else None) for i in range(10)]
        
    with col2:
        # Display the existing predictions if available
        if not user_predictions.empty:
            st.write("Your previous predictions:")
            st.write("")
            st.dataframe(user_predictions[['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10']].T.rename(columns={0:'Driver'}))

    # Check if the current time is before the race start time
    current_time = datetime.now()
    if current_time > race_start_time:
        st.error("The race has already started. You cannot submit predictions anymore.")
        return

    if st.button("Submit Predictions"):
        # Update the predictions with new data
        utils.update_predictions(predictions, name, race_location)

# Show the predictions page
predictions_page()
