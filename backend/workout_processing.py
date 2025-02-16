import re
from typing import Optional, List, Tuple
from datetime import datetime
from models import Workout
from services.google_docs import GoogleDocsClient
from services.workout_parser import parse_workout_text

class WorkoutProcessor:
    def __init__(self):
        self.docs_client = GoogleDocsClient()

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

    async def fetch_and_update_workouts(self) -> Optional[Workout]:
        """
        Fetch workouts from Google Docs and return the latest one
        """
        try:
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

            return latest_workout

        except Exception as e:
            print(f"Error in fetch_and_update_workouts: {str(e)}")
            return None