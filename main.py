#!/usr/bin/env python3
"""
Main Application for Automated Planter
Integrates plant database, configuration, hardware drivers, and web interface
Based on 5 milestone demos for senior project
"""

import sys
import os
import time
import json
import threading
from datetime import datetime
from plant_database import PlantDatabase
from plant_config import PlantConfig
from hardware_drivers import HardwareInterface
from web_interface import app, create_templates
from demo_milestones import AutomatedPlanterDemo

class AutomatedPlanter:
    def __init__(self, simulation_mode: bool = True):
        """Initialize the automated planter system"""
        self.db = PlantDatabase()
        self.config = PlantConfig()
        self.hardware = HardwareInterface(simulation_mode=simulation_mode)
        self.running = False
        self.demo_system = AutomatedPlanterDemo(simulation_mode=simulation_mode)
        
        print("🌱 Automated Planter System Initialized")
        print(f"   - Plant database: {len(self.db.get_all_plants())} plants available")
        print(f"   - Active plants: {len(self.config.config['active_plants'])}")
        print(f"   - Sensors enabled: {sum(1 for s in self.config.config['sensors'].values() if s['enabled'])}")
        print(f"   - Actuators enabled: {sum(1 for a in self.config.config['actuators'].values() if a['enabled'])}")
        print(f"   - Hardware mode: {'Simulation' if simulation_mode else 'Real Hardware'}")
        print(f"   - GPIO status: {'Initialized' if self.hardware.gpio_initialized else 'Not initialized'}")
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        print("🔄 Starting monitoring loop...")
        
        while self.running:
            try:
                self.check_plants()
                self.log_sensor_data()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitoring loop...")
                self.running = False
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def run_demo(self, demo_number: int):
        """Run a specific demo milestone"""
        print(f"\n🎯 Running Demo {demo_number}...")
        
        if demo_number == 1:
            self.demo_system.demo_1_plant_ui_database()
        elif demo_number == 2:
            self.demo_system.demo_2_water_pump_implementation()
        elif demo_number == 3:
            self.demo_system.demo_3_sensor_implementation()
        elif demo_number == 4:
            self.demo_system.demo_4_sensors_database_ui_sync()
        elif demo_number == 5:
            self.demo_system.demo_5_system_integration_touchscreen()
        else:
            print(f"❌ Invalid demo number: {demo_number}")
    
    def run_all_demos(self):
        """Run all 5 demo milestones"""
        self.demo_system.run_all_demos()
    
    def check_plants(self):
        """Check all plants and take necessary actions"""
        plants_needing_water = self.config.get_plants_needing_water()
        
        if plants_needing_water:
            print(f"💧 {len(plants_needing_water)} plants need watering:")
            for plant in plants_needing_water:
                print(f"   - {plant['name']} at position {plant['position']}")
                # Here you would trigger the actual watering mechanism
                self.trigger_watering(plant['position'])
    
    def trigger_watering(self, position):
        """Trigger watering for a plant at specific position"""
        plant = self.config.get_plant_at_position(position)
        if not plant:
            return
        
        water_amount = plant['custom_settings']['water_amount']
        print(f"🚿 Watering {plant['name']} with {water_amount}ml")
        
        # Calculate pump duration (assuming 100ml per second flow rate)
        duration = water_amount / 100.0  # seconds
        pump_num = (position % 2) + 1  # Alternate between pumps
        
        # Control the actual water pump
        success = self.hardware.control_pump(pump_num, duration, water_amount)
        
        if success:
            # Update watering time
            self.config.update_watering_time(position)
            self.config.update_plant_status(position, "active")
            print(f"✅ Watering completed successfully")
        else:
            print(f"❌ Watering failed")
    
    def log_sensor_data(self):
        """Log sensor data from hardware"""
        # Read all sensors from hardware
        sensor_data = self.hardware.read_all_sensors()
        
        # Validate readings against plant requirements
        for plant in self.config.config['active_plants']:
            position = plant['position']
            plant_name = plant['name']
            
            # Validate each sensor reading
            sensor_types = ['soil_moisture', 'temperature', 'humidity', 'light']
            for sensor_type in sensor_types:
                value = sensor_data.get(f"{sensor_type}_percent") or sensor_data.get(f"{sensor_type}_celsius") or sensor_data.get(f"{sensor_type}_lux")
                if value is not None:
                    validation = self.config.validate_sensor_reading(position, sensor_type, value)
                    if not validation['valid']:
                        print(f"⚠️  {plant_name}: {validation['message']}")
                        
                        # Take automatic action if needed
                        if validation['action'] == 'water':
                            print(f"🚿 Auto-watering {plant_name} due to {sensor_type}")
                            self.trigger_watering(position)
    
    def start_web_interface(self):
        """Start the web interface"""
        print("🌐 Starting web interface...")
        create_templates()  # Create HTML templates
        
        # Get configuration
        web_config = self.config.config['system']['web_interface']
        host = web_config['host']
        port = web_config['port']
        
        print(f"   - Access at: http://{host}:{port}")
        print(f"   - Local access: http://localhost:{port}")
        
        app.run(host=host, port=port, debug=False)
    
    def show_status(self):
        """Show current system status"""
        print("\n📊 System Status:")
        print("=" * 50)
        
        # Plant status
        active_plants = self.config.config['active_plants']
        print(f"Active Plants: {len(active_plants)}")
        for plant in active_plants:
            print(f"  - {plant['name']} (Position {plant['position']}) - {plant['status']}")
        
        # Plants needing water
        plants_needing_water = self.config.get_plants_needing_water()
        print(f"\nPlants Needing Water: {len(plants_needing_water)}")
        for plant in plants_needing_water:
            print(f"  - {plant['name']} (Position {plant['position']})")
        
        # System configuration
        print(f"\nSystem Configuration:")
        print(f"  - Sensors: {sum(1 for s in self.config.config['sensors'].values() if s['enabled'])} enabled")
        print(f"  - Actuators: {sum(1 for a in self.config.config['actuators'].values() if a['enabled'])} enabled")
        print(f"  - Web Interface: {'Enabled' if self.config.config['system']['web_interface']['enabled'] else 'Disabled'}")
    
    def setup_demo_plants(self):
        """Set up some demo plants for testing"""
        print("🌱 Setting up demo plants...")
        
        # Add some common plants
        demo_plants = [
            ("Snake Plant", 0),
            ("Peace Lily", 1),
            ("Spider Plant", 2)
        ]
        
        for plant_name, position in demo_plants:
            success = self.config.add_plant(plant_name, position)
            if success:
                print(f"  ✅ Added {plant_name} at position {position}")
            else:
                print(f"  ❌ Failed to add {plant_name} at position {position}")

def main():
    """Main application entry point"""
    print("🌱 Automated Planter System")
    print("=" * 40)
    
    # Check for simulation mode
    simulation_mode = "--simulation" in sys.argv or "-s" in sys.argv
    if simulation_mode:
        sys.argv.remove("--simulation" if "--simulation" in sys.argv else "-s")
    
    # Initialize system
    planter = AutomatedPlanter(simulation_mode=simulation_mode)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "web":
            # Start web interface only
            planter.start_web_interface()
        
        elif command == "monitor":
            # Start monitoring only
            planter.start_monitoring()
        
        elif command == "status":
            # Show status
            planter.show_status()
        
        elif command == "setup":
            # Setup demo plants
            planter.setup_demo_plants()
        
        elif command == "demo":
            # Run demos
            if len(sys.argv) > 2:
                demo_num = int(sys.argv[2])
                planter.run_demo(demo_num)
            else:
                print("Please specify demo number (1-5) or 'all'")
                print("Usage: python main.py demo [1|2|3|4|5|all]")
        
        elif command == "help":
            print("\nAvailable commands:")
            print("  python main.py web      - Start web interface")
            print("  python main.py monitor   - Start monitoring loop")
            print("  python main.py status    - Show system status")
            print("  python main.py setup     - Setup demo plants")
            print("  python main.py demo N    - Run demo N (1-5)")
            print("  python main.py demo all  - Run all demos")
            print("  python main.py help      - Show this help")
            print("\nOptions:")
            print("  --simulation, -s        - Use simulation mode")
            print("\nDefault: Start both web interface and monitoring")
        
        else:
            print(f"Unknown command: {command}")
            print("Use 'python main.py help' for available commands")
    
    else:
        # Default: start both web interface and monitoring
        print("\nStarting full system...")
        print("Press Ctrl+C to stop")
        
        try:
            # Start monitoring in background
            monitor_thread = threading.Thread(target=planter.start_monitoring)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Start web interface (main thread)
            planter.start_web_interface()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            planter.running = False
            planter.hardware.cleanup()

if __name__ == "__main__":
    main()
