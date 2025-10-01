# Integration Guide: Raspberry Pi + AutomatedPlanterSite

This guide shows how to integrate your Raspberry Pi hardware with your existing `AutomatedPlanterSite` web interface and database.

## 🎯 Integration Overview

The integrated system connects your Raspberry Pi sensors to your existing website database, allowing you to:
- **Use your existing plant database** from AutomatedPlanterSite
- **Send real-time sensor data** to your website
- **Display live sensor readings** on your web interface
- **Trigger automatic watering** based on website data
- **Maintain a single database** for all plant and sensor data

## 🏗️ System Architecture

```
Raspberry Pi Hardware
├── Sensors (DHT22, Soil Moisture, Light, Water Level)
├── Actuators (Pumps, LEDs)
└── Raspberry Pi Software
    ├── hardware_drivers.py
    ├── integrated_system.py
    └── website_database_client.py
           ↓ (HTTP API calls)
AutomatedPlanterSite
├── Next.js Web Interface
├── SQLite Database (plants.db)
├── Plant Management System
└── Real-time Sensor Display
```

## 🚀 Setup Instructions

### Step 1: Prepare Your AutomatedPlanterSite

1. **Start your AutomatedPlanterSite**:
   ```bash
   cd /path/to/AutomatedPlanterSite
   npm run dev
   ```
   Your website should be running on `http://localhost:3000`

2. **Verify your database** has the plant data you want to use

### Step 2: Set Up Raspberry Pi Integration

1. **Install dependencies**:
   ```bash
   cd /path/to/AutomatedPlanter
   pip3 install -r requirements.txt
   ```

2. **Test the integration**:
   ```bash
   # Test connection to your website
   python3 website_database_client.py
   ```

### Step 3: Run the Integrated System

#### Option A: Simple Integration (Recommended)
```bash
# Run the integrated system
python3 integrated_system.py monitor http://localhost:3000
```

This will:
- Connect to your AutomatedPlanterSite database
- Read sensor data every 5 minutes
- Send data to your website
- Check for plants needing water
- Trigger automatic watering

#### Option B: Demo Mode
```bash
# Run all 5 integrated demos
python3 integrated_system.py demo 0
```

This will run all 5 milestone demos showing the complete integration.

### Step 4: View Live Data

1. **Open your AutomatedPlanterSite** in a web browser
2. **Check the sensor data** - it should now show live readings from your Raspberry Pi
3. **Monitor plant status** - automatic watering will be logged in your database

## 📊 Data Flow

### Sensor Data Flow
```
Raspberry Pi Sensors → hardware_drivers.py → integrated_system.py → 
website_database_client.py → AutomatedPlanterSite API → 
SQLite Database → Web Interface Display
```

### Watering Control Flow
```
Website Database → website_database_client.py → integrated_system.py → 
hardware_drivers.py → Raspberry Pi Pumps → 
Watering Event → Database Log → Web Interface Update
```

## 🔧 Configuration

### Raspberry Pi Configuration
The system automatically configures itself based on your hardware:

```python
# GPIO Pin Assignments (automatically configured)
GPIO_CONFIG = {
    "dht22_pin": 4,           # Temperature/humidity
    "soil_moisture_pin": 18,  # Soil moisture
    "light_sensor_sda": 2,    # Light sensor I2C
    "light_sensor_scl": 3,    # Light sensor I2C
    "water_level_pins": [5, 6, 7],  # Water level sensors
    "pump1_pin": 23,          # Pump 1
    "pump2_pin": 24,          # Pump 2
    "pump_enable_pin": 25,    # MOSFET enable
}
```

### Website Integration Settings
```python
# Default settings (automatically configured)
INTEGRATION_SETTINGS = {
    "sensor_reading_interval": 300,  # 5 minutes
    "data_log_interval": 3600,       # 1 hour
    "pump_flow_rate": 100,           # ml per second
    "safety_timeout": 30,            # seconds
}
```

## 🎯 Your 5 Milestone Demos

### Demo 1: Website Integration and Database Connection
```bash
python3 integrated_system.py demo 1
```
- Tests connection to your AutomatedPlanterSite
- Retrieves plant data from your existing database
- Verifies sensor data can be sent to your website

### Demo 2: Real-time Data Synchronization
```bash
python3 integrated_system.py demo 2
```
- Sends live sensor data to your website every 10 seconds
- Shows real-time data updates in your web interface
- Demonstrates continuous data synchronization

### Demo 3: Automatic Watering Based on Website Data
```bash
python3 integrated_system.py demo 3
```
- Checks your website database for plants needing water
- Triggers automatic watering based on plant requirements
- Logs watering events back to your database

### Demo 4: Complete System Integration
```bash
python3 integrated_system.py demo 4
```
- Tests all components working together
- Verifies complete data pipeline
- Shows full system integration

### Demo 5: Production System with Touch Screen
```bash
python3 integrated_system.py demo 5
```
- Simulates production system operation
- Tests touch screen interface integration
- Demonstrates continuous monitoring

## 🌐 Web Interface Integration

### Sensor Data Display
Your AutomatedPlanterSite will now show:
- **Live temperature readings** from DHT22 sensor
- **Real-time humidity levels** from DHT22 sensor
- **Current soil moisture** from capacitive sensor
- **Ambient light levels** from digital light sensor
- **Water tank levels** from contact sensors

### Plant Management Integration
- **Use your existing plant database** - no need to recreate plants
- **Automatic watering** based on your plant care schedules
- **Watering event logging** in your database
- **Plant health monitoring** with sensor validation

### Dashboard Updates
Your web interface will automatically update with:
- **Live sensor graphs** showing real-time data
- **Plant status indicators** based on sensor readings
- **Watering history** from automatic system
- **System health status** from Raspberry Pi

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test website connection
python3 -c "from website_database_client import WebsiteDatabaseClient; c = WebsiteDatabaseClient('http://localhost:3000'); print('Connected!' if c.test_connection() else 'Failed')"
```

### Sensor Issues
```bash
# Test sensor reading
python3 -c "from hardware_drivers import HardwareInterface; h = HardwareInterface(True); print(h.read_all_sensors())"
```

### Database Issues
```bash
# Test database operations
python3 -c "from website_database_client import WebsiteDatabaseClient; c = WebsiteDatabaseClient('http://localhost:3000'); print(f'Found {len(c.get_all_plants())} plants')"
```

## 📱 Touch Screen Integration

Your 7" touch screen will display:
- **Live sensor readings** updated every 5 minutes
- **Plant status** from your website database
- **Manual watering controls** for each plant
- **System status** and health indicators
- **Water tank level** with visual indicators

## 🚀 Production Deployment

### For Real Hardware
1. **Connect all sensors** to Raspberry Pi GPIO pins
2. **Install hardware libraries**:
   ```bash
   pip3 install RPi.GPIO Adafruit_DHT smbus spidev
   ```
3. **Run without simulation mode**:
   ```bash
   python3 integrated_system.py monitor http://localhost:3000
   ```

### For Continuous Operation
1. **Create a systemd service** for automatic startup
2. **Set up log rotation** for sensor data
3. **Configure automatic restart** on failure
4. **Set up monitoring** for system health

## 📊 Database Schema

The integration adds these tables to your existing database:

```sql
-- Sensor data from Raspberry Pi
CREATE TABLE sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    temperature REAL,
    humidity REAL,
    soil_moisture REAL,
    light_level REAL,
    water_level REAL,
    source TEXT DEFAULT 'raspberry_pi'
);

-- Watering events from automatic system
CREATE TABLE watering_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    water_amount REAL NOT NULL,
    success BOOLEAN NOT NULL,
    timestamp DATETIME NOT NULL,
    source TEXT DEFAULT 'raspberry_pi',
    FOREIGN KEY (plant_id) REFERENCES plants (id)
);

-- Hardware configuration
CREATE TABLE hardware_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hardware_id TEXT UNIQUE NOT NULL,
    config TEXT NOT NULL,
    timestamp DATETIME NOT NULL
);
```

## 🎓 Educational Benefits

This integration demonstrates:
- **Full-stack development** - hardware to web interface
- **Database integration** - real-time data synchronization
- **API development** - RESTful endpoints for data exchange
- **System integration** - multiple components working together
- **Real-world application** - practical IoT system implementation

## 📞 Support

If you encounter issues:
1. **Check the logs** for error messages
2. **Verify website connection** with test commands
3. **Test individual components** with demo scripts
4. **Check GPIO connections** for hardware issues

---

**Your integrated system is now ready!** 🌱

The Raspberry Pi will send live sensor data to your AutomatedPlanterSite, and your website will display real-time plant monitoring with automatic watering capabilities.
