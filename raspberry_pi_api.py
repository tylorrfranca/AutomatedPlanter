#!/usr/bin/env python3
"""
Raspberry Pi API Server
Simple API to communicate with existing AutomatedPlanterSite
"""

from flask import Flask, jsonify, request
import json
import threading
from datetime import datetime
from raspberry_pi_core import RaspberryPiCore

app = Flask(__name__)

# Global Raspberry Pi core instance
pi_core = None

@app.route('/')
def index():
    """API status endpoint"""
    return jsonify({
        "status": "Raspberry Pi Automated Planter API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/status')
def get_status():
    """Get system status"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    status = pi_core.get_system_status()
    return jsonify(status)

@app.route('/api/sensors')
def get_sensors():
    """Get current sensor readings"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    sensor_data = pi_core.read_all_sensors()
    return jsonify(sensor_data)

@app.route('/api/plants/status')
def get_plants_status():
    """Get plant status and validation"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    validation = pi_core.validate_sensor_readings()
    plants_needing_water = pi_core.check_plants_needing_water()
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "plant_validation": validation,
        "plants_needing_water": [p["name"] for p in plants_needing_water],
        "active_plants": pi_core.plant_config["active_plants"]
    })

@app.route('/api/water/<int:position>', methods=['POST'])
def water_plant(position):
    """Manually trigger watering for a plant at specific position"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    success = pi_core.manual_water_plant(position)
    
    if success:
        return jsonify({
            "message": f"Successfully watered plant at position {position}",
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"error": f"Failed to water plant at position {position}"}), 400

@app.route('/api/water/all', methods=['POST'])
def water_all_plants():
    """Water all plants that need it"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    plants_needing_water = pi_core.check_plants_needing_water()
    
    if not plants_needing_water:
        return jsonify({
            "message": "No plants need watering",
            "timestamp": datetime.now().isoformat()
        })
    
    # Water all plants that need it
    watered_plants = []
    for plant in plants_needing_water:
        success = pi_core.water_plant(plant)
        watered_plants.append({
            "plant": plant["name"],
            "position": plant["position"],
            "success": success
        })
    
    return jsonify({
        "message": f"Watered {len(watered_plants)} plants",
        "watered_plants": watered_plants,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/sensors/history')
def get_sensor_history():
    """Get sensor reading history"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    history = pi_core.system_status["sensor_history"]
    
    # Get last N readings (default 10)
    limit = request.args.get('limit', 10, type=int)
    recent_history = history[-limit:] if history else []
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "history": recent_history,
        "total_readings": len(history)
    })

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update system configuration"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    if request.method == 'GET':
        return jsonify({
            "plant_config": pi_core.plant_config,
            "system_status": pi_core.system_status,
            "simulation_mode": pi_core.simulation_mode,
            "web_interface_url": pi_core.web_interface_url
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Update plant configuration
        if 'plant_config' in data:
            pi_core.plant_config.update(data['plant_config'])
        
        return jsonify({
            "message": "Configuration updated",
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/demo/<int:demo_number>', methods=['POST'])
def run_demo(demo_number):
    """Run a specific demo milestone"""
    if not pi_core:
        return jsonify({"error": "System not initialized"}), 500
    
    if demo_number < 1 or demo_number > 5:
        return jsonify({"error": "Invalid demo number. Must be 1-5"}), 400
    
    # Run demo in background thread
    def run_demo_thread():
        try:
            if demo_number == 1:
                from raspberry_pi_core import demo_1_hardware_setup
                demo_1_hardware_setup()
            elif demo_number == 2:
                from raspberry_pi_core import demo_2_pump_control
                demo_2_pump_control()
            elif demo_number == 3:
                from raspberry_pi_core import demo_3_sensor_integration
                demo_3_sensor_integration()
            elif demo_number == 4:
                from raspberry_pi_core import demo_4_data_integration
                demo_4_data_integration()
            elif demo_number == 5:
                from raspberry_pi_core import demo_5_system_integration
                demo_5_system_integration()
        except Exception as e:
            print(f"Demo {demo_number} failed: {e}")
    
    thread = threading.Thread(target=run_demo_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": f"Demo {demo_number} started",
        "timestamp": datetime.now().isoformat()
    })

def initialize_pi_core(simulation_mode=True, web_interface_url=None):
    """Initialize the Raspberry Pi core system"""
    global pi_core
    pi_core = RaspberryPiCore(simulation_mode=simulation_mode, web_interface_url=web_interface_url)
    return pi_core

if __name__ == "__main__":
    import sys
    
    # Initialize Raspberry Pi core
    simulation_mode = "--simulation" in sys.argv or "-s" in sys.argv
    if simulation_mode:
        sys.argv.remove("--simulation" if "--simulation" in sys.argv else "-s")
    
    # Optional: Connect to existing web interface
    web_interface_url = None
    if "--web-url" in sys.argv:
        idx = sys.argv.index("--web-url")
        if idx + 1 < len(sys.argv):
            web_interface_url = sys.argv[idx + 1]
            sys.argv.remove("--web-url")
            sys.argv.remove(web_interface_url)
    
    # Initialize system
    pi_core = initialize_pi_core(simulation_mode=simulation_mode, web_interface_url=web_interface_url)
    
    print("🌱 Raspberry Pi Automated Planter API Server")
    print("=" * 50)
    print(f"Mode: {'Simulation' if simulation_mode else 'Real Hardware'}")
    if web_interface_url:
        print(f"Web Interface: {web_interface_url}")
    print(f"API Server: http://localhost:5000")
    print(f"Endpoints:")
    print(f"  GET  /api/status          - System status")
    print(f"  GET  /api/sensors         - Current sensor readings")
    print(f"  GET  /api/plants/status   - Plant status and validation")
    print(f"  POST /api/water/<pos>     - Water specific plant")
    print(f"  POST /api/water/all       - Water all plants needing it")
    print(f"  GET  /api/sensors/history - Sensor reading history")
    print(f"  GET  /api/config          - Get configuration")
    print(f"  POST /api/config          - Update configuration")
    print(f"  POST /api/demo/<num>      - Run demo milestone (1-5)")
    print("=" * 50)
    
    # Start API server
    app.run(host='0.0.0.0', port=5000, debug=False)
