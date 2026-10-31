# Deploying StartupPulse (free: Render for the API, Streamlit Community Cloud for the UI)
1. `python3 export_data.py` (Postgres up) -> creates data/startups.csv
2. In your src/classify.py, replace the DB_URL line and load_data() with the versions in this folder's src/classify.py
3. Push the folder to GitHub
4. Render: New > Blueprint > pick the repo (render.yaml). Copy the generated STARTUPPULSE_API_KEY.
5. Streamlit Cloud: New app > repo, main file `ui/app.py`, Secrets:
   STARTUPPULSE_API_URL = "https://<your-service>.onrender.com"
   STARTUPPULSE_API_KEY = "<the key from Render>"
