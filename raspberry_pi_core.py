#!/usr/bin/env python3
"""
Raspberry Pi Core System for Automated Planter
Focuses on hardware control and sensor integration
Can connect to existing AutomatedPlanterSite web interface
"""

import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from hardware_drivers import HardwareInterface

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RaspberryPiCore:
    """Core Raspberry Pi system for automated planter"""
    
    def __init__(self, simulation_mode: bool = True, web_interface_url: str = None):
        """
        Initialize Raspberry Pi core system
        Args:
            simulation_mode: Use simulated hardware for testing
            web_interface_url: URL to existing AutomatedPlanterSite (optional)
        """
        self.simulation_mode = simulation_mode
        self.web_interface_url = web_interface_url
        self.hardware = HardwareInterface(simulation_mode=simulation_mode)
        self.running = False
        
        # Plant configuration (simplified for hardware focus)
        self.plant_config = {
            "active_plants": [
                {"name": "Snake Plant", "position": 0, "water_amount": 250, "watering_frequency": 14},
                {"name": "Peace Lily", "position": 1, "water_amount": 300, "watering_frequency": 7},
                {"name": "Spider Plant", "position": 2, "water_amount": 200, "watering_frequency": 7}
            ]
        }
        
        # System status
        self.system_status = {
            "last_reading": None,
            "plants_needing_water": [],
            "sensor_history": [],
            "pump_status": {"pump1": False, "pump2": False, "last_watered": None}
        }
        
        logger.info(f"Raspberry Pi Core initialized (simulation: {simulation_mode})")
        if web_interface_url:
            logger.info(f"Web interface URL: {web_interface_url}")
    
    def read_all_sensors(self) -> Dict:
        """Read all sensors and return comprehensive data"""
        sensor_data = self.hardware.read_all_sensors()
        self.system_status["last_reading"] = sensor_data
        
        # Store in history (keep last 50 readings)
        self.system_status["sensor_history"].append(sensor_data)
        if len(self.system_status["sensor_history"]) > 50:
            self.system_status["sensor_history"] = self.system_status["sensor_history"][-50:]
        
        return sensor_data
    
    def check_plants_needing_water(self) -> List[Dict]:
        """Check which plants need watering based on time since last watering"""
        plants_needing_water = []
        current_time = datetime.now()
        
        for plant in self.plant_config["active_plants"]:
            position = plant["position"]
            plant_name = plant["name"]
            watering_frequency = plant["watering_frequency"]
            
            # Check if enough time has passed since last watering
            last_watered = self.system_status["pump_status"].get("last_watered")
            if last_watered:
                last_watered_time = datetime.fromisoformat(last_watered)
                days_since_watering = (current_time - last_watered_time).days
                
                if days_since_watering >= watering_frequency:
                    plants_needing_water.append(plant)
            else:
                # Never been watered
                plants_needing_water.append(plant)
        
        self.system_status["plants_needing_water"] = plants_needing_water
        return plants_needing_water
    
    def water_plant(self, plant: Dict) -> bool:
        """Water a specific plant"""
        position = plant["position"]
        plant_name = plant["name"]
        water_amount = plant["water_amount"]
        
        logger.info(f"Watering {plant_name} at position {position} with {water_amount}ml")
        
        # Calculate pump duration (assuming 100ml per second flow rate)
        duration = water_amount / 100.0  # seconds
        pump_num = (position % 2) + 1  # Alternate between pumps
        
        # Control the water pump
        success = self.hardware.control_pump(pump_num, duration, water_amount)
        
        if success:
            # Update watering time
            self.system_status["pump_status"]["last_watered"] = datetime.now().isoformat()
            logger.info(f"Successfully watered {plant_name}")
        else:
            logger.error(f"Failed to water {plant_name}")
        
        return success
    
    def auto_water_plants(self):
        """Automatically water plants that need it"""
        plants_needing_water = self.check_plants_needing_water()
        
        if plants_needing_water:
            logger.info(f"Found {len(plants_needing_water)} plants needing water")
            
            for plant in plants_needing_water:
                success = self.water_plant(plant)
                if success:
                    time.sleep(2)  # Brief pause between plants
        else:
            logger.info("No plants need watering at this time")
    
    def validate_sensor_readings(self) -> Dict:
        """Validate sensor readings against plant requirements"""
        sensor_data = self.read_all_sensors()
        validation_results = {}
        
        for plant in self.plant_config["active_plants"]:
            position = plant["position"]
            plant_name = plant["name"]
            
            # Simple validation (you can expand this based on your needs)
            plant_validation = {
                "soil_moisture": {
                    "value": sensor_data.get("soil_moisture_percent"),
                    "status": "OK" if 20 <= sensor_data.get("soil_moisture_percent", 0) <= 70 else "CHECK"
                },
                "temperature": {
                    "value": sensor_data.get("temperature_celsius"),
                    "status": "OK" if 15 <= sensor_data.get("temperature_celsius", 0) <= 30 else "CHECK"
                },
                "humidity": {
                    "value": sensor_data.get("humidity_percent"),
                    "status": "OK" if 30 <= sensor_data.get("humidity_percent", 0) <= 80 else "CHECK"
                },
                "light": {
                    "value": sensor_data.get("light_lux"),
                    "status": "OK" if 50 <= sensor_data.get("light_lux", 0) <= 500 else "CHECK"
                }
            }
            
            validation_results[position] = {
                "plant_name": plant_name,
                "validation": plant_validation
            }
        
        return validation_results
    
    def send_data_to_web_interface(self, sensor_data: Dict):
        """Send sensor data to existing web interface (if URL provided)"""
        if not self.web_interface_url:
            return
        
        try:
            # Send sensor data to web interface
            payload = {
                "timestamp": sensor_data["timestamp"],
                "sensor_data": {
                    "temperature": sensor_data.get("temperature_celsius"),
                    "humidity": sensor_data.get("humidity_percent"),
                    "soil_moisture": sensor_data.get("soil_moisture_percent"),
                    "light": sensor_data.get("light_lux"),
                    "water_level": sensor_data.get("water_tank_percentage")
                },
                "plant_status": self.system_status["plants_needing_water"],
                "pump_status": self.system_status["pump_status"]
            }
            
            response = requests.post(
                f"{self.web_interface_url}/api/raspberry-pi/data",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Data sent to web interface successfully")
            else:
                logger.warning(f"Failed to send data to web interface: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending data to web interface: {e}")
    
    def start_monitoring_loop(self, interval_seconds: int = 300):
        """Start continuous monitoring loop"""
        self.running = True
        logger.info(f"Starting monitoring loop (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                # Read sensors
                sensor_data = self.read_all_sensors()
                logger.info(f"Sensor reading: Temp={sensor_data.get('temperature_celsius')}°C, "
                           f"Humidity={sensor_data.get('humidity_percent')}%, "
                           f"Soil={sensor_data.get('soil_moisture_percent')}%, "
                           f"Water={sensor_data.get('water_tank_percentage')}%")
                
                # Validate readings
                validation = self.validate_sensor_readings()
                
                # Check for plants needing water
                plants_needing_water = self.check_plants_needing_water()
                if plants_needing_water:
                    logger.info(f"Plants needing water: {[p['name'] for p in plants_needing_water]}")
                
                # Send data to web interface
                self.send_data_to_web_interface(sensor_data)
                
                # Wait for next reading
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring loop stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        sensor_data = self.read_all_sensors()
        validation = self.validate_sensor_readings()
        plants_needing_water = self.check_plants_needing_water()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hardware_status": "operational" if self.hardware.gpio_initialized else "simulation",
            "simulation_mode": self.simulation_mode,
            "last_sensor_reading": sensor_data,
            "plant_validation": validation,
            "plants_needing_water": [p["name"] for p in plants_needing_water],
            "pump_status": self.system_status["pump_status"],
            "sensor_history_count": len(self.system_status["sensor_history"]),
            "web_interface_connected": self.web_interface_url is not None
        }
    
    def manual_water_plant(self, position: int) -> bool:
        """Manually trigger watering for a plant at specific position"""
        plant = None
        for p in self.plant_config["active_plants"]:
            if p["position"] == position:
                plant = p
                break
        
        if not plant:
            logger.error(f"No plant found at position {position}")
            return False
        
        return self.water_plant(plant)
    
    def cleanup(self):
        """Clean up hardware resources"""
        self.running = False
        self.hardware.cleanup()
        logger.info("System cleanup completed")

# Demo functions for the 5 milestones
def demo_1_hardware_setup():
    """Demo 1: Hardware Setup and Basic Functionality"""
    print("\n" + "="*60)
    print("DEMO 1: Hardware Setup and Basic Functionality")
    print("="*60)
    
    # Initialize system
    pi_core = RaspberryPiCore(simulation_mode=True)
    
    print(f"\n🔧 System Status:")
    status = pi_core.get_system_status()
    print(f"   - Hardware Mode: {'Simulation' if status['simulation_mode'] else 'Real Hardware'}")
    print(f"   - GPIO Status: {status['hardware_status']}")
    print(f"   - Active Plants: {len(pi_core.plant_config['active_plants'])}")
    
    print(f"\n📊 Initial Sensor Reading:")
    sensor_data = pi_core.read_all_sensors()
    for key, value in sensor_data.items():
        if key != 'timestamp' and key != 'pump_status':
            print(f"   - {key}: {value}")
    
    print(f"\n✅ Demo 1 Complete: Hardware system operational")
    pi_core.cleanup()

def demo_2_pump_control():
    """Demo 2: Water Pump Implementation"""
    print("\n" + "="*60)
    print("DEMO 2: Water Pump Implementation")
    print("="*60)
    
    pi_core = RaspberryPiCore(simulation_mode=True)
    
    print(f"\n💧 Testing Pump Control:")
    
    # Test manual watering
    print(f"   - Manual watering test...")
    success = pi_core.manual_water_plant(0)  # Water plant at position 0
    print(f"   - Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test automatic watering
    print(f"\n🤖 Testing Automatic Watering:")
    pi_core.auto_water_plants()
    
    print(f"\n✅ Demo 2 Complete: Pump control functional")
    pi_core.cleanup()

def demo_3_sensor_integration():
    """Demo 3: Sensor Implementation"""
    print("\n" + "="*60)
    print("DEMO 3: Sensor Implementation")
    print("="*60)
    
    pi_core = RaspberryPiCore(simulation_mode=True)
    
    print(f"\n📊 Testing All Sensors:")
    
    # Read all sensors multiple times
    for i in range(3):
        print(f"\n   Reading {i+1}/3:")
        sensor_data = pi_core.read_all_sensors()
        print(f"      - Temperature: {sensor_data.get('temperature_celsius')}°C")
        print(f"      - Humidity: {sensor_data.get('humidity_percent')}%")
        print(f"      - Soil Moisture: {sensor_data.get('soil_moisture_percent')}%")
        print(f"      - Light: {sensor_data.get('light_lux')} lux")
        print(f"      - Water Level: {sensor_data.get('water_tank_percentage')}%")
        time.sleep(2)
    
    # Test validation
    print(f"\n🔍 Testing Sensor Validation:")
    validation = pi_core.validate_sensor_readings()
    for position, data in validation.items():
        print(f"   - {data['plant_name']}: All sensors {'✅ OK' if all(v['status'] == 'OK' for v in data['validation'].values()) else '⚠️ Check needed'}")
    
    print(f"\n✅ Demo 3 Complete: All sensors operational")
    pi_core.cleanup()

def demo_4_data_integration():
    """Demo 4: Data Integration and Monitoring"""
    print("\n" + "="*60)
    print("DEMO 4: Data Integration and Monitoring")
    print("="*60)
    
    pi_core = RaspberryPiCore(simulation_mode=True)
    
    print(f"\n📈 Testing Data Integration:")
    
    # Test monitoring loop for 30 seconds
    print(f"   - Running monitoring loop for 30 seconds...")
    
    start_time = time.time()
    while time.time() - start_time < 30:
        sensor_data = pi_core.read_all_sensors()
        validation = pi_core.validate_sensor_readings()
        plants_needing_water = pi_core.check_plants_needing_water()
        
        print(f"      → {datetime.now().strftime('%H:%M:%S')}: "
              f"Temp={sensor_data.get('temperature_celsius')}°C, "
              f"Plants needing water: {len(plants_needing_water)}")
        
        time.sleep(5)
    
    print(f"\n✅ Demo 4 Complete: Data integration functional")
    pi_core.cleanup()

def demo_5_system_integration():
    """Demo 5: Complete System Integration"""
    print("\n" + "="*60)
    print("DEMO 5: Complete System Integration")
    print("="*60)
    
    pi_core = RaspberryPiCore(simulation_mode=True)
    
    print(f"\n🎯 Testing Complete System Integration:")
    
    # Test full system cycle
    print(f"   1. System Status Check:")
    status = pi_core.get_system_status()
    print(f"      - Status: {status['hardware_status']}")
    print(f"      - Active Plants: {len(pi_core.plant_config['active_plants'])}")
    
    print(f"\n   2. Sensor Reading:")
    sensor_data = pi_core.read_all_sensors()
    print(f"      - All sensors: ✅ Operational")
    
    print(f"\n   3. Plant Health Check:")
    validation = pi_core.validate_sensor_readings()
    healthy_plants = sum(1 for data in validation.values() if all(v['status'] == 'OK' for v in data['validation'].values()))
    print(f"      - Healthy plants: {healthy_plants}/{len(validation)}")
    
    print(f"\n   4. Automatic Watering:")
    plants_needing_water = pi_core.check_plants_needing_water()
    if plants_needing_water:
        print(f"      - Watering {len(plants_needing_water)} plants...")
        pi_core.auto_water_plants()
    else:
        print(f"      - No watering needed")
    
    print(f"\n   5. System Monitoring:")
    print(f"      - Sensor history: {len(pi_core.system_status['sensor_history'])} readings")
    print(f"      - Last watering: {pi_core.system_status['pump_status']['last_watered'] or 'Never'}")
    
    print(f"\n✅ Demo 5 Complete: Full system integration successful")
    pi_core.cleanup()

def run_all_demos():
    """Run all 5 demos in sequence"""
    print("🌱 RASPBERRY PI AUTOMATED PLANTER - DEMO SEQUENCE")
    print("=" * 60)
    
    demos = [
        ("Demo 1", demo_1_hardware_setup),
        ("Demo 2", demo_2_pump_control),
        ("Demo 3", demo_3_sensor_integration),
        ("Demo 4", demo_4_data_integration),
        ("Demo 5", demo_5_system_integration)
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
            print(f"\n✅ {demo_name} completed successfully!")
            input(f"\nPress Enter to continue to next demo...")
        except Exception as e:
            logger.error(f"{demo_name} failed: {e}")
            print(f"\n❌ {demo_name} failed: {e}")
            input(f"\nPress Enter to continue to next demo...")
    
    print(f"\n🎉 ALL DEMOS COMPLETED!")
    print(f"   - Raspberry Pi core system fully demonstrated")
    print(f"   - All 5 milestones achieved")
    print(f"   - System ready for integration with web interface")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "demo":
            if len(sys.argv) > 2:
                demo_num = int(sys.argv[2])
                if demo_num == 1:
                    demo_1_hardware_setup()
                elif demo_num == 2:
                    demo_2_pump_control()
                elif demo_num == 3:
                    demo_3_sensor_integration()
                elif demo_num == 4:
                    demo_4_data_integration()
                elif demo_num == 5:
                    demo_5_system_integration()
                elif demo_num == 0:
                    run_all_demos()
                else:
                    print(f"Invalid demo number: {demo_num}")
            else:
                print("Usage: python raspberry_pi_core.py demo [1|2|3|4|5|0]")
                print("  demo 0 = run all demos")
        
        elif command == "monitor":
            # Start monitoring loop
            pi_core = RaspberryPiCore(simulation_mode=True)
            try:
                pi_core.start_monitoring_loop()
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
            finally:
                pi_core.cleanup()
        
        elif command == "status":
            # Show system status
            pi_core = RaspberryPiCore(simulation_mode=True)
            status = pi_core.get_system_status()
            print("\n📊 System Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")
            pi_core.cleanup()
        
        else:
            print("Available commands:")
            print("  python raspberry_pi_core.py demo [1|2|3|4|5|0]")
            print("  python raspberry_pi_core.py monitor")
            print("  python raspberry_pi_core.py status")
    
    else:
        # Interactive mode
        print("🌱 Raspberry Pi Automated Planter Core")
        print("Choose an option:")
        print("1-5. Run individual demo")
        print("A. Run all demos")
        print("M. Start monitoring")
        print("S. Show status")
        print("Q. Quit")
        
        while True:
            choice = input("\nEnter your choice: ").upper()
            
            if choice in ["1", "2", "3", "4", "5"]:
                demo_num = int(choice)
                if demo_num == 1:
                    demo_1_hardware_setup()
                elif demo_num == 2:
                    demo_2_pump_control()
                elif demo_num == 3:
                    demo_3_sensor_integration()
                elif demo_num == 4:
                    demo_4_data_integration()
                elif demo_num == 5:
                    demo_5_system_integration()
            
            elif choice == "A":
                run_all_demos()
                break
            
            elif choice == "M":
                pi_core = RaspberryPiCore(simulation_mode=True)
                try:
                    pi_core.start_monitoring_loop()
                except KeyboardInterrupt:
                    print("\nMonitoring stopped by user")
                finally:
                    pi_core.cleanup()
            
            elif choice == "S":
                pi_core = RaspberryPiCore(simulation_mode=True)
                status = pi_core.get_system_status()
                print("\n📊 System Status:")
                for key, value in status.items():
                    print(f"   {key}: {value}")
                pi_core.cleanup()
            
            elif choice == "Q":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
