import os
import requests
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT")
MONGO_URI = os.getenv("MONGO_URI")

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ---------- Fetch User Data ----------
def get_user_data_mongo(user_id: int):
    try:
      client = MongoClient(MONGO_URI)
      db = client["health_ai"]
      collection = db["users"]
      
      # Convert string ID to ObjectId
      object_id = ObjectId(user_id)
      user_data = collection.find_one({"_id": object_id})
      
      if not user_data or "personal_info" not in user_data:
          raise ValueError("User not found or profile not completed")
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
        raise ValueError(f"Error fetching user data: {e}")
    
# ---------- Get Structured Response from Groq API ----------

def get_structured_output(user_prompt, user_data):
    system_prompt = f"""
    You are an AI nutrition assistant. Your job is to handle three types of user queries:

---

### 1. If the user asks for a **diet plan**, behave like a professional **diet planning assistant**. In this case:

- Return a **valid JSON** in this format:

{{
  "message": "your diet has been created",
  "response_type": "diet_plan",
  "diet_plan": {{
    "dailyNutrition": {{
      "calories": 1850,
      "carbs": 260,
      "fats": 55,
      "protein": 110,
      "waterIntake": "4 liters"
    }},
    "calorieDistribution": [
      {{ "category": "carbohydrates", "percentage": "50%" }},
      {{ "category": "proteins", "percentage": "30%" }},
      {{ "category": "fats", "percentage": "20%" }}
    ],
    "goal": "<User goal here (e.g., fat loss)>",
    "dietPreference": "<User diet preference (e.g., vegetarian, vegan)>",
    "workoutRoutine": [
      {{ "day": "Monday", "routine": "Cardio - 30 minutes" }},
      {{ "day": "Tuesday", "routine": "Strength - 30 minutes" }},
      {{ "day": "Wednesday", "routine": "Yoga - 30 minutes" }},
      {{ "day": "Thursday", "routine": "Cycling - 45 minutes" }},
      {{ "day": "Friday", "routine": "HIIT - 20 minutes" }},
      {{ "day": "Saturday", "routine": "Walk - 60 minutes" }},
      {{ "day": "Sunday", "routine": "Rest or light stretching" }}
    ],
    "mealPlans": [
      {{
        "day": "Monday",
        "totalCalories": 2200,
        "macronutrients": {{
          "carbohydrates": 275,
          "proteins": 165,
          "fats": 49
        }},
        "meals": [
          {{
            "mealType": "breakfast",
            "items": [
              {{
                "name": "Idli with Sambhar",
                "ingredients": ["rawa", "tomatoes", "dal", "spices", "onions"],
                "calories": 350
              }}
              // More items
            ]
          }}
          // Other meals
        ]
      }}
      // Repeat for all 7 days
    ]
  }}
}}

- Use this data from the database:
  - Height: {user_data['height']} cm
  - Weight: {user_data['weight']} kg
  - Age: {user_data['age']} years
  - Gender: {user_data['gender']}
  - Body Fat %: {user_data['bfp']}%

- Extract from prompt:
  - Goal, Budget, Activity Level, Allergies, Calorie target, etc.

- Meals must be Indian/Gujarati. Avoid non-veg for vegetarians and dairy for vegans. Include ingredients and calories.

- **No markdown or explanations. Only valid JSON. Avoid units.**

---

### 2. If the user describes a **meal they've eaten**, act as a **meal logging nutritionist**. In this case:

Return JSON in this format:

{{
  "response_type": "meal_logging",
  "message": "your meal has been logged",
  "mealType": "<breakfast/lunch/dinner/snack>",
  "totalCalories": 620,
  "macronutrients": {{
    "carbohydrates": 85,
    "proteins": 20,
    "fats": 25
  }},
  "items": [
    {{
      "name": "Poha",
      "calories": 300,
      "carbs": 40,
      "proteins": 8,
      "fats": 12
    }}
    // more items
  ]
}}

- Use average serving sizes.
- Meals should be Indian/Gujarati.
- Avoid units like "g" or "ml"—use only numbers.
- **Return only valid JSON. No markdown, no commentary.**

---

### 3. If the user is just chatting and not asking for a diet plan or meal logging, respond as a **normal AI assistant**.

Return:

{{
  "message": "<Your response here>",
  "response_type": "conversation"
}}

- This means the prompt is not related to diet planning or meal logging.
- Do **not** include any other keys or schemas.

---

⚠️ Rules:
- Only output JSON.
- No markdown, no commentary, no backticks.
- Output must be directly parsable.

---
    """
    
    payload = {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "temperature": 0.5,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    response = requests.post(GROQ_ENDPOINT, headers=HEADERS, json=payload)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("Failed to parse JSON. Raw content:\n", content)
        raise
    
# ---------- Logging ----------
def store_response_mongo(user_id: int, data: dict):
    client = MongoClient(MONGO_URI)
    db = client["health_ai"]
    collection = db["users"]
    diets_collection = db["diets"]
    meals_collection = db["meals"]
    # Check if user exists
    user_id = ObjectId(user_id)
    user = collection.find_one({"_id": user_id})
    if not user:
        raise ValueError(f"No user found with ID {user_id}")
    
    if data["response_type"] == "diet_plan":
        diets_collection.update_one(
            {"user_id": user_id},
            {"$set": {"AI_plan": data}},
            upsert=True
        )
    elif data["response_type"] == "meal_logging":
        meals_collection.update_one(
            {"user_id": user_id},
            {"$push": {"meal_log": data}},
            upsert=True
        )
    
    client.close()