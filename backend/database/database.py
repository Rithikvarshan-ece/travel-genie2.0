"""
TravelGenie Database Setup
SQLite database connection and initialization
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.database.models import Base, Trip, Destination, Hotel, FavoriteDestination
import json
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_genie.db")

# Create engine with SQLite specific config
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    seed_destinations()
    seed_hotels()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_destinations():
    """Seed the database with popular destinations if empty"""
    db = SessionLocal()
    try:
        existing = db.query(Destination).first()
        if existing:
            return

        destinations = [
            # Asia
            Destination(
                name="Bali", country="Indonesia", continent="Asia",
                season="summer", popularity_score=9.2, avg_daily_cost=80,
                interests='["beach", "nature", "adventure", "food"]',
                description="Tropical paradise with stunning beaches, ancient temples, and vibrant culture",
                latitude=-8.3405, longitude=115.0920, currency="IDR", language="Indonesian",
                best_months="April to October"
            ),
            Destination(
                name="Tokyo", country="Japan", continent="Asia",
                season="spring", popularity_score=9.5, avg_daily_cost=150,
                interests='["historical", "food", "shopping", "nightlife"]',
                description="Ultramodern city blending tradition with innovation, incredible cuisine",
                latitude=35.6762, longitude=139.6503, currency="JPY", language="Japanese",
                best_months="March to May, September to November"
            ),
            Destination(
                name="Bangkok", country="Thailand", continent="Asia",
                season="winter", popularity_score=8.8, avg_daily_cost=50,
                interests='["food", "shopping", "historical", "nightlife"]',
                description="Vibrant city with ornate temples, bustling markets, and amazing street food",
                latitude=13.7563, longitude=100.5018, currency="THB", language="Thai",
                best_months="November to February"
            ),
            Destination(
                name="Goa", country="India", continent="Asia",
                season="winter", popularity_score=8.0, avg_daily_cost=60,
                interests='["beach", "nature", "adventure", "food", "nightlife"]',
                description="Beautiful coastal region with Portuguese heritage, pristine beaches, and vibrant nightlife",
                latitude=15.2993, longitude=74.1240, currency="INR", language="Konkani",
                best_months="November to February"
            ),
            Destination(
                name="Manali", country="India", continent="Asia",
                season="summer", popularity_score=7.8, avg_daily_cost=45,
                interests='["nature", "adventure", "historical"]',
                description="Scenic hill station in the Himalayas, perfect for adventure and nature lovers",
                latitude=32.2396, longitude=77.1887, currency="INR", language="Hindi",
                best_months="March to June, October to February"
            ),
            # Europe
            Destination(
                name="Paris", country="France", continent="Europe",
                season="spring", popularity_score=9.4, avg_daily_cost=180,
                interests='["historical", "food", "shopping", "nightlife"]',
                description="City of Light, romance, world-class art, cuisine, and iconic landmarks",
                latitude=48.8566, longitude=2.3522, currency="EUR", language="French",
                best_months="April to June, September to October"
            ),
            Destination(
                name="Barcelona", country="Spain", continent="Europe",
                season="summer", popularity_score=9.0, avg_daily_cost=130,
                interests='["beach", "historical", "food", "nightlife", "shopping"]',
                description="Vibrant Mediterranean city with unique architecture, beaches, and rich culture",
                latitude=41.3874, longitude=2.1686, currency="EUR", language="Spanish",
                best_months="May to October"
            ),
            Destination(
                name="Swiss Alps", country="Switzerland", continent="Europe",
                season="winter", popularity_score=8.9, avg_daily_cost=200,
                interests='["nature", "adventure", "food"]',
                description="Breathtaking alpine landscapes, world-class skiing, and charming villages",
                latitude=46.8182, longitude=8.2275, currency="CHF", language="German",
                best_months="December to March, June to September"
            ),
            # North America
            Destination(
                name="New York", country="USA", continent="North America",
                season="autumn", popularity_score=9.3, avg_daily_cost=200,
                interests='["shopping", "food", "historical", "nightlife"]',
                description="Iconic city that never sleeps with world-class entertainment, food, and culture",
                latitude=40.7128, longitude=-74.0060, currency="USD", language="English",
                best_months="April to June, September to November"
            ),
            Destination(
                name="Cancun", country="Mexico", continent="North America",
                season="winter", popularity_score=8.5, avg_daily_cost=120,
                interests='["beach", "adventure", "historical", "nightlife"]',
                description="Tropical paradise with white sand beaches, ancient Mayan ruins, and crystal-clear waters",
                latitude=21.1619, longitude=-86.8515, currency="MXN", language="Spanish",
                best_months="December to April"
            ),
            # Middle East
            Destination(
                name="Dubai", country="UAE", continent="Asia",
                season="winter", popularity_score=9.1, avg_daily_cost=180,
                interests='["shopping", "adventure", "food", "nightlife", "beach"]',
                description="Ultramodern city with luxury shopping, futuristic architecture, and desert adventures",
                latitude=25.2048, longitude=55.2708, currency="AED", language="Arabic",
                best_months="November to March"
            ),
            # Australia
            Destination(
                name="Sydney", country="Australia", continent="Oceania",
                season="summer", popularity_score=8.7, avg_daily_cost=160,
                interests='["beach", "nature", "food", "adventure", "nightlife"]',
                description="Stunning harbor city with iconic opera house, beautiful beaches, and outdoor lifestyle",
                latitude=-33.8688, longitude=151.2093, currency="AUD", language="English",
                best_months="September to November, March to May"
            ),
            # South America
            Destination(
                name="Rio de Janeiro", country="Brazil", continent="South America",
                season="summer", popularity_score=8.6, avg_daily_cost=90,
                interests='["beach", "nightlife", "nature", "adventure"]',
                description="Vibrant city with iconic beaches, carnival spirit, and stunning natural landscapes",
                latitude=-22.9068, longitude=-43.1729, currency="BRL", language="Portuguese",
                best_months="December to March"
            ),
            # Africa
            Destination(
                name="Cape Town", country="South Africa", continent="Africa",
                season="summer", popularity_score=8.4, avg_daily_cost=100,
                interests='["nature", "beach", "adventure", "food"]',
                description="Stunning coastal city with Table Mountain, beautiful beaches, and vibrant culture",
                latitude=-33.9249, longitude=18.4241, currency="ZAR", language="Afrikaans",
                best_months="November to March"
            ),
        ]

        for dest in destinations:
            db.add(dest)
        db.commit()
        print(f"Success Seeded {len(destinations)} destinations")
    except Exception as e:
        db.rollback()
        print(f"Error Error seeding destinations: {e}")
    finally:
        db.close()


def seed_hotels():
    """Seed the database with sample hotels"""
    db = SessionLocal()
    try:
        existing = db.query(Hotel).first()
        if existing:
            return

        hotels = [
            # Bali Hotels
            Hotel(name="Bali Beach Resort", destination="Bali", category="resort",
                  price_per_night=150, rating=4.5, amenities='["pool", "spa", "restaurant", "beach access", "free wifi"]',
                  latitude=-8.3405, longitude=115.0920, distance_from_center=2.0),
            Hotel(name="Bali Budget Inn", destination="Bali", category="budget",
                  price_per_night=35, rating=3.8, amenities='["free wifi", "breakfast", "air conditioning"]',
                  latitude=-8.3500, longitude=115.1000, distance_from_center=3.5),
            Hotel(name="Bali Luxury Villa", destination="Bali", category="luxury",
                  price_per_night=350, rating=4.9, amenities='["private pool", "butler service", "spa", "ocean view", "restaurant"]',
                  latitude=-8.3300, longitude=115.0800, distance_from_center=1.5),
            Hotel(name="Bali Hostel", destination="Bali", category="hostel",
                  price_per_night=15, rating=4.0, amenities='["free wifi", "shared kitchen", "locker", "common room"]',
                  latitude=-8.3600, longitude=115.1100, distance_from_center=4.0),

            # Tokyo Hotels
            Hotel(name="Tokyo Luxury Tower", destination="Tokyo", category="luxury",
                  price_per_night=400, rating=4.8, amenities='["sky bar", "spa", "multiple restaurants", "concierge", "free wifi"]',
                  latitude=35.6762, longitude=139.6503, distance_from_center=1.0),
            Hotel(name="Tokyo Capsule Inn", destination="Tokyo", category="budget",
                  price_per_night=30, rating=3.5, amenities='["free wifi", "locker", "shared bathroom"]',
                  latitude=35.6800, longitude=139.6600, distance_from_center=2.0),
            Hotel(name="Tokyo Traditional Ryokan", destination="Tokyo", category="resort",
                  price_per_night=250, rating=4.6, amenities='["hot spring", "traditional meals", "garden", "free wifi"]',
                  latitude=35.6700, longitude=139.6400, distance_from_center=3.0),

            # Paris Hotels
            Hotel(name="Paris Luxury Palace", destination="Paris", category="luxury",
                  price_per_night=500, rating=4.9, amenities='["spa", "michelin restaurant", "eiffel tower view", "concierge", "pool"]',
                  latitude=48.8566, longitude=2.3522, distance_from_center=0.5),
            Hotel(name="Paris Boutique Hotel", destination="Paris", category="budget",
                  price_per_night=80, rating=4.0, amenities='["free wifi", "breakfast", "air conditioning", "city view"]',
                  latitude=48.8600, longitude=2.3600, distance_from_center=1.5),
            Hotel(name="Paris Hostel", destination="Paris", category="hostel",
                  price_per_night=40, rating=3.8, amenities='["free wifi", "shared kitchen", "locker", "common room", "breakfast"]',
                  latitude=48.8700, longitude=2.3700, distance_from_center=2.5),

            # Dubai Hotels
            Hotel(name="Burj Al Arab", destination="Dubai", category="luxury",
                  price_per_night=800, rating=5.0, amenities='["private beach", "helicopter pad", "underwater restaurant", "spa", "butler"]',
                  latitude=25.1412, longitude=55.1852, distance_from_center=5.0),
            Hotel(name="Dubai Budget Stay", destination="Dubai", category="budget",
                  price_per_night=60, rating=3.7, amenities='["free wifi", "pool", "gym", "restaurant"]',
                  latitude=25.2000, longitude=55.2708, distance_from_center=3.0),
            Hotel(name="Dubai Marina Hotel", destination="Dubai", category="resort",
                  price_per_night=200, rating=4.3, amenities='["pool", "spa", "marina view", "restaurant", "free wifi"]',
                  latitude=25.0800, longitude=55.1400, distance_from_center=7.0),

            # Goa Hotels
            Hotel(name="Goa Beach Resort", destination="Goa", category="resort",
                  price_per_night=120, rating=4.4, amenities='["pool", "beach access", "restaurant", "bar", "free wifi"]',
                  latitude=15.2993, longitude=74.1240, distance_from_center=2.0),
            Hotel(name="Goa Budget Guesthouse", destination="Goa", category="budget",
                  price_per_night=25, rating=3.6, amenities='["free wifi", "breakfast", "air conditioning"]',
                  latitude=15.3100, longitude=74.1300, distance_from_center=3.0),
            Hotel(name="Goa Portuguese Villa", destination="Goa", category="luxury",
                  price_per_night=250, rating=4.7, amenities='["private pool", "garden", "restaurant", "spa", "free wifi"]',
                  latitude=15.2800, longitude=74.1100, distance_from_center=1.5),

            # Manali Hotels
            Hotel(name="Manali Mountain Resort", destination="Manali", category="resort",
                  price_per_night=100, rating=4.3, amenities='["mountain view", "fireplace", "restaurant", "free wifi", "parking"]',
                  latitude=32.2396, longitude=77.1887, distance_from_center=1.5),
            Hotel(name="Manali Budget Lodge", destination="Manali", category="budget",
                  price_per_night=30, rating=3.5, amenities='["free wifi", "heater", "parking", "breakfast"]',
                  latitude=32.2500, longitude=77.1900, distance_from_center=2.0),
            Hotel(name="Manali Hostel", destination="Manali", category="hostel",
                  price_per_night=12, rating=4.1, amenities='["free wifi", "common room", "shared kitchen", "bonfire"]',
                  latitude=32.2400, longitude=77.1950, distance_from_center=2.5),

            # Bangkok Hotels
            Hotel(name="Bangkok Riverside Hotel", destination="Bangkok", category="luxury",
                  price_per_night=180, rating=4.6, amenities='["pool", "spa", "river view", "restaurant", "free wifi"]',
                  latitude=13.7563, longitude=100.5018, distance_from_center=1.0),
            Hotel(name="Bangkok Budget Inn", destination="Bangkok", category="budget",
                  price_per_night=25, rating=3.8, amenities='["free wifi", "breakfast", "air conditioning"]',
                  latitude=13.7600, longitude=100.5100, distance_from_center=2.0),
            Hotel(name="Bangkok Backpackers", destination="Bangkok", category="hostel",
                  price_per_night=10, rating=4.0, amenities='["free wifi", "shared kitchen", "common room", "bar"]',
                  latitude=13.7700, longitude=100.5200, distance_from_center=3.0),

            # New York Hotels
            Hotel(name="NYC Luxury Suites", destination="New York", category="luxury",
                  price_per_night=600, rating=4.8, amenities='["spa", "fitness center", "restaurant", "bar", "central park view"]',
                  latitude=40.7128, longitude=-74.0060, distance_from_center=1.0),
            Hotel(name="NYC Budget Hotel", destination="New York", category="budget",
                  price_per_night=100, rating=3.6, amenities='["free wifi", "breakfast", "air conditioning"]',
                  latitude=40.7200, longitude=-74.0000, distance_from_center=2.5),
            Hotel(name="NYC Hostel", destination="New York", category="hostel",
                  price_per_night=50, rating=3.9, amenities='["free wifi", "locker", "common room", "breakfast"]',
                  latitude=40.7300, longitude=-73.9900, distance_from_center=3.0),
        ]

        for hotel in hotels:
            db.add(hotel)
        db.commit()
        print(f"Success Seeded {len(hotels)} hotels")
    except Exception as e:
        db.rollback()
        print(f"Error Error seeding hotels: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Success Database initialized successfully!")
