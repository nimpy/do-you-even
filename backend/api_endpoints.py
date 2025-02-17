import os
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from workout_processing import WorkoutProcessor

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
