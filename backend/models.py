from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class GymLocation(str, Enum):
    DOK_NOORD = "dok noord"
    OVERPOORT = "overpoort"
    OTHER = "other"

class WorkoutType(str, Enum):
    GYM = "gym"
    HOME = "at home"

class Set(BaseModel):
    difficulty: str  # e.g., "20kg", "level 3", "bodyweight"
    reps: str       # e.g., "20", "1:30" (for time-based), "failure"

class Exercise(BaseModel):
    name: str
    sets: List[Set]

class Workout(BaseModel):
    date: str
    workout_type: WorkoutType
    gym_location: Optional[GymLocation] = None
    exercises: List[Exercise]

    def determine_gym_location(self):
        """Determine gym location based on date (weekend = Overpoort, weekday = Dok Noord)"""
        if self.workout_type == WorkoutType.GYM:
            # Convert string date to datetime for weekday check
            date_obj = datetime.strptime(self.date, '%Y-%m-%d')
            if date_obj.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                self.gym_location = GymLocation.OVERPOORT
            else:
                self.gym_location = GymLocation.DOK_NOORD