import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated

st.title("Season Standings")
st.markdown("Here is where you'll be able to see the standings for this season. Still under construction!")
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
