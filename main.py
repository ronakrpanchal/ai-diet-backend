from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
from llm import get_structured_output, store_response_mongo, get_user_data_mongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()

# Chat Request Body
class ChatRequest(BaseModel):
    message: str
    user_id: str

# ---------------------------
# GET /user?id=
# ---------------------------
@app.get("/user")
def get_user(id: str = Query(..., description="MongoDB ObjectId of the user")):
    try:
        client = MongoClient(MONGO_URI)
        db = client["health_ai"]
        collection = db["users"]
        
        # Convert string ID to ObjectId
        object_id = ObjectId(id)
        user_data = collection.find_one({"_id": object_id})
        
        if not user_data or "personal_info" not in user_data:
            raise HTTPException(status_code=404, detail="User not found or profile not completed")
        
        info = user_data["personal_info"]
        return {
            "name": info["name"],
            "height": info["height"],
            "weight": info["weight"],
            "age": info["age"],
            "gender": info["gender"],
            "bfp": info["bfp"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# GET /diet?id=
# ---------------------------

@app.get("/diet")
def get_diet(id: str = Query(..., description="User ID as MongoDB ObjectId string")):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["diets"]

    diet_data = collection.find_one({"user_id": object_id})
    if not diet_data:
        raise HTTPException(status_code=404, detail="Diet not found")
    else:
        return {
            "id": str(diet_data["_id"]),
            "AI_Plan": diet_data["AI_plan"],
            "user_id": str(diet_data["user_id"])
        }
    
    
@app.get("/meals")
def get_meals(id: str = Query(..., description="User ID (ObjectId string)")):
    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["meals"]

    try:
        user_object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    meal_data = collection.find_one({"user_id": user_object_id})
    if not meal_data:
        raise HTTPException(status_code=404, detail="Meals not found")

    meal_logs = meal_data.get("meal_log", [])
    if not meal_logs:
        raise HTTPException(status_code=404, detail="No meals logged")

    return {
        "id": str(meal_data["_id"]),
        "user_id": str(meal_data["user_id"]),
        "meal_logs": meal_logs
    }

# ---------------------------
# POST /ai - Combined endpoint for diet plans and meal logging
# ---------------------------
@app.post("/ai")
def health_ai(request: ChatRequest):
    try:
        user_id = request.user_id
        user_prompt = request.message
        user_data = get_user_data_mongo(user_id)
        response = get_structured_output(user_prompt, user_data)
        if response["response_type"] == "diet_plan":
            store_response_mongo(user_id, response)
            return {
                "message": response["message"],
                "diet_plan": response["diet_plan"]
            }
        elif response["response_type"] == "meal_logging":
            meal_type = response["mealType"]
            user_meals = response["items"]
            store_response_mongo(user_id, response)
            return {
                "message": response["message"],
                "meal_log": {
                    "meal_type": meal_type,
                    "user_meals": user_meals
                }
            }
        elif response["response_type"] == "conversation":
            return {
                "message": response["message"]
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid request_type. Must be 'diet_plan' or 'meal_log'")

    except ValueError as ve:
        # This is for missing user in DB
        raise HTTPException(status_code=404, detail=str(ve))

    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")