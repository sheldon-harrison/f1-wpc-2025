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


# Function to show the results page
def results_page():
    st.title("Race Results and Predictions")
    st.markdown("Select a race to see the results!")
    race_list,race_dict = utils.get_race_list()
    race_location = st.selectbox("Select the race", race_list)
    # st.info("More stats coming soon!")
    try:
        race_results = pd.DataFrame([utils.get_race_results(race_dict[race_location])])
        race_results = race_results.T.rename(columns={0:'Driver'})
    except:
        race_results = pd.DataFrame()
    predictions_df = utils.read_predictions_from_s3()
    user_predictions = predictions_df[((predictions_df['Race']==race_location)&
                                       (predictions_df['Name']==st.session_state.user))]

    if race_results.empty:
        st.error(f"Could not retrieve race results for the {race_location}. Check back again later.")
        return
    elif user_predictions.empty:
        st.error(f"No predictions found for {st.session_state.user}. Did you forget to submit them?")
        return
    else:
        user_predictions = utils.calculate_scores(user_predictions,race_results)
        all_scores = utils.get_all_user_scores(predictions_df[predictions_df['Race']==race_location],race_results)
        st.markdown(f"""**{race_results.loc[1,'Driver']}** won the actual race.
                    You scored **{user_predictions.Points.sum()}** pts for this race.""")
        winners = all_scores.loc[all_scores.Points==all_scores.Points.max(),'Predictor']
        if len(winners)>1:
            st.markdown(f"""**{", ".join([winner for winner in winners])}** won this race, scoring **{all_scores.Points.max()}** pts each.
                        The group average score was **{all_scores.Points.mean().round(1)}** pts.
                        The group score variation was **{(all_scores.Points.std()/all_scores.Points.mean()*100).round(1)}\%**.""")
        else:
            st.markdown(f"""**{winners.values[0]}** won this race with **{all_scores.Points.max()}** pts.
                        The group average score was **{all_scores.Points.mean().round(1)}** pts.
                        The group score variation was **{(all_scores.Points.std()/all_scores.Points.mean()*100).round(1)}\%**.""")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Actual Race Results**")
            st.dataframe(race_results,use_container_width=True)
            
        with col2:
            st.markdown(f"**Your Results ({st.session_state.user})**")
            st.dataframe(user_predictions)
            
        with col3:
            st.markdown("**Group Prediction Results**")
            st.dataframe(all_scores)

# Show the results page
results_page()
