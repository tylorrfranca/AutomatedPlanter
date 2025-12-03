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
    ├── hardware_drivers.c/h
    ├── raspberry_pi_core.c/h
    ├── main.c
    └── demo_milestones.c
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
   sudo apt-get update
   sudo apt-get install -y libgpiod-dev libjson-c-dev libcurl4-openssl-dev pkg-config gcc make
   ```

2. **Build the C application**:
   ```bash
   make clean && make
   ```

3. **Available commands**:
   ```bash
   # Show system status
   ./automated_planter status
   
   # Start monitoring loop (default behavior)
   ./automated_planter monitor
   
   # Run specific demo
   ./automated_planter demo 1    # Individual demo (1-5)
   ./automated_planter demo all  # Run all demos
   
   # Run with options
   ./automated_planter --simulation monitor              # Simulation mode
   ./automated_planter --web-url http://localhost:3000 monitor  # With web interface
   ```

4. **Test the integration**:
   ```bash
   # Test system status
   ./automated_planter status
   
   # Test in simulation mode with web connection
   ./automated_planter --simulation --web-url http://localhost:3000 status
   ```

### Step 3: Run the Integrated System

#### Option A: Simple Integration (Recommended)
```bash
# Run the integrated system with web interface connection
./automated_planter --web-url http://localhost:3000 monitor
```

This will:
- Connect to your AutomatedPlanterSite database
- Read sensor data every minute
- Send data to your website
- Check for plants needing water
- Trigger automatic watering

#### Option B: Demo Mode
```bash
# Run all 5 integrated demos
./demo_milestones all

# Or run individual demos
./automated_planter demo all
```

This will run all 5 milestone demos showing the complete integration.

### Step 4: View Live Data

1. **Open your AutomatedPlanterSite** in a web browser
2. **Check the sensor data** - it should now show live readings from your Raspberry Pi
3. **Monitor plant status** - automatic watering will be logged in your database

## 📊 Data Flow

### Sensor Data Flow
```
Raspberry Pi Sensors → hardware_drivers.c → raspberry_pi_core.c → 
main.c → AutomatedPlanterSite API → 
SQLite Database → Web Interface Display
```

### Watering Control Flow
```
Website Database → raspberry_pi_core.c → main.c → 
hardware_drivers.c → Raspberry Pi Pumps → 
Watering Event → Database Log → Web Interface Update
```

## 🔧 Configuration

### Raspberry Pi Configuration
The system automatically configures itself based on your hardware:

```c
// GPIO Pin Assignments (defined in hardware_drivers.h)
#define DHT22_PIN 4           // Temperature/humidity
#define SOIL_MOISTURE_PIN 18 // Soil moisture
#define LIGHT_SENSOR_SDA 2    // Light sensor I2C
#define LIGHT_SENSOR_SCL 3    // Light sensor I2C
#define WATER_LEVEL_PINS {5, 6, 7}  // Water level sensors
#define PUMP1_PIN 23          // Pump 1
#define PUMP2_PIN 24          // Pump 2
#define PUMP_ENABLE_PIN 25    // MOSFET enable
```

### Website Integration Settings
The system uses built-in configuration with these defaults:
- **Sensor reading interval**: 60 seconds (1 minute)
- **Data logging**: Real-time as sensor data changes
- **Pump flow rate**: Configurable per plant
- **Safety timeout**: 30 seconds maximum watering duration

## 🎯 Your 5 Milestone Demos

### Demo 1: Hardware Setup and Basic Functionality
```bash
./automated_planter demo 1
```
- Tests hardware initialization and GPIO setup
- Verifies sensor reading capabilities
- Tests basic pump control functionality

### Demo 2: Pump Control and Actuator Testing
```bash
./automated_planter demo 2
```
- Demonstrates individual pump control
- Tests water delivery system
- Verifies actuator response and timing

### Demo 3: Sensor Integration and Data Reading
```bash
./automated_planter demo 3
```
- Shows all sensor readings (temperature, humidity, moisture, light)
- Tests data validation and error handling
- Demonstrates sensor calibration

### Demo 4: Database Integration and Web Communication
```bash
./automated_planter demo 4
```
- Tests connection to AutomatedPlanterSite API
- Sends sensor data to website database
- Retrieves plant configuration from web interface

### Demo 5: Complete System Integration
```bash
./automated_planter demo 5
```
- Runs full system integration test
- Demonstrates automatic watering based on sensor data
- Shows complete data flow from sensors to web interface

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
# Test system status and web connection
./automated_planter --web-url http://localhost:3000 status

# Test in simulation mode
./automated_planter --simulation status
```

### Sensor Issues
```bash
# Test sensor reading in simulation mode
./automated_planter --simulation demo 3

# Check hardware initialization
./automated_planter status
```

### Build Issues
```bash
# Check dependencies
make check-deps

# Install missing dependencies
make install-deps-pi

# Clean and rebuild
make clean && make
```

### Database Issues
```bash
# Test database integration
./automated_planter --web-url http://localhost:3000 demo 4
```

## 📱 Touch Screen Integration

Your 7" touch screen will display:
- **Live sensor readings** updated every minute
- **Plant status** from your website database
- **Manual watering controls** for each plant
- **System status** and health indicators
- **Water tank level** with visual indicators

## 🚀 Production Deployment

### For Real Hardware
1. **Connect all sensors** to Raspberry Pi GPIO pins
2. **Install required libraries**:
   ```bash
   make install-deps-pi
   ```
3. **Build the application**:
   ```bash
   make clean && make
   ```
4. **Run without simulation mode**:
   ```bash
   ./automated_planter --web-url http://localhost:3000 monitor
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
1. **Check system status**: `./automated_planter status`
2. **Test in simulation mode**: `./automated_planter --simulation demo 3`
3. **Verify build**: `make check-deps` and `make clean && make`
4. **Test individual components** with demo scripts: `./automated_planter demo [1-5]`
5. **Check GPIO connections** for hardware issues

---

**Your integrated system is now ready!** 🌱

The C-based Raspberry Pi application will send live sensor data to your AutomatedPlanterSite, and your website will display real-time plant monitoring with automatic watering capabilities. The system provides robust performance with efficient resource usage and reliable hardware control.
