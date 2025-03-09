import streamlit as st
import pandas as pd
import requests

# Check if the user is authenticated before showing any content
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first!")
    st.stop()  # Stop execution if not authenticated

st.title("Race Results & Scoring")

# Sample session state storage for predictions (until you move to blob storage)
if "predictions_df" not in st.session_state:
    st.session_state["predictions_df"] = pd.DataFrame(columns=["User", "Race", "Position", "Driver"])

# Hardcoded driver name dictionary
driver_names = {
    "max_verstappen": "Max Verstappen",
    "lawson": "Liam Lawson",
    "perez": "Sergio Perez",
    "hamilton": "Lewis Hamilton",
    "russell": "George Russell",
    "leclerc": "Charles Leclerc",
    "antonelli": "Kimi Antonelli",
    "sainz": "Carlos Sainz",
    "norris": "Lando Norris",
    "piastri": "Oscar Piastri",
    "ricciardo": "Daniel Ricciardo",
    "gasly": "Pierre Gasly",
    "ocon": "Esteban Ocon",
    "valtteri_bottas": "Valtteri Bottas",
    "alonso": "Fernando Alonso",
    "kevin_magnussen": "Kevin Magnussen",
    "stroll": "Lance Stroll",
    "zhou": "Zhou Guanyou",
    "tsunoda": "Yuki Tsunoda",
    "albon": "Alex Albon",
    "hulkenburg": "Nico Hulkenburg"
}

# Fetch the 2024 F1 race schedule using the Ergast API
@st.cache_data
def fetch_race_schedule():
    api_url = "https://ergast.com/api/f1/2024.json"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        races = data["MRData"]["RaceTable"]["Races"]
        race_schedule = {race["raceName"]: race["round"] for race in races}
        return race_schedule
    else:
        st.error("Failed to fetch race schedule.")
        return {}

# Fetch actual race results using the Ergast API
def fetch_race_results(season, round_number):
    api_url = f"https://ergast.com/api/f1/{season}/{round_number}/results.json"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        results = data["MRData"]["RaceTable"]["Races"][0]["Results"]
        return {entry["Driver"]["driverId"]: int(entry["position"]) for entry in results}
    else:
        st.error("Failed to fetch race results.")
        return {}

# Get the race schedule
race_schedule = fetch_race_schedule()

if race_schedule:
    # Select race
    selected_race = st.selectbox("Select a race:", list(race_schedule.keys()))

    # Retrieve predictions for the selected race
    predictions = st.session_state["predictions_df"]
    race_predictions = predictions[predictions["Race"] == selected_race].copy()

    # Fetch actual results for the selected race
    round_number = race_schedule[selected_race]
    actual_results = fetch_race_results(2024, round_number)

    if actual_results:
        # Merge predictions with actual results if predictions exist
        if not race_predictions.empty:
            race_predictions["Actual Position"] = race_predictions["Driver"].map(actual_results)
            race_predictions["Driver Name"] = race_predictions["Driver"].map(driver_names)
            race_predictions["Points"] = race_predictions.apply(
                lambda row: 10 - abs(row["Actual Position"] - row["Position"]) if pd.notna(row["Actual Position"]) else 0,
                axis=1
            )

        # Display actual race results
        st.subheader(f"Race Results for {selected_race}")
        race_results_df = pd.DataFrame({
            "Driver": [driver_names.get(driver_id, "Unknown") for driver_id in actual_results.keys()],
            "Actual Position": list(actual_results.values())
        })

        # Display the results
        st.dataframe(race_results_df.sort_values(by=["Actual Position"], ascending=True), use_container_width=True)

        # If there are predictions, display them along with scores
        if not race_predictions.empty:
            st.subheader("User Predictions & Points")
            st.dataframe(race_predictions[["User", "Driver Name", "Actual Position", "Points"]].sort_values(by=["User", "Points"], ascending=[True, False]), use_container_width=True)

        # Save results to session state (for now)
        st.session_state["race_results"] = race_predictions
    else:
        st.write("Actual results data is not available for the selected race.")
else:
    st.write("Race schedule is currently unavailable.")