#!/usr/bin/env python3
"""
Integration Script for AutomatedPlanterSite
Connects Raspberry Pi system to existing web interface
"""

import requests
import json
import time
import logging
from datetime import datetime
from raspberry_pi_core import RaspberryPiCore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebsiteIntegration:
    """Integration with existing AutomatedPlanterSite"""
    
    def __init__(self, website_url: str, pi_core: RaspberryPiCore):
        """
        Initialize integration with existing website
        Args:
            website_url: URL of your AutomatedPlanterSite (e.g., http://localhost:3000)
            pi_core: Raspberry Pi core system instance
        """
        self.website_url = website_url.rstrip('/')
        self.pi_core = pi_core
        self.running = False
        
        logger.info(f"Website integration initialized with {self.website_url}")
    
    def sync_plants_to_website(self):
        """Sync plant configuration to website"""
        try:
            # Get plant configuration from Raspberry Pi
            plants = self.pi_core.plant_config["active_plants"]
            
            # Send to website (assuming your website has an API endpoint)
            for plant in plants:
                payload = {
                    "name": plant["name"],
                    "position": plant["position"],
                    "water_amount": plant["water_amount"],
                    "watering_frequency": plant["watering_frequency"],
                    "hardware_managed": True  # Flag to indicate this is managed by hardware
                }
                
                # Try to add/update plant on website
                response = requests.post(
                    f"{self.website_url}/api/plants/hardware-sync",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.info(f"Synced plant {plant['name']} to website")
                else:
                    logger.warning(f"Failed to sync plant {plant['name']}: {response.status_code}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing plants to website: {e}")
            return False
    
    def send_sensor_data_to_website(self):
        """Send sensor data to website"""
        try:
            # Get sensor data from Raspberry Pi
            sensor_data = self.pi_core.read_all_sensors()
            plants_needing_water = self.pi_core.check_plants_needing_water()
            
            # Prepare payload
            payload = {
                "timestamp": sensor_data["timestamp"],
                "hardware_id": "raspberry_pi_001",  # Unique identifier for this hardware
                "sensor_data": {
                    "temperature": sensor_data.get("temperature_celsius"),
                    "humidity": sensor_data.get("humidity_percent"),
                    "soil_moisture": sensor_data.get("soil_moisture_percent"),
                    "light": sensor_data.get("light_lux"),
                    "water_tank_level": sensor_data.get("water_tank_percentage")
                },
                "plant_status": {
                    "plants_needing_water": [p["name"] for p in plants_needing_water],
                    "active_plants": len(self.pi_core.plant_config["active_plants"])
                },
                "pump_status": self.pi_core.system_status["pump_status"]
            }
            
            # Send to website
            response = requests.post(
                f"{self.website_url}/api/hardware/sensor-data",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Sensor data sent to website successfully")
                return True
            else:
                logger.warning(f"Failed to send sensor data: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending sensor data to website: {e}")
            return False
    
    def get_watering_commands_from_website(self):
        """Check for watering commands from website"""
        try:
            # Check if website has any watering commands
            response = requests.get(
                f"{self.website_url}/api/hardware/watering-commands",
                timeout=5
            )
            
            if response.status_code == 200:
                commands = response.json()
                
                for command in commands.get("commands", []):
                    position = command.get("position")
                    water_amount = command.get("water_amount")
                    
                    if position is not None:
                        logger.info(f"Received watering command for position {position}")
                        
                        # Execute watering command
                        success = self.pi_core.manual_water_plant(position)
                        
                        # Confirm command execution
                        self.confirm_watering_command(command["id"], success)
                        
                        if success:
                            logger.info(f"Successfully executed watering command for position {position}")
                        else:
                            logger.error(f"Failed to execute watering command for position {position}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking watering commands from website: {e}")
            return False
    
    def confirm_watering_command(self, command_id: str, success: bool):
        """Confirm watering command execution to website"""
        try:
            payload = {
                "command_id": command_id,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.website_url}/api/hardware/confirm-command",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Confirmed watering command {command_id}")
            else:
                logger.warning(f"Failed to confirm command {command_id}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error confirming command {command_id}: {e}")
    
    def start_integration_loop(self, interval_seconds: int = 60):
        """Start continuous integration loop"""
        self.running = True
        logger.info(f"Starting integration loop with website (interval: {interval_seconds}s)")
        
        # Initial sync
        logger.info("Performing initial sync with website...")
        self.sync_plants_to_website()
        
        while self.running:
            try:
                # Send sensor data
                self.send_sensor_data_to_website()
                
                # Check for commands
                self.get_watering_commands_from_website()
                
                # Wait for next cycle
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Integration loop stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Error in integration loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def stop_integration(self):
        """Stop integration loop"""
        self.running = False
        logger.info("Integration stopped")

def main():
    """Main integration function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python integrate_with_website.py <website_url> [--simulation]")
        print("Example: python integrate_with_website.py http://localhost:3000 --simulation")
        return
    
    website_url = sys.argv[1]
    simulation_mode = "--simulation" in sys.argv or "-s" in sys.argv
    
    print(f"🌐 Website Integration for Automated Planter")
    print(f"Website URL: {website_url}")
    print(f"Mode: {'Simulation' if simulation_mode else 'Real Hardware'}")
    print("=" * 50)
    
    # Initialize Raspberry Pi core
    pi_core = RaspberryPiCore(simulation_mode=simulation_mode, web_interface_url=website_url)
    
    # Initialize website integration
    integration = WebsiteIntegration(website_url, pi_core)
    
    try:
        # Start integration loop
        integration.start_integration_loop(interval_seconds=30)
    except KeyboardInterrupt:
        print("\nIntegration stopped by user")
    finally:
        integration.stop_integration()
        pi_core.cleanup()

if __name__ == "__main__":
    main()
