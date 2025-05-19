from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
from llm import get_structured_output, store_response_mongo, get_user_data_mongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()

# Chat Request Body
class ChatRequest(BaseModel):
    message: str
    user_id: int

# ---------------------------
# GET /user?id=
# ---------------------------
@app.get("/user")
def get_user(id: int = Query(..., description="User ID")):    
    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["users"]
    user_data = collection.find_one({"_id": id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        return {
            "height": user_data["height"],
            "weight": user_data["weight"],
            "age": user_data["age"],
            "gender": user_data["gender"],
            "bfp": user_data["bfp"]
        }

# ---------------------------
# GET /diet?id=
# ---------------------------
@app.get("/diet")
def get_diet(id: int = Query(..., description="User ID")):
    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["diets"]
    diet_data = collection.find_one({"user_id": id})
    if not diet_data:
        raise HTTPException(status_code=404, detail="Diet not found")
    else:
        return {
            "id": str(diet_data["_id"]),
            "AI_Plan": diet_data["AI_plan"],
            "user_id": diet_data["user_id"]
        }
    
    
@app.get("/meals")
def get_meals(id: int = Query(..., description="User ID")):
    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["meals"]
    meal_data = collection.find_one({"user_id": id})
    if not meal_data:
        raise HTTPException(status_code=404, detail="Meals not found")
    else:
        meal_logs = meal_data.get("meal_log", [])
        if not meal_logs:
            raise HTTPException(status_code=404, detail="No meals logged")
        return {
            "id": str(meal_data["_id"]),
            "meal_logs":meal_logs,
            "user_id": meal_data["user_id"]
        }

# ---------------------------
# POST /health_ai - Combined endpoint for diet plans and meal logging
# ---------------------------
@app.post("/health_ai")
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