# Health AI Backend

A FastAPI-based backend service for a health and nutrition AI application that provides personalized diet plans and meal logging functionality.

## Features

- **User Profile Management**: Retrieve user health information including physical stats
- **AI-Powered Diet Planning**: Generate personalized diet plans using LLaMA-4 Maverick model via Groq API
- **Meal Logging**: Log and track meals with AI nutritional analysis
- **Conversational AI**: Natural language interaction for health and nutrition queries
- **Indian/Gujarati Cuisine Focus**: Specialized in Indian dietary preferences and meal planning
- **MongoDB Integration**: Persistent storage for user data, diet plans, and meal logs
- **Structured AI Responses**: JSON-formatted responses for consistent data handling

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **MongoDB**: NoSQL database for data persistence
- **Pydantic**: Data validation and settings management
- **Python-dotenv**: Environment variable management
- **Groq API**: LLaMA-4 Maverick model for AI-powered responses
- **Requests**: HTTP library for API communication

## Prerequisites

- Python 3.8+
- MongoDB instance (local or cloud)
- Groq API account and API key
- Environment variables properly configured

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd health-ai-backend
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi pymongo python-dotenv pydantic uvicorn requests
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   MONGO_URI=mongodb://localhost:27017
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_ENDPOINT=https://api.groq.com/openai/v1/chat/completions
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Get User Information
```http
GET /user?id={user_id}
```
Retrieves user profile information including name, height, weight, age, gender, and body fat percentage.

**Parameters:**
- `id` (required): MongoDB ObjectId of the user

**Response:**
```json
{
  "name": "John Doe",
  "height": 175,
  "weight": 70,
  "age": 25,
  "gender": "male",
  "bfp": 15.5
}
```

### Get Diet Plan
```http
GET /diet?id={user_id}
```
Retrieves the AI-generated diet plan for a specific user.

**Parameters:**
- `id` (required): User ID as MongoDB ObjectId string

**Response:**
```json
{
  "id": "diet_document_id",
  "AI_Plan": "Detailed diet plan...",
  "user_id": "user_object_id"
}
```

### Get Meal Logs
```http
GET /meals?id={user_id}
```
Retrieves all logged meals for a specific user.

**Parameters:**
- `id` (required): User ID as ObjectId string

**Response:**
```json
{
  "id": "meal_document_id",
  "user_id": "user_object_id",
  "meal_logs": [
    {
      "meal_type": "breakfast",
      "items": ["oatmeal", "banana", "milk"],
      "timestamp": "2024-01-01T08:00:00Z"
    }
  ]
}
```

### AI Chat Interface
```http
POST /ai
```
Main endpoint for interacting with the AI assistant. Handles diet plan generation, meal logging, and general conversation.

**Request Body:**
```json
{
  "message": "I want to log my breakfast: eggs and toast",
  "user_id": "65f1a2b3c4d5e6f7g8h9i0j1"
}
```

**Response Types:**

**Diet Plan Generation:**
```json
{
  "message": "your diet has been created",
  "response_type": "diet_plan",
  "diet_plan": {
    "dailyNutrition": {
      "calories": 1850,
      "carbs": 260,
      "fats": 55,
      "protein": 110,
      "waterIntake": "4 liters"
    },
    "calorieDistribution": [
      { "category": "carbohydrates", "percentage": "50%" },
      { "category": "proteins", "percentage": "30%" },
      { "category": "fats", "percentage": "20%" }
    ],
    "goal": "fat loss",
    "dietPreference": "vegetarian",
    "workoutRoutine": [
      { "day": "Monday", "routine": "Cardio - 30 minutes" },
      { "day": "Tuesday", "routine": "Strength - 30 minutes" }
    ],
    "mealPlans": [
      {
        "day": "Monday",
        "totalCalories": 2200,
        "macronutrients": {
          "carbohydrates": 275,
          "proteins": 165,
          "fats": 49
        },
        "meals": [
          {
            "mealType": "breakfast",
            "items": [
              {
                "name": "Idli with Sambhar",
                "ingredients": ["rawa", "tomatoes", "dal", "spices", "onions"],
                "calories": 350
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Meal Logging:**
```json
{
  "response_type": "meal_logging",
  "message": "your meal has been logged",
  "mealType": "breakfast",
  "totalCalories": 620,
  "macronutrients": {
    "carbohydrates": 85,
    "proteins": 20,
    "fats": 25
  },
  "items": [
    {
      "name": "Poha",
      "calories": 300,
      "carbs": 40,
      "proteins": 8,
      "fats": 12
    }
  ]
}
```

**General Conversation:**
```json
{
  "message": "AI response to general health question",
  "response_type": "conversation"
}
```

## Database Schema

### Collections

1. **users**: User profile information
   - `_id`: ObjectId
   - `personal_info`: Object containing name, height, weight, age, gender, bfp

2. **diets**: AI-generated diet plans
   - `_id`: ObjectId
   - `user_id`: ObjectId reference to user
   - `AI_plan`: String containing the diet plan

3. **meals**: User meal logs
   - `_id`: ObjectId
   - `user_id`: ObjectId reference to user
   - `meal_log`: Array of meal entries

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid ObjectId format or request type
- **404 Not Found**: User, diet, or meals not found
- **500 Internal Server Error**: Database connection issues or unexpected errors

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
FastAPI automatically generates interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Dependencies

- `fastapi`: Web framework
- `pymongo`: MongoDB driver
- `pydantic`: Data validation
- `python-dotenv`: Environment management
- `bson`: MongoDB ObjectId handling
- `requests`: HTTP client for API communication

## LLM Module Functions

The `llm.py` module provides core AI functionality:

### `get_user_data_mongo(user_id)`
Retrieves user profile data from MongoDB including:
- Physical stats (height, weight, age, gender)
- Body fat percentage
- Personal information for AI personalization

### `get_structured_output(user_prompt, user_data)`
Processes user input through Groq AI API:
- **Model**: meta-llama/llama-4-maverick-17b-128e-instruct
- **Temperature**: 0.5 for consistent responses
- **Input**: User message + profile data
- **Output**: Structured JSON response

### `store_response_mongo(user_id, data)`
Stores AI responses in appropriate MongoDB collections:
- Diet plans → `diets` collection
- Meal logs → `meals` collection
- Handles upsert operations for data persistence

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request