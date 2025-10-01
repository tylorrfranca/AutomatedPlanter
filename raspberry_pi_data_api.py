#!/usr/bin/env python3
"""
Raspberry Pi Data API
Simple API endpoints for AutomatedPlanterSite to receive sensor data
"""

from flask import Flask, jsonify, request
import json
import sqlite3
from datetime import datetime
from typing import Dict, List

app = Flask(__name__)

# Database setup (this will integrate with your existing database)
def init_database():
    """Initialize database tables for sensor data"""
    conn = sqlite3.connect('plants.db')  # Use your existing database
    cursor = conn.cursor()
    
    # Create sensor_data table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            temperature REAL,
            humidity REAL,
            soil_moisture REAL,
            light_level REAL,
            water_level REAL,
            source TEXT DEFAULT 'raspberry_pi',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create watering_events table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watering_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            water_amount REAL NOT NULL,
            success BOOLEAN NOT NULL,
            timestamp DATETIME NOT NULL,
            source TEXT DEFAULT 'raspberry_pi',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants (id)
        )
    ''')
    
    # Create hardware_config table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT UNIQUE NOT NULL,
            config TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """API status endpoint"""
    return jsonify({
        "status": "Raspberry Pi Data API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "sensor_data": "POST /api/sensor-data",
            "watering_events": "POST /api/watering-events",
            "hardware_config": "POST /api/hardware/config",
            "latest_data": "GET /api/sensor-data/latest",
            "watering_history": "GET /api/watering-events"
        }
    })

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from Raspberry Pi"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract sensor data
        timestamp = data.get('timestamp', datetime.now().isoformat())
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        soil_moisture = data.get('soil_moisture')
        light_level = data.get('light_level')
        water_level = data.get('water_level')
        source = data.get('source', 'raspberry_pi')
        
        # Store in database
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sensor_data 
            (timestamp, temperature, humidity, soil_moisture, light_level, water_level, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, temperature, humidity, soil_moisture, light_level, water_level, source))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "Sensor data received and stored",
            "timestamp": timestamp,
            "stored": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/watering-events', methods=['POST'])
def receive_watering_event():
    """Receive watering event data from Raspberry Pi"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract watering event data
        plant_id = data.get('plant_id')
        water_amount = data.get('water_amount')
        success = data.get('success', False)
        timestamp = data.get('timestamp', datetime.now().isoformat())
        source = data.get('source', 'raspberry_pi')
        
        if not plant_id or not water_amount:
            return jsonify({"error": "plant_id and water_amount are required"}), 400
        
        # Store in database
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO watering_events 
            (plant_id, water_amount, success, timestamp, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (plant_id, water_amount, success, timestamp, source))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "Watering event received and stored",
            "plant_id": plant_id,
            "water_amount": water_amount,
            "success": success,
            "timestamp": timestamp,
            "stored": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hardware/config', methods=['POST'])
def receive_hardware_config():
    """Receive hardware configuration from Raspberry Pi"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        hardware_id = data.get('hardware_id')
        config = data.get('config')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if not hardware_id or not config:
            return jsonify({"error": "hardware_id and config are required"}), 400
        
        # Store in database
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        # Update or insert hardware config
        cursor.execute('''
            INSERT OR REPLACE INTO hardware_config 
            (hardware_id, config, timestamp)
            VALUES (?, ?, ?)
        ''', (hardware_id, json.dumps(config), timestamp))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "Hardware configuration received and stored",
            "hardware_id": hardware_id,
            "timestamp": timestamp,
            "stored": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensor-data/latest')
def get_latest_sensor_data():
    """Get latest sensor data"""
    try:
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        latest = cursor.fetchone()
        conn.close()
        
        if latest:
            return jsonify({
                "id": latest[0],
                "timestamp": latest[1],
                "temperature": latest[2],
                "humidity": latest[3],
                "soil_moisture": latest[4],
                "light_level": latest[5],
                "water_level": latest[6],
                "source": latest[7],
                "created_at": latest[8]
            })
        else:
            return jsonify({"message": "No sensor data available"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensor-data/history')
def get_sensor_data_history():
    """Get sensor data history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        
        data = []
        for row in history:
            data.append({
                "id": row[0],
                "timestamp": row[1],
                "temperature": row[2],
                "humidity": row[3],
                "soil_moisture": row[4],
                "light_level": row[5],
                "water_level": row[6],
                "source": row[7],
                "created_at": row[8]
            })
        
        return jsonify({
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/watering-events')
def get_watering_events():
    """Get watering events history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT we.*, p.name as plant_name 
            FROM watering_events we
            LEFT JOIN plants p ON we.plant_id = p.id
            ORDER BY we.timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        events = cursor.fetchall()
        conn.close()
        
        data = []
        for row in events:
            data.append({
                "id": row[0],
                "plant_id": row[1],
                "plant_name": row[6],
                "water_amount": row[2],
                "success": bool(row[3]),
                "timestamp": row[4],
                "source": row[5],
                "created_at": row[7]
            })
        
        return jsonify({
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hardware/status')
def get_hardware_status():
    """Get hardware status and configuration"""
    try:
        conn = sqlite3.connect('plants.db')
        cursor = conn.cursor()
        
        # Get latest hardware config
        cursor.execute('''
            SELECT * FROM hardware_config 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        config_row = cursor.fetchone()
        
        # Get latest sensor data
        cursor.execute('''
            SELECT timestamp, temperature, humidity, soil_moisture, light_level, water_level
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        sensor_row = cursor.fetchone()
        
        conn.close()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "hardware_connected": config_row is not None,
            "last_sensor_reading": sensor_row[0] if sensor_row else None,
            "current_sensors": {
                "temperature": sensor_row[1] if sensor_row else None,
                "humidity": sensor_row[2] if sensor_row else None,
                "soil_moisture": sensor_row[3] if sensor_row else None,
                "light_level": sensor_row[4] if sensor_row else None,
                "water_level": sensor_row[5] if sensor_row else None
            }
        }
        
        if config_row:
            status["hardware_config"] = json.loads(config_row[2])
            status["hardware_id"] = config_row[1]
            status["config_timestamp"] = config_row[3]
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    print("🌱 Raspberry Pi Data API Server")
    print("=" * 40)
    print("This API receives data from your Raspberry Pi")
    print("and stores it in your AutomatedPlanterSite database")
    print("=" * 40)
    print("Endpoints:")
    print("  POST /api/sensor-data      - Receive sensor readings")
    print("  POST /api/watering-events  - Receive watering events")
    print("  POST /api/hardware/config  - Receive hardware config")
    print("  GET  /api/sensor-data/latest    - Get latest sensor data")
    print("  GET  /api/sensor-data/history   - Get sensor data history")
    print("  GET  /api/watering-events       - Get watering events")
    print("  GET  /api/hardware/status       - Get hardware status")
    print("=" * 40)
    print("Server: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
