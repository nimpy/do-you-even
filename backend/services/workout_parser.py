from openai import OpenAI
import os
from datetime import datetime
from models import Workout, Exercise, Set, WorkoutType
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = """
Extract workout information into a structured format.

The workout text follows this format:
- First line contains date (YYYYMMDD) and workout type (gym or home)
- Following lines contain exercises with their sets
- Each set may include difficulty (weight, resistance) and reps
- For time-based exercises, use the time as reps
- For bodyweight exercises, use "bodyweight" as difficulty

Parse workout details including:
- date (as YYYY-MM-DD string, converted from YYYYMMDD format)
- workout_type (Either "upper", "lower", or "full body". Only use "full body" if there are exercises for both upper and lower body. This will rarely be the case. Abs (core) exercises are not included in the workout type.)
- gym_location (Either "Dok Noord", "Overpoort", "at home", or "other".)
- exercises list, each with:
  - name (string)
  - sets list, each with:
    - difficulty (string, include units like "kg" if present)
    - reps (string)
- workout_text (string, the original workout text)

For example, if the date is 20231229, convert it to "2023-12-29" in the output.
"""

def parse_workout_text(workout_text: str) -> Workout:
    """Parse a single workout text using OpenAI API"""
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": workout_text}
            ],
            response_format=Workout
        )
        
        # The completion is already a Workout object
        workout = completion.choices[0].message.parsed
        
        # Determine gym location based on text or date
        workout.determine_gym_location()
        
        print(f"Parsed workout: {workout}")  # TODO: remove

        return workout
        
    except Exception as e:
        print(f"Error parsing workout text: {str(e)}")
        print(f"Problematic text: {workout_text}")
        raise