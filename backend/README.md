# 1. Navigate to the backend folder

cd backend

# 2. Create virtual environment (only once)

py -m venv venv

# 3. Activate virtual environment

venv\Scripts\activate

# 4. Install dependencies from requirements.txt

pip install -r requirements.txt

# 5. Run your FastAPI server

uvicorn LoginPage:app --reload --host 0.0.0.0
