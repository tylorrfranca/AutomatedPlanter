#!/usr/bin/env python3
"""
Website Database Client
Connects to AutomatedPlanterSite database and API
Uses the existing plant database instead of creating a separate one
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebsiteDatabaseClient:
    """Client to interact with AutomatedPlanterSite database and API"""
    
    def __init__(self, website_url: str):
        """
        Initialize client for website database
        Args:
            website_url: URL of your AutomatedPlanterSite (e.g., http://localhost:3000)
        """
        self.website_url = website_url.rstrip('/')
        self.api_base = f"{self.website_url}/api"
        self.session = requests.Session()
        
        logger.info(f"Website database client initialized: {self.website_url}")
    
    def test_connection(self) -> bool:
        """Test connection to the website"""
        try:
            response = self.session.get(f"{self.api_base}/plants", timeout=5)
            if response.status_code == 200:
                logger.info("Successfully connected to AutomatedPlanterSite")
                return True
            else:
                logger.warning(f"Website returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to website: {e}")
            return False
    
    def get_all_plants(self) -> List[Dict]:
        """Get all plants from the website database"""
        try:
            response = self.session.get(f"{self.api_base}/plants", timeout=5)
            if response.status_code == 200:
                plants = response.json()
                logger.info(f"Retrieved {len(plants)} plants from website database")
                return plants
            else:
                logger.error(f"Failed to get plants: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting plants: {e}")
            return []
    
    def get_plant_by_id(self, plant_id: int) -> Optional[Dict]:
        """Get a specific plant by ID"""
        try:
            response = self.session.get(f"{self.api_base}/plants/{plant_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Plant with ID {plant_id} not found")
                return None
            else:
                logger.error(f"Failed to get plant {plant_id}: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting plant {plant_id}: {e}")
            return None
    
    def get_plant_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific plant by name"""
        plants = self.get_all_plants()
        for plant in plants:
            if plant.get('name', '').lower() == name.lower():
                return plant
        return None
    
    def create_plant(self, plant_data: Dict) -> Optional[Dict]:
        """Create a new plant in the website database"""
        try:
            response = self.session.post(f"{self.api_base}/plants", json=plant_data, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                created_plant = response.json()
                logger.info(f"Created plant: {created_plant.get('name')}")
                return created_plant
            else:
                logger.error(f"Failed to create plant: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating plant: {e}")
            return None
    
    def update_plant(self, plant_id: int, plant_data: Dict) -> Optional[Dict]:
        """Update an existing plant"""
        try:
            response = self.session.put(f"{self.api_base}/plants/{plant_id}", json=plant_data, timeout=5)
            if response.status_code == 200:
                updated_plant = response.json()
                logger.info(f"Updated plant: {updated_plant.get('name')}")
                return updated_plant
            else:
                logger.error(f"Failed to update plant {plant_id}: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating plant {plant_id}: {e}")
            return None
    
    def delete_plant(self, plant_id: int) -> bool:
        """Delete a plant from the database"""
        try:
            response = self.session.delete(f"{self.api_base}/plants/{plant_id}", timeout=5)
            if response.status_code == 200:
                logger.info(f"Deleted plant with ID {plant_id}")
                return True
            else:
                logger.error(f"Failed to delete plant {plant_id}: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting plant {plant_id}: {e}")
            return False
    
    def send_sensor_data(self, sensor_data: Dict) -> bool:
        """Send sensor data to the website"""
        try:
            # Create a sensor reading entry
            payload = {
                "timestamp": sensor_data.get("timestamp", datetime.now().isoformat()),
                "temperature": sensor_data.get("temperature_celsius"),
                "humidity": sensor_data.get("humidity_percent"),
                "soil_moisture": sensor_data.get("soil_moisture_percent"),
                "light_level": sensor_data.get("light_lux"),
                "water_level": sensor_data.get("water_tank_percentage"),
                "source": "raspberry_pi"
            }
            
            response = self.session.post(f"{self.api_base}/sensor-data", json=payload, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                logger.info("Sensor data sent to website successfully")
                return True
            else:
                logger.warning(f"Failed to send sensor data: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending sensor data: {e}")
            return False
    
    def log_watering_event(self, plant_id: int, water_amount: float, success: bool) -> bool:
        """Log a watering event to the website"""
        try:
            payload = {
                "plant_id": plant_id,
                "water_amount": water_amount,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "source": "raspberry_pi_auto"
            }
            
            response = self.session.post(f"{self.api_base}/watering-events", json=payload, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Watering event logged for plant {plant_id}")
                return True
            else:
                logger.warning(f"Failed to log watering event: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error logging watering event: {e}")
            return False
    
    def get_plants_needing_water(self) -> List[Dict]:
        """Get plants that need watering based on website database"""
        try:
            response = self.session.get(f"{self.api_base}/plants/needing-water", timeout=5)
            if response.status_code == 200:
                plants = response.json()
                logger.info(f"Found {len(plants)} plants needing water")
                return plants
            else:
                # Fallback: get all plants and check locally
                logger.warning("Website doesn't have 'needing-water' endpoint, checking locally")
                return self._check_plants_needing_water_locally()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting plants needing water: {e}")
            return self._check_plants_needing_water_locally()
    
    def _check_plants_needing_water_locally(self) -> List[Dict]:
        """Check plants needing water based on local logic"""
        all_plants = self.get_all_plants()
        plants_needing_water = []
        
        # This is a simplified check - you might want to implement more sophisticated logic
        # based on your website's watering schedule system
        for plant in all_plants:
            # Check if plant is active and needs watering
            if plant.get('status') == 'active':
                # Simple check: if no recent watering events, it needs water
                # You can enhance this based on your website's logic
                plants_needing_water.append(plant)
        
        return plants_needing_water
    
    def get_system_status(self) -> Dict:
        """Get system status from website"""
        try:
            response = self.session.get(f"{self.api_base}/system/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                # Return basic status if endpoint doesn't exist
                return {
                    "website_connected": True,
                    "plants_count": len(self.get_all_plants()),
                    "timestamp": datetime.now().isoformat()
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "website_connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def sync_hardware_config(self, hardware_config: Dict) -> bool:
        """Sync hardware configuration to website"""
        try:
            payload = {
                "hardware_id": "raspberry_pi_001",
                "config": hardware_config,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{self.api_base}/hardware/config", json=payload, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                logger.info("Hardware configuration synced to website")
                return True
            else:
                logger.warning(f"Failed to sync hardware config: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing hardware config: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Test the database client
    client = WebsiteDatabaseClient("http://localhost:3000")
    
    print("Testing Website Database Client...")
    
    # Test connection
    if client.test_connection():
        print("✅ Connection successful")
        
        # Get all plants
        plants = client.get_all_plants()
        print(f"✅ Retrieved {len(plants)} plants")
        
        # Show first few plants
        for i, plant in enumerate(plants[:3]):
            print(f"   {i+1}. {plant.get('name')} - {plant.get('watering_frequency')} days")
        
        # Test sensor data sending
        test_sensor_data = {
            "temperature_celsius": 22.5,
            "humidity_percent": 60.0,
            "soil_moisture_percent": 45.0,
            "light_lux": 300.0,
            "water_tank_percentage": 75.0
        }
        
        if client.send_sensor_data(test_sensor_data):
            print("✅ Sensor data sent successfully")
        else:
            print("❌ Failed to send sensor data")
    
    else:
        print("❌ Connection failed")
        print("Make sure your AutomatedPlanterSite is running on http://localhost:3000")
