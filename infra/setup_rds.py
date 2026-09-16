"""Setup RDS PostgreSQL with geography data."""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.environ.get("RDS_ENDPOINT", "localhost")
DB_PORT = int(os.environ.get("RDS_PORT", "5432"))
DB_NAME = os.environ.get("RDS_DB_NAME", "geography_db")
DB_USER = os.environ.get("RDS_USER", "postgres")
DB_PASSWORD = os.environ.get("RDS_PASSWORD", "postgres")

# Geography data
COUNTRIES = [
    (1, "India", "New Delhi", 1393409038, 3287263)
]

STATES = [
    (1, "Maharashtra", "Mumbai", "Southwest", 307713),
    (2, "Karnataka", "Bengaluru", "South", 191791),
    (3, "Tamil Nadu", "Chennai", "South", 130060),
    (4, "Uttar Pradesh", "Lucknow", "North", 240928),
    (5, "West Bengal", "Kolkata", "East", 88752),
    (6, "Telangana", "Hyderabad", "South", 112077),
    (7, "Rajasthan", "Jaipur", "Northwest", 342239),
    (8, "Gujarat", "Gandhinagar", "West", 196244),
    (9, "Andhra Pradesh", "Amaravati", "South", 160205),
    (10, "Madhya Pradesh", "Bhopal", "Central", 308252),
    (11, "Punjab", "Chandigarh", "North", 50362),
    (12, "Haryana", "Chandigarh", "North", 44212),
    (13, "Bihar", "Patna", "East", 94163),
    (14, "Jharkhand", "Ranchi", "East", 79716),
    (15, "Odisha", "Bhubaneswar", "East", 155707),
    (16, "Chhattisgarh", "Raipur", "Central", 135192),
    (17, "Kerala", "Thiruvananthapuram", "South", 38852),
    (18, "Assam", "Dispur", "Northeast", 78438),
    (19, "Himachal Pradesh", "Shimla", "North", 55673),
    (20, "Uttarakhand", "Dehradun", "North", 53483),
    (21, "Tripura", "Agartala", "Northeast", 10486),
    (22, "Manipur", "Imphal", "Northeast", 22327),
    (23, "Mizoram", "Aizawl", "Northeast", 21081),
    (24, "Nagaland", "Kohima", "Northeast", 16579),
    (25, "Sikkim", "Gangtok", "Northeast", 7096),
    (26, "Arunachal Pradesh", "Itanagar", "Northeast", 83743),
    (27, "Meghalaya", "Shillong", "Northeast", 22429),
    (28, "Goa", "Panaji", "West", 3702),
]

DISTRICTS = [
    (1, "Mumbai", 1),
    (2, "Pune", 1),
    (3, "Nagpur", 1),
    (4, "Bengaluru Urban", 2),
    (5, "Mysuru", 2),
    (6, "Chennai", 3),
    (7, "Coimbatore", 3),
]


def setup_database():
    """Create tables and insert geography data."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info(f"Connected to database: {DB_NAME}")
        
        with conn.cursor() as cur:
            # Create countries table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    capital VARCHAR(255),
                    population BIGINT,
                    area_sq_km NUMERIC
                )
            """)
            
            # Create states table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    capital VARCHAR(255),
                    region VARCHAR(100),
                    area_sq_km NUMERIC
                )
            """)
            
            # Create districts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS districts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    state_id INTEGER REFERENCES states(id)
                )
            """)
            
            # Insert countries
            execute_values(cur, "INSERT INTO countries (name, capital, population, area_sq_km) VALUES %s ON CONFLICT DO NOTHING",
                         COUNTRIES)
            
            # Insert states
            execute_values(cur, "INSERT INTO states (name, capital, region, area_sq_km) VALUES %s ON CONFLICT DO NOTHING",
                         STATES)
            
            # Insert districts
            execute_values(cur, "INSERT INTO districts (name, state_id) VALUES %s",
                         DISTRICTS)
            
            conn.commit()
            logger.info("✅ Database setup complete")
            
            # Verify data
            cur.execute("SELECT COUNT(*) FROM countries")
            countries_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM states")
            states_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM districts")
            districts_count = cur.fetchone()[0]
            
            logger.info(f"Data counts: {countries_count} countries, {states_count} states, {districts_count} districts")
        
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
