# Raspberry Pi Automated Planter - Hardware Integration

This repository contains the Raspberry Pi hardware integration for the Automated Planter project. It focuses on sensor control, pump management, and hardware-specific functionality, while maintaining the ability to integrate with your existing `AutomatedPlanterSite` web interface.

## 🎯 Project Focus

This Raspberry Pi system handles:
- **Hardware Control**: GPIO management for sensors and actuators
- **Sensor Integration**: DHT22, soil moisture, light, and water level sensors
- **Pump Control**: Peristaltic pump management with safety features
- **5 Milestone Demos**: Hardware-focused demonstrations
- **API Integration**: Communication with existing web interface

## 🛠️ Hardware Components

### Your Raspberry Pi Setup
- **Raspberry Pi 5 (8GB)** - Main controller
- **DHT22** - Temperature/humidity sensor (Pin 4)
- **Capacitive Soil Moisture Sensor** - Soil monitoring (Pin 18, via ADC)
- **Digital Light Sensor** - Ambient light (I2C, Pins 2, 3)
- **Contact Water Level Sensors (3x)** - Tank monitoring (Pins 5, 6, 7)
- **Peristaltic Pumps (2x)** - Watering system (Pins 23, 24)
- **MOSFET Control** - Safe pump operation (Pin 25)
- **7" IPS Touch Screen** - Local interface (HDMI + USB)

## 📋 Core Files

### Hardware Focus
- **`hardware_drivers.py`** - GPIO control for all sensors and actuators
- **`raspberry_pi_core.py`** - Main system logic and plant management
- **`raspberry_pi_api.py`** - Simple API server for external communication
- **`integrate_with_website.py`** - Integration with your existing web interface

### Demo System
- **`demo_milestones.py`** - All 5 milestone demonstrations
- **`main.py`** - Integrated system (includes web interface from AutomatedPlanterSite)

## 🚀 Quick Start

### 1. Installation
```bash
# Install dependencies
pip3 install -r requirements.txt

# For real hardware (uncomment when ready):
# pip3 install RPi.GPIO Adafruit_DHT smbus spidev
```

### 2. Hardware-Focused Usage

#### Run Individual Demos
```bash
# Demo 1: Hardware Setup
python3 raspberry_pi_core.py demo 1

# Demo 2: Pump Control
python3 raspberry_pi_core.py demo 2

# Demo 3: Sensor Integration
python3 raspberry_pi_core.py demo 3

# Demo 4: Data Integration
python3 raspberry_pi_core.py demo 4

# Demo 5: System Integration
python3 raspberry_pi_core.py demo 5

# Run all demos
python3 raspberry_pi_core.py demo 0
```

#### Start Monitoring
```bash
# Simulation mode
python3 raspberry_pi_core.py monitor

# Real hardware mode
python3 raspberry_pi_core.py monitor  # (remove simulation flag)
```

#### Check System Status
```bash
python3 raspberry_pi_core.py status
```

### 3. API Server (Optional)
```bash
# Start API server for external communication
python3 raspberry_pi_api.py --simulation

# With real hardware
python3 raspberry_pi_api.py
```

### 4. Integration with Existing Website
```bash
# Connect to your AutomatedPlanterSite
python3 integrate_with_website.py http://localhost:3000 --simulation
```

## 🎯 Your 5 Milestones

### Demo 1: Hardware Setup and Basic Functionality
- **Objective**: Verify hardware initialization and basic sensor reading
- **What it shows**: System status, GPIO initialization, sensor readings
- **Success criteria**: All hardware components detected and operational

### Demo 2: Water Pump Implementation
- **Objective**: Test peristaltic pump control via GPIO
- **What it shows**: Manual and automatic pump operation
- **Success criteria**: Pumps activate correctly with proper timing

### Demo 3: Sensor Implementation
- **Objective**: Verify all environmental sensors working
- **What it shows**: Temperature, humidity, soil moisture, light, water level
- **Success criteria**: All sensors providing accurate readings

### Demo 4: Data Integration and Monitoring
- **Objective**: Continuous monitoring and data pipeline
- **What it shows**: Real-time sensor data, plant health validation
- **Success criteria**: Stable monitoring loop with data logging

### Demo 5: Complete System Integration
- **Objective**: Full system operation with touch screen
- **What it shows**: Complete automation with manual override
- **Success criteria**: Self-sufficient plant care system

## 🌐 Integration Options

### Option 1: Standalone Raspberry Pi System
Use only the Raspberry Pi core system without external web interface:
```bash
python3 raspberry_pi_core.py monitor
```

### Option 2: API Integration
Run API server to communicate with external systems:
```bash
python3 raspberry_pi_api.py
# Access API at http://localhost:5000
```

### Option 3: Website Integration
Connect to your existing `AutomatedPlanterSite`:
```bash
python3 integrate_with_website.py http://localhost:3000
```

### Option 4: Full Integration (Original)
Use the complete system with integrated web interface:
```bash
python3 main.py  # Includes web interface from AutomatedPlanterSite
```

## 🔧 Hardware Configuration

### GPIO Pin Assignments
```python
GPIO_CONFIG = {
    "dht22_pin": 4,           # Temperature/humidity
    "soil_moisture_pin": 18,  # Soil moisture (analog)
    "light_sensor_sda": 2,    # Light sensor I2C
    "light_sensor_scl": 3,    # Light sensor I2C
    "water_level_pins": [5, 6, 7],  # Water level sensors
    "pump1_pin": 23,          # Pump 1
    "pump2_pin": 24,          # Pump 2
    "pump_enable_pin": 25,    # MOSFET enable
    "status_led": 12,         # Status LED
    "warning_led": 13         # Warning LED
}
```

### Plant Configuration
```python
plant_config = {
    "active_plants": [
        {"name": "Snake Plant", "position": 0, "water_amount": 250, "watering_frequency": 14},
        {"name": "Peace Lily", "position": 1, "water_amount": 300, "watering_frequency": 7},
        {"name": "Spider Plant", "position": 2, "water_amount": 200, "watering_frequency": 7}
    ]
}
```

## 📊 System Features

### Hardware Control
- **GPIO Management**: Safe voltage levels and current limits
- **Sensor Reading**: Real-time data from all sensors
- **Pump Control**: Precise timing with safety timeouts
- **Error Handling**: Comprehensive error detection and recovery

### Plant Management
- **Automatic Watering**: Based on soil moisture and plant requirements
- **Health Monitoring**: Continuous plant health validation
- **Custom Schedules**: Per-plant watering schedules
- **Manual Override**: User can always take control

### Data Management
- **Real-time Monitoring**: Continuous sensor data collection
- **Data Logging**: Complete sensor history storage
- **API Endpoints**: External system integration
- **Status Reporting**: Comprehensive system status

## 🛡️ Safety Features

- **Pump Timeouts**: Maximum watering duration limits
- **Water Level Monitoring**: Prevents dry pump operation
- **GPIO Protection**: Safe voltage levels and current limits
- **Error Recovery**: Automatic error detection and recovery
- **Manual Override**: Emergency stop capabilities

## 🎓 Educational Value

This project demonstrates:
- **Embedded Systems Programming**: Raspberry Pi GPIO control
- **Sensor Integration**: Multiple sensor types and protocols
- **Hardware/Software Integration**: Seamless coordination
- **API Development**: RESTful endpoints for external communication
- **System Design**: Modular architecture with clear separation of concerns

## 📞 Usage Examples

### Testing Individual Components
```bash
# Test hardware drivers only
python3 -c "from hardware_drivers import HardwareInterface; h = HardwareInterface(True); print(h.read_all_sensors())"

# Test plant configuration
python3 -c "from raspberry_pi_core import RaspberryPiCore; r = RaspberryPiCore(True); print(r.get_system_status())"
```

### Running Demos for Class
```bash
# Run all demos in sequence
python3 raspberry_pi_core.py demo 0

# Run specific demo for presentation
python3 raspberry_pi_core.py demo 3  # Sensor implementation
```

### Production Deployment
```bash
# Start monitoring system
python3 raspberry_pi_core.py monitor

# Start with website integration
python3 integrate_with_website.py http://your-website-url.com
```

---

**Raspberry Pi Automated Planter** - Focused hardware integration for your senior project! 🌱
