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
    for race in race_list:
        if race in predictions_df.Race.unique():
            race_results = pd.DataFrame([utils.get_race_results(race_dict[race])])
            race_results = race_results.T.rename(columns={0: 'Driver'})
            race_scores = utils.get_all_user_scores(predictions_df[predictions_df['Race'] == race], race_results)
            race_scores = race_scores[['Predictor', 'F1Points']].set_index('Predictor').rename(columns={'F1Points': race})
            all_f1_points = pd.concat([all_f1_points, race_scores], axis=1)
    all_f1_points = all_f1_points.fillna(0)
    cumsum_df = all_f1_points.cumsum(axis=1)
    places = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14']
    standings_df = (all_f1_points
                    .sum(axis=1)
                    .sort_values(ascending=False)
                    .reset_index()
                    .rename(columns={0: 'F1Points'}))
    standings_df.index = places
    st.info(f"""The season is {round(all_f1_points.shape[1]/len(race_list)*100,1)}\% done. So far,
            **{standings_df.iloc[0,0]}** is leading with **{standings_df.iloc[0,1]}** F1 points, ahead of
            {standings_df.iloc[1,0]} and {standings_df.iloc[2,0]} with {standings_df.iloc[1,1]}
            and {standings_df.iloc[2,1]} points, respectively.""")
    st.dataframe(standings_df)
   
    with st.expander(label="Full season F1 points table", expanded=False):
        st.dataframe(all_f1_points)

    fig = go.Figure()
    for i, row in cumsum_df.iterrows():
        fig.add_trace(go.Scatter(
            x=cumsum_df.columns,
            y=row.values,
            mode='lines+markers',
            name=i
        ))
    fig.update_layout(
        title="Cumulative F1 Points Over Races",
        xaxis_title="Race",
        yaxis_title="Cumulative F1 Points"
    )
    st.plotly_chart(fig)

    fig = go.Figure()
    for i, row in all_f1_points.iterrows():
        fig.add_trace(go.Scatter(
            x=all_f1_points.columns,
            y=row.values,
            mode='lines+markers',
            name=i
        ))
    fig.update_layout(
        title="Individual Race F1 Points",
        xaxis_title="Race",
        yaxis_title="Race F1 Points"
    )
    st.plotly_chart(fig)
        
standings_page()    

# # Extended dummy data for more races and users
# dummy_data = {
#     "User": ["Alice", "Bob", "Alice", "Charlie", "Bob", "Charlie", "Alice", "Bob", "Charlie", "Alice", "Bob", "Charlie"],
#     "Race": ["Bahrain", "Bahrain", "Bahrain", "Bahrain", "Saudi Arabia", "Saudi Arabia", "Australia", "Australia", "Australia", "Monaco", "Monaco", "Monaco"],
#     "Position": [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3],  # Predicted positions
#     "Driver": ["max_verstappen", "lewis_hamilton", "sergio_perez", "max_verstappen", "lewis_hamilton", "sergio_perez",
#                "max_verstappen", "lewis_hamilton", "sergio_perez", "max_verstappen", "lewis_hamilton", "sergio_perez"],
#     "Points": [10, 8, 6, 10, 8, 6, 10, 8, 6, 10, 8, 6]  # Points earned for predictions
# }

# # Convert dummy data into a DataFrame
# dummy_predictions_df = pd.DataFrame(dummy_data)

# # Store the dummy data in session state for testing (remove later when using real predictions)
# st.session_state["predictions_df"] = dummy_predictions_df

# # Function to calculate the total points for each user
# def calculate_season_points():
#     # Retrieve the predictions dataframe
#     predictions_df = st.session_state["predictions_df"]

#     # Calculate the total points for each user
#     total_points = predictions_df.groupby("User")["Points"].sum().reset_index()

#     # Sort by points in descending order
#     total_points = total_points.sort_values(by="Points", ascending=False)

#     return total_points

# # Function to get points by race for each user
# def points_by_race():
#     predictions_df = st.session_state["predictions_df"]
#     race_points = predictions_df.pivot_table(index="Race", columns="User", values="Points", aggfunc="sum", fill_value=0)
#     return race_points

# # Display the season standings (total points)
# total_points_df = calculate_season_points()

# # Show the standings table
# if not total_points_df.empty:
#     st.subheader("Leaderboard")
#     st.dataframe(total_points_df, use_container_width=True)
# else:
#     st.write("No predictions available for the season yet.")

# # Show a table of points per race for each user
# race_points_df = points_by_race()
# if not race_points_df.empty:
#     st.subheader("Points per Race")
#     st.dataframe(race_points_df, use_container_width=True)

# # Plot the cumulative season points for each user
# if not total_points_df.empty:
#     st.subheader("Cumulative Season Points")
    
#     # Create a cumulative sum of the points for each user
#     cumulative_points = race_points_df.cumsum(axis=0)
    
#     # Plotting the cumulative points for each user
#     fig, ax = plt.subplots(figsize=(10, 6))
#     cumulative_points.plot(kind="line", ax=ax, marker="o", linestyle="-")
#     ax.set_title("Cumulative Season Points by User")
#     ax.set_xlabel("Races")
#     ax.set_ylabel("Cumulative Points")
#     ax.legend(title="Users", bbox_to_anchor=(1.05, 1), loc='upper left')
    
#     st.pyplot(fig)
# else:
#     st.write("No race points data available yet.")
