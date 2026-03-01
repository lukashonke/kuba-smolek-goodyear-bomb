# Car & Tire Shop Finder

Streamlit app that searches for car repair shops, tire shops, and car dealers using Google Places API and exports results to Excel.

## Local Setup

1. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

2. Create `.env` from the template:
   ```
   cp .env.example .env
   ```
   Fill in your `GOOGLE_MAPS_API_KEY` and `APP_PASSWORD`.

3. Run:
   ```
   streamlit run app.py
   ```

## Streamlit Cloud Deployment

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Add secrets in the dashboard:
   - `GOOGLE_MAPS_API_KEY = "your_key"`
   - `APP_PASSWORD = "your_password"`
4. Deploy.
