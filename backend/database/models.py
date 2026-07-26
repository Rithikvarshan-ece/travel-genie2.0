"""
TravelGenie Database Models
SQLite models for storing trip data, user preferences, and generated plans
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Trip(Base):
    """Main trip model storing user inputs and generated plans"""
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # User inputs
    budget = Column(Float, nullable=False)
    source_city = Column(String(100), nullable=False)
    trip_days = Column(Integer, nullable=False)
    travel_type = Column(String(50), nullable=False)  # solo, family, couple, friends
    transportation = Column(String(50), nullable=False)  # flight, train, bus, car
    interests = Column(Text, nullable=False)  # JSON string of interests array
    hotel_preference = Column(String(50), nullable=False)  # budget, luxury, hostel, resort
    travel_month = Column(String(20), nullable=False)
    destination = Column(String(100), nullable=True)

    # Generated data
    destination_suggestions = Column(Text, nullable=True)  # JSON
    budget_breakdown = Column(Text, nullable=True)  # JSON
    weather_info = Column(Text, nullable=True)  # JSON
    transport_options = Column(Text, nullable=True)  # JSON
    hotel_suggestions = Column(Text, nullable=True)  # JSON
    attractions = Column(Text, nullable=True)  # JSON
    daily_itinerary = Column(Text, nullable=True)  # JSON
    expense_summary = Column(Text, nullable=True)  # JSON
    final_recommendation = Column(Text, nullable=True)  # JSON

    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)


class Destination(Base):
    """Pre-populated destinations database"""
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    continent = Column(String(50), nullable=False)
    season = Column(String(50), nullable=False)  # summer, winter, monsoon, autumn, spring
    popularity_score = Column(Float, default=5.0)
    avg_daily_cost = Column(Float, nullable=False)
    interests = Column(Text, nullable=False)  # JSON array
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=True)
    currency = Column(String(10), default="USD")
    language = Column(String(50), default="English")
    best_months = Column(String(200), nullable=True)


class Hotel(Base):
    """Pre-populated hotel database"""
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    destination = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # budget, luxury, hostel, resort
    price_per_night = Column(Float, nullable=False)
    rating = Column(Float, default=4.0)
    amenities = Column(Text, nullable=True)  # JSON array
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    distance_from_center = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)


class FavoriteDestination(Base):
    """User favorites table"""
    __tablename__ = "favorite_destinations"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, nullable=False)
    destination = Column(String(100), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
