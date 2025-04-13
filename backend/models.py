from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class GymLocation(str, Enum):
    DOK_NOORD = "Dok Noord"
    OVERPOORT = "Overpoort"
    HOME = "at home"
    OTHER = "other"

class WorkoutType(str, Enum):
    UPPER = "upper"
    LOWER = "lower"
    FULL_BODY = "full body"

class Set(BaseModel):
    difficulty: str  # e.g., "20kg", "level 3", "bodyweight"
    reps: str       # e.g., "20", "1:30" (for time-based), "failure"

class Exercise(BaseModel):
    name: str
    sets: List[Set]

class Workout(BaseModel):
    date: str
    workout_type: WorkoutType
    gym_location: GymLocation
    exercises: List[Exercise]
    workout_text: Optional[str] = None

    def determine_gym_location(self):
        """Determine gym location based on workout text or date"""
        # First check if we can determine location from workout text
        if self.workout_text:
            workout_text_lower = self.workout_text.lower()
            if GymLocation.DOK_NOORD.lower() in workout_text_lower:
                self.gym_location = GymLocation.DOK_NOORD
                return
            elif GymLocation.OVERPOORT.lower() in workout_text_lower:
                self.gym_location = GymLocation.OVERPOORT
                return
            
        # If no location found in text, fallback to date-based logic
        date_obj = datetime.strptime(self.date, '%Y-%m-%d')
        if date_obj.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            self.gym_location = GymLocation.OVERPOORT
        else:
            self.gym_location = GymLocation.DOK_NOORD