import streamlit as st

# Define pages and their navigation logic
PAGES = {
    "Login": "login.py",
    "Main": "main.py",
    "Predictions": "predictions.py",
    "Results": "results.py",
    "Standings": "standings.py"
}

# Function to handle authentication
def authenticate():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

# Function to show the login page
def login():
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log in"):
        # Dummy authentication check
        if username == "user" and password == "password":  # Replace with actual logic
            st.session_state["authenticated"] = True
            st.success("Login successful! Redirecting...")
            st.session_state["page"] = "Main"  # Set page to Main after login
            st.rerun()  # Re-run the app to go to the Main page
        else:
            st.error("Invalid credentials. Please try again.")

# Function to show the main page after login
def main_page():
    if not st.session_state["authenticated"]:
        st.warning("Please log in first!")
        st.stop()  # Stop further execution until user is authenticated
    
    st.title("Main Page")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("View Predictions"):
            st.session_state["page"] = "Predictions"  # Set page to Predictions
            st.rerun()  # Rerun to go to predictions page
    
    with col2:
        if st.button("View Results"):
            st.session_state["page"] = "Results"  # Set page to Results
            st.rerun()  # Rerun to go to results page
    
    with col3:
        if st.button("View Standings"):
            st.session_state["page"] = "Standings"  # Set page to Standings
            st.rerun()  # Rerun to go to standings page

# Function to handle page access
def app():
    authenticate()  # Check authentication state

    if not st.session_state["authenticated"]:
        login()  # Show login page if not authenticated
    else:
        # Display the page based on session state
        page = st.session_state.get("page", "Main")  # Default to Main page if no page is set

        if page == "Main":
            main_page()
        elif page == "Predictions":
            # Code for predictions page
            st.title("Make Your Predictions")
            # Your prediction form logic here...
        elif page == "Results":
            # Code for results page
            st.title("Race Results")
            # Your results display logic here...
        elif page == "Standings":
            # Code for standings page
            st.title("Season Standings")
            # Your standings display logic here...
        else:
            st.error("Page not found!")

if __name__ == "__main__":
    app()
