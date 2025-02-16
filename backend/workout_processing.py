import re
from datetime import datetime
from typing import Dict, List, Optional
from google_doc_communication import GoogleDocsClient

def parse_workout_data(content: str) -> List[Dict]:
    """Parse workout data from text content"""
    workouts = []
    days = re.split(r'\n\s*\n', content.strip())

    for day in days:
        lines = day.strip().split('\n')
        date_line = lines[0]
        date_match = re.search(r'(\d{8})', date_line)
        
        if date_match:
            date = date_match.group(1)
            # Convert date string to ISO format
            date_obj = datetime.strptime(date, '%Y%m%d')
            iso_date = date_obj.isoformat()
            
            location = "home" if "home" in date_line.lower() else "gym"
            
            exercises = []
            for exercise_line in lines[1:]:
                if not exercise_line.strip():  # Skip empty lines
                    continue
                    
                # Extract exercise name and details
                parts = exercise_line.split(' ')
                numbers = re.findall(r'[\d.]+', exercise_line)
                
                # Get everything before the first number as the exercise name
                exercise_name = ' '.join(parts[:next((i for i, p in enumerate(parts) if any(c.isdigit() for c in p)), len(parts))])
                
                exercises.append({
                    "name": exercise_name.strip(),
                    "sets": len(re.findall(r',', exercise_line)) + 1,
                    "reps_weights": numbers  # Raw numbers from the exercise line
                })
            
            workouts.append({
                "date": iso_date,
                "location": location,
                "exercises": exercises
            })
    
    return workouts

def fetch_and_update_workouts() -> Optional[Dict]:
    """
    Fetch workouts from Google Docs and return the latest workout
    """
    try:
        # Initialize Google Docs client
        client = GoogleDocsClient()
        
        # Fetch document content
        content = client.read_document()
        if not content:
            return None
            
        # Parse workouts
        workouts = parse_workout_data(content)
        if not workouts:
            return None
            
        # Sort workouts by date and get the latest
        latest_workout = sorted(workouts, key=lambda x: x["date"], reverse=True)[0]
        
        return latest_workout
        
    except Exception as e:
        print(f"Error processing workouts: {str(e)}")
        return None