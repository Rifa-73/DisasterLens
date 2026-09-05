# DisasterLens

AI-powered flood detection and severity assessment platform. Users report flood incidents with a photo (and optionally audio/video), and the system runs the image through a trained deep learning model plus a generative AI assessment to estimate severity — helping emergency responders prioritize where help is needed most.

## How it works

1. A user uploads a photo of a flooded area, along with their location and an optional description, audio note, or video clip.
2. The image is analyzed by a custom-trained **U-Net segmentation model** that classifies each pixel (flooded building, flooded road, water, etc.) and computes a flood severity score.
3. The image is also sent to **Gemini AI** for a second, independent assessment — disaster type, likelihood, priority, and reasoning.
4. Everything is saved to a database and made available via API for a map/dashboard view.

## Tech stack

**Backend:** FastAPI, SQLAlchemy, SQLite
**Computer Vision / Deep Learning:** PyTorch, custom U-Net architecture trained on the FloodNet dataset
**Generative AI:** Google Gemini API
**Frontend:** React, Vite
**Mapping:** Leaflet + OpenStreetMap

## Project structure

```
DisasterLens/
├── app/                    # FastAPI backend
│   ├── main.py              # app entrypoint
│   ├── routers/              # API endpoints
│   ├── schemas/               # request/response data shapes
│   ├── models/                # database table definitions
│   ├── services/               # CV model + Gemini AI integration
│   └── database.py
├── cvdl/                    # Computer vision / deep learning
│   ├── models/cvdl_model.py    # U-Net architecture
│   ├── src/predict_api.py       # inference class used by the backend
│   └── outputs/                  # trained model weights + evaluation results
│
├── disaster-ai/                      # Disaster AI service
│   ├── app.py                        # AI service entrypoint 
│   ├── ai_model.py                   # AI model logic
│   ├── services/                     # Gemini integration
│   └── requirements.txt
│
├── frontend/                         # React + Vite 
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   └── package.json
│
├── database.db                       # Local SQLite database
├── requirements.txt                  # Backend dependencies
└── README.md
```

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/incidents/assess` | Run the AI model on an image, return severity only (nothing saved) |
| POST | `/incidents/report` | Full flow: image + location (+ optional audio/video) → AI assessment → saved to database |
| GET | `/incidents/` | List saved incidents, with optional `severity` and `limit` filters |
| POST | `/incidents/chat` | Ask a question about a specific incident, answered by Gemini |

## Getting started (backend)

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Gemini API key
# Create a file named .env in the project root with:
# GEMINI_API_KEY=your_key_here

# 4. Run the server
uvicorn app.main:app --reload --reload-dir app
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

## Getting started (frontend)

```bash
cd frontend
npm install
npm run dev
```

## Team

- **Backend & API:** RITU RAJ
- **Computer Vision / Deep Learning:** RIFA
- **Frontend:** NIKITA
