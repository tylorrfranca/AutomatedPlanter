#!/usr/bin/env python3
"""
Plant Configuration System for Automated Planter
Uses plant database to configure Raspberry Pi sensors and actuators
"""

import json
import os
from typing import Dict, List, Optional
from plant_database import PlantDatabase

class PlantConfig:
    def __init__(self, config_file: str = "plant_config.json"):
        self.config_file = config_file
        self.db = PlantDatabase()
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.create_default_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_default_config(self) -> Dict:
        """Create default configuration"""
        return {
            "active_plants": [],
            "sensors": {
                "soil_moisture": {
                    "enabled": True,
                    "pin": 18,
                    "read_interval": 300,  # 5 minutes
                    "calibration": {
                        "dry": 1023,
                        "wet": 0
                    }
                },
                "temperature": {
                    "enabled": True,
                    "pin": 4,
                    "read_interval": 300,  # 5 minutes
                    "unit": "celsius"
                },
                "humidity": {
                    "enabled": True,
                    "pin": 4,
                    "read_interval": 300,  # 5 minutes
                    "unit": "percent"
                },
                "light": {
                    "enabled": True,
                    "pin": 17,
                    "read_interval": 600,  # 10 minutes
                    "unit": "lux"
                }
            },
            "actuators": {
                "water_pump": {
                    "enabled": True,
                    "pin": 23,
                    "flow_rate": 100,  # ml per second
                    "safety_timeout": 30  # seconds
                },
                "led_grow_light": {
                    "enabled": True,
                    "pin": 24,
                    "max_brightness": 255,
                    "schedule": {
                        "on_time": "06:00",
                        "off_time": "22:00"
                    }
                },
                "fan": {
                    "enabled": True,
                    "pin": 25,
                    "auto_mode": True,
                    "humidity_threshold": 80
                }
            },
            "system": {
                "log_level": "INFO",
                "data_log_interval": 3600,  # 1 hour
                "backup_interval": 86400,   # 24 hours
                "web_interface": {
                    "enabled": True,
                    "port": 8080,
                    "host": "0.0.0.0"
                }
            }
        }
    
    def add_plant(self, plant_name: str, position: int = 0) -> bool:
        """Add a plant to the active configuration"""
        plant = self.db.get_plant_by_name(plant_name)
        if not plant:
            print(f"Plant '{plant_name}' not found in database")
            return False
        
        # Check if plant already exists at this position
        for active_plant in self.config["active_plants"]:
            if active_plant["position"] == position:
                print(f"Position {position} already occupied by {active_plant['name']}")
                return False
        
        plant_config = {
            "name": plant["name"],
            "position": position,
            "plant_id": plant["id"],
            "last_watered": None,
            "last_checked": None,
            "status": "active",
            "custom_settings": {
                "water_amount": plant["water_amount"],
                "watering_frequency": plant["watering_frequency"],
                "light_min": plant["light_min"],
                "light_max": plant["light_max"],
                "soil_moisture_min": plant["soil_moisture_min"],
                "soil_moisture_max": plant["soil_moisture_max"],
                "humidity_min": plant["humidity_min"],
                "humidity_max": plant["humidity_max"],
                "temperature_min": plant["temperature_min"],
                "temperature_max": plant["temperature_max"]
            }
        }
        
        self.config["active_plants"].append(plant_config)
        self.save_config()
        print(f"Added {plant_name} at position {position}")
        return True
    
    def remove_plant(self, position: int) -> bool:
        """Remove a plant from the active configuration"""
        for i, plant in enumerate(self.config["active_plants"]):
            if plant["position"] == position:
                removed_plant = self.config["active_plants"].pop(i)
                self.save_config()
                print(f"Removed {removed_plant['name']} from position {position}")
                return True
        
        print(f"No plant found at position {position}")
        return False
    
    def get_plant_at_position(self, position: int) -> Optional[Dict]:
        """Get plant configuration at specific position"""
        for plant in self.config["active_plants"]:
            if plant["position"] == position:
                return plant
        return None
    
    def update_plant_status(self, position: int, status: str):
        """Update plant status (active, needs_water, needs_light, etc.)"""
        plant = self.get_plant_at_position(position)
        if plant:
            plant["status"] = status
            plant["last_checked"] = self.get_current_timestamp()
            self.save_config()
    
    def update_watering_time(self, position: int):
        """Update last watering time for a plant"""
        plant = self.get_plant_at_position(position)
        if plant:
            plant["last_watered"] = self.get_current_timestamp()
            self.save_config()
    
    def get_plants_needing_water(self) -> List[Dict]:
        """Get list of plants that need watering"""
        from datetime import datetime, timedelta
        
        plants_needing_water = []
        current_time = datetime.now()
        
        for plant in self.config["active_plants"]:
            if plant["status"] != "active":
                continue
            
            # Check if enough time has passed since last watering
            if plant["last_watered"]:
                last_watered = datetime.fromisoformat(plant["last_watered"])
                days_since_watering = (current_time - last_watered).days
                watering_frequency = plant["custom_settings"]["watering_frequency"]
                
                if days_since_watering >= watering_frequency:
                    plants_needing_water.append(plant)
            else:
                # Never been watered
                plants_needing_water.append(plant)
        
        return plants_needing_water
    
    def get_plant_care_requirements(self, position: int) -> Optional[Dict]:
        """Get care requirements for plant at specific position"""
        plant = self.get_plant_at_position(position)
        if plant:
            return plant["custom_settings"]
        return None
    
    def validate_sensor_reading(self, position: int, sensor_type: str, value: float) -> Dict:
        """Validate sensor reading against plant requirements"""
        plant = self.get_plant_at_position(position)
        if not plant:
            return {"valid": False, "message": "No plant at position"}
        
        requirements = plant["custom_settings"]
        result = {"valid": True, "message": "OK", "action": None}
        
        if sensor_type == "soil_moisture":
            min_val = requirements["soil_moisture_min"]
            max_val = requirements["soil_moisture_max"]
            
            if value < min_val:
                result["valid"] = False
                result["message"] = f"Soil too dry ({value}% < {min_val}%)"
                result["action"] = "water"
            elif value > max_val:
                result["valid"] = False
                result["message"] = f"Soil too wet ({value}% > {max_val}%)"
                result["action"] = "drain"
        
        elif sensor_type == "temperature":
            min_val = requirements["temperature_min"]
            max_val = requirements["temperature_max"]
            
            if value < min_val:
                result["valid"] = False
                result["message"] = f"Temperature too low ({value}°C < {min_val}°C)"
                result["action"] = "heat"
            elif value > max_val:
                result["valid"] = False
                result["message"] = f"Temperature too high ({value}°C > {max_val}°C)"
                result["action"] = "cool"
        
        elif sensor_type == "humidity":
            min_val = requirements["humidity_min"]
            max_val = requirements["humidity_max"]
            
            if value < min_val:
                result["valid"] = False
                result["message"] = f"Humidity too low ({value}% < {min_val}%)"
                result["action"] = "humidify"
            elif value > max_val:
                result["valid"] = False
                result["message"] = f"Humidity too high ({value}% > {max_val}%)"
                result["action"] = "dehumidify"
        
        elif sensor_type == "light":
            min_val = requirements["light_min"]
            max_val = requirements["light_max"]
            
            if value < min_val:
                result["valid"] = False
                result["message"] = f"Light too low ({value} lux < {min_val} lux)"
                result["action"] = "increase_light"
            elif value > max_val:
                result["valid"] = False
                result["message"] = f"Light too high ({value} lux > {max_val} lux)"
                result["action"] = "decrease_light"
        
        return result
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def list_available_plants(self) -> List[Dict]:
        """Get list of all available plants from database"""
        return self.db.get_all_plants()
    
    def export_config(self, filename: str = "plant_config_backup.json"):
        """Export current configuration to file"""
        with open(filename, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration exported to {filename}")
    
    def import_config(self, filename: str):
        """Import configuration from file"""
        with open(filename, 'r') as f:
            self.config = json.load(f)
        self.save_config()
        print(f"Configuration imported from {filename}")

# Example usage
if __name__ == "__main__":
    # Initialize configuration
    config = PlantConfig()
    
    # List available plants
    print("Available plants:")
    plants = config.list_available_plants()
    for plant in plants[:5]:  # Show first 5
        print(f"- {plant['name']}")
    
    # Add some plants
    config.add_plant("Snake Plant", position=0)
    config.add_plant("Peace Lily", position=1)
    
    # Check plants needing water
    plants_needing_water = config.get_plants_needing_water()
    print(f"\nPlants needing water: {len(plants_needing_water)}")
    
    # Validate sensor reading
    validation = config.validate_sensor_reading(0, "soil_moisture", 15)
    print(f"Soil moisture validation: {validation}")
    
    # Export configuration
    config.export_config()
