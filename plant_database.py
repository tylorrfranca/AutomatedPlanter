#!/usr/bin/env python3
"""
Plant Database for Automated Planter
Extracted from AutomatedPlanterSite repository
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime

class PlantDatabase:
    def __init__(self, db_path: str = "plants.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with plants table and initial data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create plants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                water_amount REAL NOT NULL,
                watering_frequency INTEGER NOT NULL,
                light_min REAL NOT NULL,
                light_max REAL NOT NULL,
                soil_type TEXT NOT NULL,
                soil_moisture_min REAL NOT NULL,
                soil_moisture_max REAL NOT NULL,
                humidity_min REAL NOT NULL,
                humidity_max REAL NOT NULL,
                temperature_min REAL NOT NULL,
                temperature_max REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert initial plant data
        initial_plants = [
            {
                'name': 'Snake Plant',
                'water_amount': 250,
                'watering_frequency': 14,
                'light_min': 50,
                'light_max': 200,
                'soil_type': 'Well-draining potting mix',
                'soil_moisture_min': 20,
                'soil_moisture_max': 40,
                'humidity_min': 30,
                'humidity_max': 60,
                'temperature_min': 15,
                'temperature_max': 30
            },
            {
                'name': 'Peace Lily',
                'water_amount': 300,
                'watering_frequency': 7,
                'light_min': 100,
                'light_max': 300,
                'soil_type': 'Rich, well-draining soil',
                'soil_moisture_min': 40,
                'soil_moisture_max': 70,
                'humidity_min': 50,
                'humidity_max': 80,
                'temperature_min': 18,
                'temperature_max': 28
            },
            {
                'name': 'Spider Plant',
                'water_amount': 200,
                'watering_frequency': 7,
                'light_min': 100,
                'light_max': 400,
                'soil_type': 'Well-draining potting soil',
                'soil_moisture_min': 30,
                'soil_moisture_max': 60,
                'humidity_min': 40,
                'humidity_max': 70,
                'temperature_min': 15,
                'temperature_max': 30
            },
            {
                'name': 'Pothos',
                'water_amount': 250,
                'watering_frequency': 7,
                'light_min': 50,
                'light_max': 300,
                'soil_type': 'Well-draining potting mix',
                'soil_moisture_min': 30,
                'soil_moisture_max': 60,
                'humidity_min': 40,
                'humidity_max': 70,
                'temperature_min': 18,
                'temperature_max': 30
            },
            {
                'name': 'Monstera',
                'water_amount': 400,
                'watering_frequency': 7,
                'light_min': 200,
                'light_max': 500,
                'soil_type': 'Rich, well-draining soil',
                'soil_moisture_min': 40,
                'soil_moisture_max': 70,
                'humidity_min': 60,
                'humidity_max': 80,
                'temperature_min': 20,
                'temperature_max': 30
            },
            {
                'name': 'ZZ Plant',
                'water_amount': 200,
                'watering_frequency': 21,
                'light_min': 50,
                'light_max': 200,
                'soil_type': 'Well-draining potting mix',
                'soil_moisture_min': 20,
                'soil_moisture_max': 40,
                'humidity_min': 30,
                'humidity_max': 60,
                'temperature_min': 15,
                'temperature_max': 30
            },
            {
                'name': 'Fiddle Leaf Fig',
                'water_amount': 350,
                'watering_frequency': 7,
                'light_min': 200,
                'light_max': 500,
                'soil_type': 'Well-draining potting soil',
                'soil_moisture_min': 30,
                'soil_moisture_max': 60,
                'humidity_min': 50,
                'humidity_max': 70,
                'temperature_min': 18,
                'temperature_max': 28
            },
            {
                'name': 'Aloe Vera',
                'water_amount': 150,
                'watering_frequency': 21,
                'light_min': 200,
                'light_max': 600,
                'soil_type': 'Cactus/succulent mix',
                'soil_moisture_min': 10,
                'soil_moisture_max': 30,
                'humidity_min': 30,
                'humidity_max': 50,
                'temperature_min': 15,
                'temperature_max': 30
            },
            {
                'name': 'Chinese Evergreen',
                'water_amount': 250,
                'watering_frequency': 10,
                'light_min': 50,
                'light_max': 200,
                'soil_type': 'Well-draining potting mix',
                'soil_moisture_min': 30,
                'soil_moisture_max': 60,
                'humidity_min': 40,
                'humidity_max': 70,
                'temperature_min': 18,
                'temperature_max': 28
            },
            {
                'name': 'Philodendron',
                'water_amount': 300,
                'watering_frequency': 7,
                'light_min': 100,
                'light_max': 400,
                'soil_type': 'Rich, well-draining soil',
                'soil_moisture_min': 40,
                'soil_moisture_max': 70,
                'humidity_min': 50,
                'humidity_max': 80,
                'temperature_min': 18,
                'temperature_max': 30
            }
        ]
        
        # Check if plants table is empty and insert initial data
        cursor.execute('SELECT COUNT(*) FROM plants')
        count = cursor.fetchone()[0]
        
        if count == 0:
            for plant in initial_plants:
                cursor.execute('''
                    INSERT INTO plants (
                        name, water_amount, watering_frequency, light_min, light_max, 
                        soil_type, soil_moisture_min, soil_moisture_max, humidity_min, 
                        humidity_max, temperature_min, temperature_max
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plant['name'], plant['water_amount'], plant['watering_frequency'],
                    plant['light_min'], plant['light_max'], plant['soil_type'],
                    plant['soil_moisture_min'], plant['soil_moisture_max'],
                    plant['humidity_min'], plant['humidity_max'],
                    plant['temperature_min'], plant['temperature_max']
                ))
        
        conn.commit()
        conn.close()
    
    def get_all_plants(self) -> List[Dict]:
        """Get all plants from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM plants ORDER BY name')
        plants = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return plants
    
    def get_plant_by_id(self, plant_id: int) -> Optional[Dict]:
        """Get a specific plant by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM plants WHERE id = ?', (plant_id,))
        plant = cursor.fetchone()
        
        conn.close()
        return dict(plant) if plant else None
    
    def get_plant_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific plant by name"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM plants WHERE name = ?', (name,))
        plant = cursor.fetchone()
        
        conn.close()
        return dict(plant) if plant else None
    
    def create_plant(self, plant_data: Dict) -> Dict:
        """Create a new plant"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO plants (
                name, water_amount, watering_frequency, light_min, light_max, 
                soil_type, soil_moisture_min, soil_moisture_max, humidity_min, 
                humidity_max, temperature_min, temperature_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plant_data['name'], plant_data['water_amount'], plant_data['watering_frequency'],
            plant_data['light_min'], plant_data['light_max'], plant_data['soil_type'],
            plant_data['soil_moisture_min'], plant_data['soil_moisture_max'],
            plant_data['humidity_min'], plant_data['humidity_max'],
            plant_data['temperature_min'], plant_data['temperature_max']
        ))
        
        plant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return self.get_plant_by_id(plant_id)
    
    def update_plant(self, plant_id: int, plant_data: Dict) -> Optional[Dict]:
        """Update an existing plant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        for key, value in plant_data.items():
            if key != 'id' and value is not None:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            conn.close()
            return self.get_plant_by_id(plant_id)
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(plant_id)
        
        query = f"UPDATE plants SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return self.get_plant_by_id(plant_id)
    
    def delete_plant(self, plant_id: int) -> bool:
        """Delete a plant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def export_to_json(self, filename: str = "plants_export.json"):
        """Export all plants to JSON file"""
        plants = self.get_all_plants()
        with open(filename, 'w') as f:
            json.dump(plants, f, indent=2, default=str)
        return len(plants)
    
    def import_from_json(self, filename: str):
        """Import plants from JSON file"""
        with open(filename, 'r') as f:
            plants = json.load(f)
        
        imported_count = 0
        for plant_data in plants:
            # Remove id and timestamps for import
            plant_data.pop('id', None)
            plant_data.pop('created_at', None)
            plant_data.pop('updated_at', None)
            
            self.create_plant(plant_data)
            imported_count += 1
        
        return imported_count

# Example usage
if __name__ == "__main__":
    # Initialize database
    db = PlantDatabase()
    
    # Get all plants
    plants = db.get_all_plants()
    print(f"Found {len(plants)} plants in database")
    
    # Export to JSON
    exported = db.export_to_json()
    print(f"Exported {exported} plants to JSON")
    
    # Example: Get specific plant
    snake_plant = db.get_plant_by_name("Snake Plant")
    if snake_plant:
        print(f"Snake Plant needs {snake_plant['water_amount']}ml every {snake_plant['watering_frequency']} days")
