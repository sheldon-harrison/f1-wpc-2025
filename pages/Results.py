import streamlit as st
import pandas as pd
import utils
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated


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

def get_all_user_scores(predictions_df,race_results):
    all_predictions = pd.DataFrame(columns=['Predictor','Points'])
    for this_user in predictions_df.Name.unique():
        this_user_predictions = predictions_df[predictions_df['Name']==this_user]
        user_points = calculate_scores(this_user_predictions,race_results).Points.sum()
        all_predictions = pd.concat([all_predictions,
                                    pd.DataFrame([{'Predictor':this_user,'Points':user_points}])],
                                    axis=0,
                                    ignore_index=True)
    positions_list = ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10','P11','P12','P13','P14']
    all_predictions = all_predictions.sort_values(by='Points',ascending=False).reset_index(drop=True)
    all_predictions = all_predictions.set_index(pd.Index(positions_list[:len(all_predictions)]))
    return all_predictions

# Function to show the results page
def results_page():
    st.title("Race Results and Predictions")
    st.markdown("Choose a race to see results")
    race_list,race_dict = utils.get_race_list()
    race_location = st.selectbox("Select the race", race_list)
    st.info("More stats coming soon!")
    try:
        race_results = pd.DataFrame([get_race_results(race_dict[race_location])])
        race_results = race_results.T.rename(columns={0:'Driver'})
    except:
        race_results = pd.DataFrame()
    predictions_df = utils.read_predictions_from_s3()
    user_predictions = predictions_df[((predictions_df['Race']==race_location)&
                                       (predictions_df['Name']==st.session_state.user))]
    user_predictions = calculate_scores(user_predictions,race_results)
    all_scores = get_all_user_scores(predictions_df[predictions_df['Race']==race_location],race_results)

    if race_results.empty:
        st.error(f"Could not retrieve race results for the {race_location}.")
        return
    elif user_predictions.empty:
        st.error(f"No user predictions found for {st.session_state.user}.")
        return
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("Actual Race Results")
            st.dataframe(race_results,use_container_width=True)
            
        with col2:
            st.markdown(f"Your Results ({st.session_state.user}) - **{user_predictions.Points.sum()}** pts")
            st.dataframe(user_predictions)
            
        with col3:
            st.markdown("Group Prediction Results")
            st.dataframe(all_scores)

# Show the results page
results_page()
