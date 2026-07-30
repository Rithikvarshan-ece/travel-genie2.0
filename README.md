# 🌍 TravelGenie – AI-Powered Multi-Agent Travel Planner

TravelGenie is an AI-powered multi-agent travel planning system that generates personalized travel itineraries based on user preferences, budget, duration, and destination. It leverages multiple AI agents to collaboratively recommend destinations, hotels, transport options, daily schedules, and validate the complete travel plan.

---

## ✨ Features

- 🤖 Multi-Agent AI Architecture
- 🗺️ Intelligent Destination Recommendations
- 🏨 Hotel Recommendations
- 🚗 Smart Transport Suggestions
- 📅 Automatic Day-wise Itinerary Generation
- 💰 Budget Analysis & Validation
- 🌤️ Weather Integration
- 📍 Route Optimization
- 📊 Expense Breakdown
- ⚡ Real-time Streaming Planner Progress
- 🔄 SQLite Fallback for Offline Reliability

---

## 🏗️ System Architecture

```
User Input
     │
     ▼
Planner Agent
     │
     ├────────► Trip Feasibility Agent
     │
     ├────────► Destination Agent
     │
     ├────────► Route Logistics Agent
     │
     ├────────► Schedule Agent
     │
     └────────► Validation Agent
                  │
                  ▼
          Final Travel Plan
```

---

## 🛠️ Tech Stack

### Frontend
- React.js
- TypeScript
- Vite
- Tailwind CSS

### Backend
- Python
- FastAPI
- AsyncIO

### AI & LLM
- Groq API
- Llama 3.3 70B Versatile
- LangGraph
- Pydantic AI Models

### Database
- MongoDB Atlas
- SQLite (Fallback)

### APIs
- OpenStreetMap (OSM)
- Overpass API
- OSRM Routing
- OpenWeather API
- Google Places API (Optional)
- Google Routes API (Optional)

### Version Control
- Git
- GitHub

---

## 🚀 Project Workflow

1. User enters destination, budget, duration, and preferences.
2. Planner Agent coordinates all AI agents.
3. Destination Agent suggests suitable destinations and hotels.
4. Route Logistics Agent calculates transport options.
5. Schedule Agent creates a detailed itinerary.
6. Validation Agent checks feasibility and budget.
7. TravelGenie generates the final optimized travel plan.

---

## 📂 Project Structure

```
TravelGenie
│
├── backend/
│   ├── agents/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── assets/
│
├── README.md
├── requirements.txt
└── package.json
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/TravelGenie.git
cd TravelGenie
```

### Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn backend.api.main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## 🔑 Environment Variables

Create a `.env` file in the backend directory.

```env
GROQ_API_KEY=YOUR_GROQ_KEY
GROQ_MODEL=llama-3.3-70b-versatile

MONGODB_URL=YOUR_MONGODB_URL

OPENWEATHER_API_KEY=YOUR_OPENWEATHER_KEY

GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_KEY
```

---

## 📸 Screenshots

Add screenshots of:

- Home Page
- Planner Progress
- Generated Itinerary
- Hotel Recommendations
- Budget Summary
- Transport Recommendations

---

## 🎯 Future Enhancements

- Voice-based Trip Planning
- Flight Booking Integration
- Hotel Booking APIs
- Google Maps Live Navigation
- Multi-language Support
- PDF Itinerary Export
- Mobile Application

---

## 👨‍💻 Developed By

**Rithik Varshan A R**

B.E. Electronics and Communication Engineering (ECE)

---

## 📄 License

This project is developed for educational and research purposes.

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
