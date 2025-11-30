import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import utils
import plotly.graph_objects as go

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated


def standings_page():
    st.title("Season Standings")
    predictions_df = utils.read_predictions_from_s3()
    race_list, race_dict = utils.get_race_list()
    all_f1_points = pd.DataFrame()
    all_places = pd.DataFrame()
    for race in race_list:
        if race in predictions_df.Race.unique():
            race_results_dict = utils.get_race_results(race_dict[race])
            # If there are no official results yet for this race, skip it
            if not race_results_dict:
                continue
            race_results = pd.DataFrame([race_results_dict])
            race_results = race_results.T.rename(columns={0: 'Driver'})
            race_scores = utils.get_all_user_scores(predictions_df[predictions_df['Race'] == race], race_results)
            # F1 points table
            race_points = race_scores[['Predictor', 'Points']].set_index('Predictor').rename(columns={'Points': race})
            all_f1_points = pd.concat([all_f1_points, race_points], axis=1)
            # Place table for tiebreakers
            race_places = race_scores[['Predictor', 'Place']].set_index('Predictor').rename(columns={'Place': race})
            all_places = pd.concat([all_places, race_places], axis=1)
    all_f1_points = all_f1_points.fillna(0)
    all_places = all_places.fillna(0).astype(int)

    # Count number of P1 finishes for each user
    p1_counts = (all_places == 1).sum(axis=1)
    # Count number of podiums (P1, P2, P3) for each user
    podium_counts = ((all_places == 1) | (all_places == 2) | (all_places == 3)).sum(axis=1)

    # Build standings DataFrame with tiebreakers: Points, P1, Podiums
    standings_df = (
        all_f1_points.sum(axis=1)
        .to_frame('Points')
        .assign(P1=p1_counts, Podiums=podium_counts)
        .sort_values(
            by=['Points', 'P1', 'Podiums'],
            ascending=[False, False, False]
        )
        .reset_index()
        .rename(columns={'Predictor': 'User'})
    )

    # Set index as P1, P2, P3, ...
    standings_df.index = [f'P{i+1}' for i in range(len(standings_df))]

    # Order for legends: championship order
    champ_order = standings_df['User'].tolist()

    # Show race prediction scores (not F1 points) for each race
    all_scores = pd.DataFrame()
    for race in race_list:
        if race in predictions_df.Race.unique():
            race_results_dict = utils.get_race_results(race_dict[race])
            if not race_results_dict:
                continue
            race_results = pd.DataFrame([race_results_dict])
            race_results = race_results.T.rename(columns={0: 'Driver'})
            race_scores = utils.get_all_user_scores(predictions_df[predictions_df['Race'] == race], race_results)
            race_score_vals = race_scores[['Predictor', 'Score']].set_index('Predictor').rename(columns={'Score': race})
            all_scores = pd.concat([all_scores, race_score_vals], axis=1)
    all_scores = all_scores.fillna(0)


    st.info(f"""The season is {round(all_f1_points.shape[1]/len(race_list)*100,1)}% done. So far,
            **{standings_df.iloc[0,0]}** is leading with **{standings_df.iloc[0,1]}** points, ahead of
            {standings_df.iloc[1,0]} and {standings_df.iloc[2,0]} with {standings_df.iloc[1,1]}
            and {standings_df.iloc[2,1]} points, respectively.""")
    st.dataframe(standings_df, use_container_width=True)

    with st.expander(label="Full season points table", expanded=False):
        st.dataframe(all_f1_points.loc[champ_order], use_container_width=True)

    with st.expander(label="Full season race scores table", expanded=False):
        st.dataframe(all_scores.loc[champ_order], use_container_width=True)

    fig = go.Figure()
    cumsum_df = all_f1_points.cumsum(axis=1)
    for user in champ_order:
        if user in cumsum_df.index:
            row = cumsum_df.loc[user]
            fig.add_trace(go.Scatter(
                x=cumsum_df.columns,
                y=row.values,
                mode='lines+markers',
                name=user
            ))
    fig.update_layout(
        title="Cumulative Points Over Races",
        xaxis_title="Race",
        yaxis_title="Cumulative Points"
    )
    st.plotly_chart(fig)

    fig = go.Figure()
    for user in champ_order:
        if user in all_scores.index:
            row = all_scores.loc[user]
            # Only plot nonzero scores
            nonzero_mask = row.values != 0
            x_vals = all_scores.columns[nonzero_mask]
            y_vals = row.values[nonzero_mask]
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines+markers',
                name=user
            ))
    fig.update_layout(
        title="Individual Race Prediction Scores",
        xaxis_title="Race",
        yaxis_title="Race Score"
    )
    st.plotly_chart(fig)
        
standings_page()
