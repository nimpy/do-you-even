import os
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from workout_processing import WorkoutProcessor
from datetime import datetime
from models import GymLocation, WorkoutType

router = APIRouter()
load_dotenv()

def verify_key(x_do_you_even_key: str | None = Header(default=None)):
    if not x_do_you_even_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    if x_do_you_even_key != os.getenv('AUTH_TOKEN'):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_do_you_even_key

VERSION = "20250201_1800"

@router.get("/health")
def health(key: str = Depends(verify_key)) -> JSONResponse:
    ret = {"status": "healthy", "version": VERSION}
    return JSONResponse(ret)

@router.get("/get-last-workout")
async def get_last_workout(key: str = Depends(verify_key)) -> JSONResponse:
    try:
        processor = WorkoutProcessor()
        latest_workout = await processor.fetch_latest_workout()
        
        if not latest_workout:
            raise HTTPException(
                status_code=404,
                detail="No workouts found or error fetching workouts"
            )
        
        # Convert the Pydantic model to dict, handling datetime serialization
        workout_dict = latest_workout.model_dump(mode='json')
        
        response = {
            "workout": workout_dict
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@router.get("/get-last-n-workouts")
async def get_last_n_workouts(
    n: int = 4,
    key: str = Depends(verify_key)
) -> JSONResponse:
    try:
        processor = WorkoutProcessor()
        workouts = await processor.fetch_last_n_workouts(n)
        
        if not workouts:
            raise HTTPException(
                status_code=404,
                detail="No workouts found or error fetching workouts"
            )
        
        # Convert the Pydantic models to dicts
        workout_dicts = [
            workout.model_dump(mode='json')
            for workout in workouts
        ]
        
        response = {
            "workouts": workout_dicts
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )



@router.get("/get-aggregate-workout")
async def get_aggregate_workout(key: str = Depends(verify_key)) -> JSONResponse:
    try:
        processor = WorkoutProcessor()
        aggregate_workout = await processor.create_aggregate_workout()
        
        if not aggregate_workout:
            raise HTTPException(
                status_code=404,
                detail="No workouts found or error creating aggregate workout"
            )
        
        # Convert the Pydantic model to dict
        workout_dict = aggregate_workout.model_dump(mode='json')
        
        response = {
            "workout": workout_dict,
            "metadata": {
                "description": "This workout combines all unique exercises from the last 4 workouts, using the most recent values for each exercise."
            }
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@router.get("/get-suggested-location-and-workout-type")
async def get_suggested_location_and_workout_type(key: str = Depends(verify_key)) -> JSONResponse:
    try:
        processor = WorkoutProcessor()
        
        # Determine suggested location based on current day
        current_date = datetime.now()
        is_weekend = current_date.weekday() >= 5
        
        # TODO: Take into account public holidays in Belgium
        suggested_location = GymLocation.OVERPOORT if is_weekend else GymLocation.DOK_NOORD
        
        # Determine suggested workout type based on last workout
        last_workout = await processor.fetch_latest_workout()
        suggested_workout_type = WorkoutType.LOWER  # Never skip the leg day bro
        
        if last_workout:
            if last_workout.workout_type == WorkoutType.UPPER:
                suggested_workout_type = WorkoutType.LOWER
            elif last_workout.workout_type == WorkoutType.LOWER:
                suggested_workout_type = WorkoutType.UPPER
            else:
                # If last workout was full body or something else, check second last
                last_n_workouts = await processor.fetch_last_n_workouts(2)
                if len(last_n_workouts) >= 2:
                    second_last_workout = last_n_workouts[1]
                    if second_last_workout.workout_type == WorkoutType.UPPER:
                        suggested_workout_type = WorkoutType.LOWER
                    elif second_last_workout.workout_type == WorkoutType.LOWER:
                        suggested_workout_type = WorkoutType.UPPER
                    # If second last is also not upper/lower, keep default
        
        response = {
            "suggested_location": suggested_location.value,
            "suggested_workout_type": suggested_workout_type.value
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )
