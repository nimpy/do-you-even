import os
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

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
def health(key: str = Depends(verify_key)) -> str:
    ret = {"status": "healthy", "version": VERSION}
    return JSONResponse(ret)


@router.post("/get-last-workout")
async def get_last_workout(key: str = Depends(verify_key)) -> str:

    # TODO remove dummy response
    response = {
        "workout": {
            "date": "2025-02-01T13:00:00",
            "workout_type": "strength",
            "exercises": [
                {
                    "exercise_name": "squat",
                    "sets": 3,
                    "reps": 5,
                    "weight": 100
                },
                {
                    "exercise_name": "bench press",
                    "sets": 3,
                    "reps": 5,
                    "weight": 100
                },
                {
                    "exercise_name": "deadlift",
                    "sets": 3,
                    "reps": 5,
                    "weight": 100
                }
            ]
        }
    }    

    
    return JSONResponse(response)

