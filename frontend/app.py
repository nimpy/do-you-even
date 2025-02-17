import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "http://localhost:8080"
API_KEY = os.getenv("AUTH_TOKEN")

def fetch_workouts():
    """Fetch last 4 workouts from the API"""
    headers = {
        "x-do-you-even-key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{API_URL}/get-last-n-workouts",
            headers=headers
        )
        response.raise_for_status()
        return response.json()["workouts"]
    except Exception as e:
        st.error(f"Error fetching workouts: {str(e)}")
        return []

def format_date(date_str):
    """Format date string to a more readable format"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")

def display_workout(workout):
    """Display a single workout in a nice format"""
    date = format_date(workout["date"])
    location = workout.get("gym_location", "unknown location")
    workout_type = workout["workout_type"]
    
    # Create expandable section for each workout
    with st.expander(f"🏋️‍♂️ {date} - {location}", expanded=True):
        st.write(f"**Type:** {workout_type}")
        
        # Display exercises in a structured way
        for exercise in workout["exercises"]:
            st.markdown(f"#### {exercise['name']}")
            
            # Create a table for sets
            set_data = []
            for i, set_info in enumerate(exercise["sets"], 1):
                set_data.append({
                    "Set": i,
                    "Weight/Difficulty": set_info["difficulty"],
                    "Reps/Duration": set_info["reps"]
                })
            
            if set_data:
                st.table(set_data)
        
        st.divider()

def main():
    st.set_page_config(
        page_title="Workout Tracker",
        page_icon="💪",
        layout="wide"
    )
    
    st.title("Do you even")
    
    # Add a refresh button
    if st.button("🔄 Refresh"):
        st.experimental_rerun()
    
    # Fetch and display workouts
    workouts = fetch_workouts()
    
    if not workouts:
        st.warning("No workouts found. Try refreshing the page.")
        return
    
    # Display each workout
    for workout in workouts:
        display_workout(workout)
    
    # Add some styling
    st.markdown("""
        <style>
        .stExpander {
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
