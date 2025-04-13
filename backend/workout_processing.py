import re
import os
import json
from typing import Optional, List, Tuple
from datetime import datetime, date
from models import Workout, Exercise, Set, WorkoutType
from services.google_docs import GoogleDocsClient
from services.workout_parser import parse_workout_text

class WorkoutProcessor:
    def __init__(self):
        self.docs_client = GoogleDocsClient()
        self.cache_file = "workout_cache.json"

    def _extract_date(self, workout_text: str) -> Optional[datetime]:
        """Extract date from workout text in format YYYYMMDD"""
        date_match = re.search(r'(\d{8})', workout_text)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%Y%m%d')
            except ValueError:
                return None
        return None

    def _split_into_workouts(self, content: str) -> List[Tuple[datetime, str]]:
        """Split content into individual workout texts and their dates"""
        # Split by blank lines
        workout_sections = [
            section.strip()
            for section in content.split('\n\n')
            if section.strip()
        ]

        # Process only sections that start with a date
        dated_workouts = []
        for section in workout_sections:
            date = self._extract_date(section)
            if date:
                dated_workouts.append((date, section))

        # Sort by date, newest first
        return sorted(dated_workouts, key=lambda x: x[0], reverse=True)

    def _get_cache_data(self) -> Optional[dict]:
        """Read cache data from file if it exists and is from today"""
        if not os.path.exists(self.cache_file):
            return None
            
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache was created today
            cache_date = datetime.fromisoformat(cache_data.get('timestamp', ''))
            today = datetime.now().date()
            
            if cache_date.date() == today:
                return cache_data
            return None
        except Exception as e:
            print(f"Error reading cache: {str(e)}")
            return None
            
    def _save_to_cache(self, workouts: List[Workout]):
        """Save workouts to cache file with current timestamp"""
        try:
            # Convert workouts to dict for JSON serialization
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'workouts': [workout.model_dump() for workout in workouts]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")

    async def fetch_latest_workout(self) -> Optional[Workout]:
        """
        Fetch workouts from Google Docs and return the latest one
        """
        try:
            # Check cache first
            cache_data = self._get_cache_data()
            if cache_data and cache_data.get('workouts'):
                # Use the first (latest) workout from cache
                workout_dict = cache_data['workouts'][0]
                return Workout.model_validate(workout_dict)
                
            # Fetch document content
            content = self.docs_client.read_document()
            if not content:
                print("No content found in document")
                return None

            # Split into workouts and get the latest one
            dated_workouts = self._split_into_workouts(content)
            if not dated_workouts:
                print("No valid workouts found in content")
                return None

            # Take the most recent workout and parse it
            _, latest_workout_text = dated_workouts[0]
            latest_workout = parse_workout_text(latest_workout_text)
            
            # Cache this workout
            self._save_to_cache([latest_workout])

            return latest_workout

        except Exception as e:
            print(f"Error in fetch_latest_workout: {str(e)}")
            return None

    async def fetch_last_n_workouts(self, n: int = 4) -> List[Workout]:
        """
        Fetch the last n workouts from Google Docs
        """
        try:
            # Check cache first
            cache_data = self._get_cache_data()
            if cache_data and cache_data.get('workouts'):
                # Get up to n workouts from cache
                cached_workouts = [Workout.model_validate(w) for w in cache_data['workouts'][:n]]
                if len(cached_workouts) >= n:
                    return cached_workouts
            
            # Fetch document content
            content = self.docs_client.read_document()
            if not content:
                print("No content found in document")
                return []

            # Split into workouts
            dated_workouts = self._split_into_workouts(content)
            if not dated_workouts:
                print("No valid workouts found in content")
                return []

            # Take the n most recent workouts and parse them
            workouts = []
            for _, workout_text in dated_workouts[:n]:
                try:
                    workout = parse_workout_text(workout_text)
                    workouts.append(workout)
                except Exception as e:
                    print(f"Error parsing workout: {str(e)}")
                    continue
            
            # Cache these workouts
            if workouts:
                self._save_to_cache(workouts)

            return workouts

        except Exception as e:
            print(f"Error in fetch_last_n_workouts: {str(e)}")
            return []

    async def create_aggregate_workout(self) -> Optional[Workout]:
        """
        Create a workout containing all exercises from the last 4 workouts,
        using the most recent values for each exercise
        """
        try:
            # Get last 4 workouts (these will be from cache if available)
            recent_workouts = await self.fetch_last_n_workouts(4)
            if not recent_workouts:
                return None

            # Dictionary to store most recent exercise data
            # Key: exercise name, Value: (exercise object, date of workout)
            latest_exercises = {}

            # Process workouts from newest to oldest
            for workout in recent_workouts:
                for exercise in workout.exercises:
                    # Only keep this exercise if we haven't seen it before
                    if exercise.name not in latest_exercises:
                        latest_exercises[exercise.name] = exercise

            # Create new workout with all exercises
            aggregate_workout = Workout(
                date=recent_workouts[0].date,  # Use most recent date  # TODO: it should be today's date?
                exercises=list(latest_exercises.values()),
                workout_type=recent_workouts[0].workout_type,
                gym_location=recent_workouts[0].gym_location
            )
            
            # Set gym location based on date
            aggregate_workout.determine_gym_location()

            return aggregate_workout

        except Exception as e:
            print(f"Error creating aggregate workout: {str(e)}")
            return None

