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
        user_predictions = utils.calculate_scores(user_predictions, race_results)
        all_scores = utils.get_all_user_scores(predictions_df[predictions_df['Race'] == race_location], race_results)
        # Find user's row
        user_row = all_scores[all_scores['Predictor'] == st.session_state.user].iloc[0]
        st.markdown(
            f"""**{race_results.loc[1,'Driver']}** won the actual race.
            You scored **{user_predictions.Points.sum()}** for this race,
            finished **{user_row['Place']}**<sup>{'st' if user_row['Place']==1 else 'nd' if user_row['Place']==2 else 'rd' if user_row['Place']==3 else 'th'}</sup>
            and earned **{user_row['Points']}** points.""",
            unsafe_allow_html=True
        )
        winners = all_scores.loc[all_scores.Score == all_scores.Score.max(), 'Predictor']
        if len(winners) > 1:
            st.markdown(
                f"""**{", ".join([winner for winner in winners])}** won this race, scoring **{all_scores.Score.max()}** each.
                The group average score was **{all_scores.Score.mean().round(1)}**.
                The group score variation was **{(all_scores.Score.std()/all_scores.Score.mean()*100).round(1)}\%**.""")
        else:
            st.markdown(
                f"""**{winners.values[0]}** won this race with **{all_scores.Score.max()}**.
                The group average score was **{all_scores.Score.mean().round(1)}**.
                The group score variation was **{(all_scores.Score.std()/all_scores.Score.mean()*100).round(1)}\%**.""")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Actual Race Results**")
            st.dataframe(race_results, width='stretch')
        with col2:
            st.markdown(f"**Your Results ({st.session_state.user})**")
            st.dataframe(user_predictions)
        with col3:
            st.markdown("**Group Prediction Results**")
            # Ensure all predictors are shown, even those with 0 points
            group_table = all_scores[['Place', 'Predictor', 'Score', 'Points']].set_index('Place')
            st.dataframe(group_table, use_container_width=True)

# Show the results page
results_page()
