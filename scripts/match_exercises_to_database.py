#!/usr/bin/env python3
"""
Exercise Matching Script

This script fetches workout data, extracts unique exercises, matches them to allExercises.json
using AI, and creates a comprehensive exercise database with location and workout type information.
"""

import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict, Counter
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuration
API_URL = "http://localhost:8080"
API_KEY = os.getenv("AUTH_TOKEN")

# My exercise context for better AI matching
EXERCISE_CONTEXT = {
    "Achilles tendon on leg press": "This is a calf raise exercise performed on the leg press machine, targeting the calves/Achilles tendon",
    "hip thrust velika": "This is a hip thrust exercise with heavy weight ('velika' means large/heavy)",
    "abs": "If it just says abs, it's the following exercise: It's a legs-only ab exercise. You lie on your back with your arms resting by your sides. With your legs starting in a 90-90 tabletop bend, you straighten one leg out completely and lower it until it's parallel to the floor. Once that leg is fully extended and straight, you bring it back to the start and switch to the other leg.",
    "outer glutes (sirenje nogu)": "This is a glute exercise targeting the outer glutes. You sit on the machine and spread your legs apart",
    "inner thigh": "Adductor exercise targeting inner thigh muscles",
    "hammer strength hamstring curl": "This is a hamstring curl exercise performed while laying on your belly",
}

class ExerciseMatch(BaseModel):
    """Pydantic model for exercise matching response"""
    my_name: str
    database_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str

class ExerciseMatchingResponse(BaseModel):
    """Pydantic model for the complete AI response"""
    matches: List[ExerciseMatch]

def fetch_all_workouts():
    """Fetch all workout data from the API"""
    headers = {
        "x-do-you-even-key": API_KEY
    }
    
    try:
        # For now, we'll use the last N workouts endpoint
        # You can modify this to fetch more workouts if needed
        response = requests.get(
            f"{API_URL}/get-last-n-workouts?n=20",  # Increase N as needed
            headers=headers
        )
        response.raise_for_status()
        return response.json()["workouts"]
    except Exception as e:
        print(f"Error fetching workouts: {str(e)}")
        return []

def extract_exercises_from_workouts(workouts):
    """Extract unique exercises and their usage context from workouts"""
    exercise_usage = defaultdict(lambda: {
        'frequency': 0,
        'locations': set(),
        'workout_types': set(),
        'dates': []
    })
    
    for workout in workouts:
        date = workout['date']
        location = workout.get('gym_location', 'unknown')
        workout_type = workout.get('workout_type', 'unknown')
        
        for exercise in workout['exercises']:
            name = exercise['name']
            exercise_usage[name]['frequency'] += 1
            exercise_usage[name]['locations'].add(location)
            exercise_usage[name]['workout_types'].add(workout_type)
            exercise_usage[name]['dates'].append(date)
    
    # Convert sets to lists for JSON serialization
    for name in exercise_usage:
        exercise_usage[name]['locations'] = list(exercise_usage[name]['locations'])
        exercise_usage[name]['workout_types'] = list(exercise_usage[name]['workout_types'])
    
    return dict(exercise_usage)

def load_all_exercises_database():
    """Load the allExercises.json database"""
    with open('../allExercises.json', 'r') as f:
        data = json.load(f)
        return data['data']['allExercises']

def extract_exercise_names_for_ai(all_exercises):
    """Extract just the exercise names for AI matching"""
    return [exercise['name'] for exercise in all_exercises]

def create_ai_matching_prompt(my_exercises, database_exercises):
    """Create a prompt for AI to match exercises"""
    my_exercise_list = "\n".join([f"- {name}" for name in my_exercises])
    
    # Add context for exercises that have clarifications
    context_info = ""
    exercises_with_context = []
    for exercise in my_exercises:
        if exercise in EXERCISE_CONTEXT:
            exercises_with_context.append(f"- {exercise}: {EXERCISE_CONTEXT[exercise]}")
    
    if exercises_with_context:
        context_info = f"""

IMPORTANT CONTEXT FOR MY EXERCISES:
{chr(10).join(exercises_with_context)}

Please use this context when matching these specific exercises.
"""
    
    prompt = f"""
I need you to match my workout exercises to the closest exercises in a reference database.

MY EXERCISES ({len(my_exercises)} total):
{my_exercise_list}{context_info}

REFERENCE DATABASE ({len(database_exercises)} exercises available):
The database contains exercises like: {', '.join(database_exercises[:20])}... (and {len(database_exercises)-20} more)

For each of my exercises, find the best match from the database and provide:
1. my_name: The original exercise name from my list
2. database_name: The closest matching exercise name from the database
3. confidence: A score from 0.0 to 1.0 indicating match quality
4. reasoning: Brief explanation of why this match was chosen

Guidelines:
- Look for exact matches first
- Consider synonyms and variations (e.g., "pushup" vs "push-up")
- Consider equipment variations (e.g., "dumbbell curl" vs "barbell curl")
- Use the provided context information for better matching
- If no good match exists, choose the closest one but give it a low confidence score
- Be consistent with similar exercise names
"""
    return prompt

def call_ai_for_matching(prompt, my_exercises):
    """Call OpenAI API for exercise matching using structured output"""
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are an expert fitness trainer who specializes in matching exercise names to a standardized database. Always provide matches for ALL exercises in the user's list."},
                {"role": "user", "content": prompt}
            ],
            response_format=ExerciseMatchingResponse
        )
        
        # The completion is already parsed into our Pydantic model
        matching_response = completion.choices[0].message.parsed
        
        # Convert to dictionary format for easier processing
        matches = {}
        for match in matching_response.matches:
            matches[match.my_name] = {
                'database_name': match.database_name,
                'confidence': match.confidence,
                'reasoning': match.reasoning
            }
        
        return matches
        
    except Exception as e:
        print(f"Error calling AI for matching: {str(e)}")
        # Return empty matches as fallback
        return {name: {
            'database_name': name,
            'confidence': 0.5,
            'reasoning': 'AI matching failed, using original name'
        } for name in my_exercises}

def determine_workout_types_from_muscle_groups(exercise_data):
    """Determine workout types (upper/lower/full body) based on muscle groups"""
    primary_muscles = exercise_data.get('primaryMuscles', [])
    secondary_muscles = exercise_data.get('secondaryMuscles', [])
    all_muscles = primary_muscles + secondary_muscles
    
    # Define muscle group mappings
    upper_muscles = {
        'chest', 'shoulders', 'triceps', 'biceps', 'lats', 'middle back', 
        'lower back', 'traps', 'forearms', 'rear delts', 'front delts'
    }
    
    lower_muscles = {
        'quadriceps', 'hamstrings', 'glutes', 'calves', 'hip flexors',
        'adductors', 'abductors', 'tibialis anterior'
    }
    
    core_muscles = {
        'abs', 'obliques', 'lower back'  # lower back can be both core and upper
    }
    
    # Check which muscle groups are involved
    has_upper = any(muscle.lower() in upper_muscles for muscle in all_muscles)
    has_lower = any(muscle.lower() in lower_muscles for muscle in all_muscles)
    has_core = any(muscle.lower() in core_muscles for muscle in all_muscles)
    
    workout_types = []
    
    if has_upper and has_lower:
        workout_types.append('full body')
    elif has_upper:
        workout_types.append('upper')
    elif has_lower:
        workout_types.append('lower')
    
    # Core exercises can be part of any workout type
    if has_core:
        if not workout_types:  # If it's only core
            workout_types = ['upper', 'lower', 'full body']
        elif 'full body' not in workout_types:
            # Add the missing workout type for core exercises
            if 'upper' in workout_types:
                workout_types.append('lower')
            elif 'lower' in workout_types:
                workout_types.append('upper')
    
    return workout_types if workout_types else ['full body']  # Default fallback

def determine_gym_locations(exercise_data, my_usage):
    """Determine gym availability based on equipment and usage"""
    equipment = exercise_data.get('equipment', [])
    if isinstance(equipment, str):
        equipment = [equipment]
    
    # Equipment that's typically only available at gyms
    gym_only_equipment = {
        'cable', 'machine', 'barbell', 'smith machine', 'leg press',
        'lat pulldown', 'seated row', 'leg extension', 'leg curl',
        'chest press machine', 'shoulder press machine', 'hack squat'
    }
    
    # Equipment that can be used at home
    home_equipment = {
        'bodyweight', 'dumbbell', 'resistance band', 'kettlebell',
        'pull-up bar', 'yoga mat', 'stability ball'
    }
    
    # Check if exercise requires gym-only equipment
    requires_gym = any(
        any(gym_eq in eq.lower() for gym_eq in gym_only_equipment)
        for eq in equipment
    )
    
    # Check if exercise can be done at home
    can_do_at_home = any(
        any(home_eq in eq.lower() for home_eq in home_equipment)
        for eq in equipment
    ) or not equipment  # No equipment specified means likely bodyweight
    
    # Start with locations based on equipment
    locations = []
    
    if requires_gym:
        locations.extend(['Dok Noord', 'Overpoort'])
    
    if can_do_at_home:
        locations.append('at home')
    
    # If no equipment info, use my actual usage
    if not locations:
        my_locations = my_usage.get('locations', [])
        if my_locations:
            locations = my_locations
        else:
            # Default to all locations if no info available
            locations = ['Dok Noord', 'Overpoort', 'at home']
    
    # Remove duplicates and ensure we have at least one location
    locations = list(set(locations))
    if not locations:
        locations = ['Dok Noord', 'Overpoort', 'at home']
    
    return locations

def create_comprehensive_exercise_database(my_exercises, all_exercises, ai_matches):
    """Create the comprehensive exercise database"""
    # Create a lookup dictionary for the database exercises
    db_lookup = {exercise['name']: exercise for exercise in all_exercises}
    
    comprehensive_db = []
    
    for my_name, my_usage in my_exercises.items():
        # Get AI matching info
        match_info = ai_matches.get(my_name, {
            'database_name': my_name,
            'confidence': 0.5,
            'reasoning': 'No AI match found'
        })
        
        # Get database exercise info
        db_name = match_info['database_name']
        db_exercise = db_lookup.get(db_name, {})
        
        # Determine workout types and locations
        workout_types = determine_workout_types_from_muscle_groups(db_exercise)
        locations = determine_gym_locations(db_exercise, my_usage)
        
        # Create comprehensive entry
        entry = {
            'my_name': my_name,
            'database_name': db_name,
            'match_confidence': match_info['confidence'],
            'match_reasoning': match_info['reasoning'],
            'workout_types': workout_types,
            'location': locations,  # Renamed from available_at
            'my_usage': {
                'frequency': my_usage['frequency'],
                'locations_used': my_usage['locations'],
                'workout_types_used': my_usage['workout_types'],
                'dates': my_usage['dates']
            },
            'database_info': db_exercise
        }
        
        comprehensive_db.append(entry)
    
    return comprehensive_db

def save_results(comprehensive_db, filename='data/comprehensive_exercise_database.json'):
    """Save the comprehensive database to a JSON file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(comprehensive_db, f, indent=2, default=str)
    
    print(f"✅ Saved comprehensive exercise database to {filename}")

def print_summary(comprehensive_db):
    """Print a summary of the results"""
    print(f"\n📊 SUMMARY")
    print(f"=" * 50)
    print(f"Total unique exercises: {len(comprehensive_db)}")
    
    # Confidence distribution
    high_conf = sum(1 for ex in comprehensive_db if ex['match_confidence'] >= 0.8)
    med_conf = sum(1 for ex in comprehensive_db if 0.5 <= ex['match_confidence'] < 0.8)
    low_conf = sum(1 for ex in comprehensive_db if ex['match_confidence'] < 0.5)
    
    print(f"High confidence matches (≥0.8): {high_conf}")
    print(f"Medium confidence matches (0.5-0.8): {med_conf}")
    print(f"Low confidence matches (<0.5): {low_conf}")
    
    # Workout type distribution
    workout_type_counts = defaultdict(int)
    for ex in comprehensive_db:
        for wt in ex['workout_types']:
            workout_type_counts[wt] += 1
    
    print(f"\nWorkout type distribution:")
    for wt, count in workout_type_counts.items():
        print(f"  {wt}: {count} exercises")
    
    # Location distribution
    location_counts = defaultdict(int)
    for ex in comprehensive_db:
        for loc in ex['location']:
            location_counts[loc] += 1
    
    print(f"\nLocation availability:")
    for loc, count in location_counts.items():
        print(f"  {loc}: {count} exercises")
    
    # Most frequent exercises
    print(f"\nTop 10 most frequent exercises:")
    sorted_exercises = sorted(comprehensive_db, key=lambda x: x['my_usage']['frequency'], reverse=True)
    for i, ex in enumerate(sorted_exercises[:10], 1):
        print(f"  {i}. {ex['my_name']} ({ex['my_usage']['frequency']} times)")

def main():
    """Main function to run the exercise matching process"""
    print("🏋️‍♂️ Starting Exercise Matching Process...")
    
    # Step 1: Fetch workout data
    print("\n1️⃣ Fetching workout data from API...")
    workouts = fetch_all_workouts()
    if not workouts:
        print("❌ No workouts found. Exiting.")
        return
    print(f"✅ Found {len(workouts)} workouts")
    
    # Step 2: Extract exercises
    print("\n2️⃣ Extracting unique exercises...")
    my_exercises = extract_exercises_from_workouts(workouts)
    print(f"✅ Found {len(my_exercises)} unique exercises")
    
    # Step 3: Load database
    print("\n3️⃣ Loading exercise database...")
    all_exercises = load_all_exercises_database()
    print(f"✅ Loaded {len(all_exercises)} exercises from database")
    
    # Step 4: Prepare for AI matching
    print("\n4️⃣ Preparing AI matching...")
    database_names = extract_exercise_names_for_ai(all_exercises)
    prompt = create_ai_matching_prompt(list(my_exercises.keys()), database_names)
    
    # Step 5: Call AI for matching
    print("\n5️⃣ Calling AI for exercise matching...")
    ai_matches = call_ai_for_matching(prompt, list(my_exercises.keys()))
    print(f"✅ Received AI matches for {len(ai_matches)} exercises")
    
    # Step 6: Create comprehensive database
    print("\n6️⃣ Creating comprehensive exercise database...")
    comprehensive_db = create_comprehensive_exercise_database(my_exercises, all_exercises, ai_matches)
    print(f"✅ Created comprehensive database with {len(comprehensive_db)} entries")
    
    # Step 7: Save results
    print("\n7️⃣ Saving results...")
    save_results(comprehensive_db)
    
    # Step 8: Print summary
    print_summary(comprehensive_db)
    
    print(f"\n🎉 Exercise matching process completed successfully!")

if __name__ == "__main__":
    main() 