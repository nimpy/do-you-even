import streamlit as st
from st_draggable_list import DraggableList
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, List
import pyperclip

load_dotenv()

# Configuration
API_URL = "http://localhost:8080"
API_KEY = os.getenv("AUTH_TOKEN")

@st.cache_data()
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

@st.cache_data()
def fetch_aggregate_workout():
    """Fetch aggregate workout from the API"""
    headers = {
        "x-do-you-even-key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{API_URL}/get-aggregate-workout",
            headers=headers
        )
        response.raise_for_status()
        return response.json()["workout"]
    except Exception as e:
        st.error(f"Error fetching aggregate workout: {str(e)}")
        return None

@st.cache_data()
def fetch_suggested_location_and_workout_type():
    """Fetch suggested location and workout type from the API"""
    headers = {
        "x-do-you-even-key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{API_URL}/get-suggested-location-and-workout-type",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return {
            "location": data["suggested_location"],
            "workout_type": data["suggested_workout_type"]
        }
    except Exception as e:
        st.error(f"Error fetching suggestions: {str(e)}")
        return {
            "location": "Dok Noord",
            "workout_type": "lower"
        }

def format_date(date_str):
    """Format date string to a more readable format"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")

def display_workout(workout):
    """Display a single workout in a nice format"""
    date = format_date(workout["date"])
    location = workout.get("gym_location", "unknown location")
    workout_type = workout["workout_type"]
    
    with st.expander(f"🏋️‍♂️ {date} - {location}", expanded=True):
        st.write(f"**Type:** {workout_type}")
        
        for exercise in workout["exercises"]:
            st.markdown(f"#### {exercise['name']}")
            
            set_data = []
            for i, set_info in enumerate(exercise["sets"], 1):
                set_data.append({
                    "Set": i,
                    "Weight/Difficulty": set_info["difficulty"],
                    "Reps/Duration": set_info["reps"]
                })
            
            if set_data:
                st.table(set_data)
        
        st.markdown(f"**Workout Text:**\n```\n{workout['workout_text']}\n```")
        st.divider()

def format_exercise_for_doc(exercise: Dict) -> str:
    """Format a single exercise in Google Doc format"""
    name = exercise["name"]
    sets = exercise["sets"]
    
    # Get the difficulty (weight) from the first set if it exists and isn't "bodyweight"
    difficulty = sets[0]["difficulty"]
    difficulty_str = f" {difficulty}" if difficulty != "bodyweight" else ""
    
    # Join reps with commas
    reps_str = ", ".join(set_info["reps"] for set_info in sets)
    
    return f"{name}{difficulty_str} {reps_str}"

def generate_workout_text(exercises: List[Dict], location: str, workout_type: str) -> str:
    """Generate the complete workout text"""
    current_date = datetime.now().strftime("%Y%m%d")
    
    workout_lines = [f"{current_date} -- {location} -- {workout_type}"]
    workout_lines.extend(
        format_exercise_for_doc(exercise)
        for exercise in exercises
    )
    
    return "\n".join(workout_lines)

def prepare_draggable_exercises(exercises: List[Dict]) -> List[Dict]:
    """Prepare exercises for draggable list format"""
    return [
        {
            "id": str(i),
            "order": i,
            "name": exercise["name"],
            "data": exercise
        }
        for i, exercise in enumerate(exercises)
    ]

def main():
    st.set_page_config(
        page_title="Workout Tracker",
        page_icon="💪",
        layout="wide"
    )
    
    st.title("🏋️‍♂️ Workout Tracker")
    
    # Initialize session state
    if "workout_text" not in st.session_state:
        st.session_state.workout_text = ""
    if "selected_exercises" not in st.session_state:
        st.session_state.selected_exercises = {}
    if "draggable_exercises" not in st.session_state:
        st.session_state.draggable_exercises = []
    
    tab1, tab2 = st.tabs(["Recent Workouts", "Create New Workout"])
    
    with tab1:
        if st.button("Fetch Recent Workouts"):
            # st.rerun()
        
            workouts = fetch_workouts()
            
            if not workouts:
                st.warning("No workouts found. Try refreshing the page.")
                return
            
            for workout in workouts:
                display_workout(workout)
    
    with tab2:
        st.header("Create New Workout")
        
        # Fetch suggestions for location and workout type
        suggestions = fetch_suggested_location_and_workout_type()
        
        # Fetch aggregate workout to get exercise list
        aggregate_workout = fetch_aggregate_workout()
        if not aggregate_workout:
            st.warning("Could not load exercises. Please try again.")
            return
        
        # Location and workout type selection
        col1, col2 = st.columns(2)
        
        with col1:
            # Map API location names to UI options
            location_mapping = {
                "Dok Noord": "gym (Dok Noord)",
                "Overpoort": "gym (Overpoort)",
                "at home": "gym (at home)"
            }
            
            location_options = ["gym (Dok Noord)", "gym (Overpoort)", "gym (at home)"]
            suggested_location_ui = location_mapping.get(suggestions["location"], "gym (Dok Noord)")
            default_location_index = location_options.index(suggested_location_ui)
            
            location = st.radio(
                "Select workout location:",
                location_options,
                index=default_location_index,
                horizontal=True
            )
        
        with col2:
            workout_type_options = ["upper", "lower", "full body"]
            suggested_workout_type = suggestions["workout_type"]
            default_workout_type_index = workout_type_options.index(suggested_workout_type) if suggested_workout_type in workout_type_options else 0
            
            workout_type = st.radio(
                "Select workout type:",
                workout_type_options,
                index=default_workout_type_index,
                horizontal=True
            )
        
        # Create checkboxes for exercises
        st.subheader("Select Exercises")
        
        # Create a checkbox for each exercise
        exercises = aggregate_workout["exercises"]
        selected_count = 0
        for exercise in exercises:
            key = f"exercise_{exercise['name']}"
            is_selected = st.checkbox(
                exercise["name"],
                key=key,
                value=st.session_state.selected_exercises.get(exercise["name"], False)
            )
            st.session_state.selected_exercises[exercise["name"]] = is_selected
            if is_selected:
                selected_count += 1
        
        # Show draggable list for selected exercises
        if selected_count > 0:
            st.subheader(f"Arrange {selected_count} Selected Exercises")
            
            # Prepare selected exercises for draggable list
            selected_exercises = [
                exercise for exercise in exercises
                if st.session_state.selected_exercises.get(exercise["name"], False)
            ]
            draggable_data = prepare_draggable_exercises(selected_exercises)
            
            # Display draggable list
            dragged_exercises = DraggableList(draggable_data, width="100%")
            
            # Generate button
            if st.button("Generate Workout Text"):
                # Get exercises in the dragged order
                ordered_exercises = [
                    item["data"] for item in dragged_exercises
                ]
                
                st.session_state.workout_text = generate_workout_text(
                    ordered_exercises,
                    location,
                    workout_type
                )
        
        # Display and copy text
        if st.session_state.workout_text:
            st.subheader("Workout Text")
            text_area = st.text_area(
                "Edit if needed:",
                st.session_state.workout_text,
                height=200
            )
            
            # Copy button
            if st.button("📋 Copy to Clipboard"):
                pyperclip.copy(text_area)
                st.success("Copied to clipboard!")

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
