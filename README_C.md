# Automated Planter System - C Implementation

A high-performance Raspberry Pi-based automated planter system implemented in C using libgpiod for GPIO control. This senior project implements 5 milestone demonstrations with comprehensive plant care automation.

## 🌱 Project Overview

The Automated Planter system uses a Raspberry Pi 5 as the central controller to monitor plant health through various sensors and automatically water plants based on their specific requirements. The system includes a web-based interface for remote monitoring and control, plus a 7" touch screen for local interaction.

**Key Features:**
- **High Performance**: C implementation for optimal resource usage
- **Modern GPIO Control**: Uses libgpiod for reliable GPIO operations
- **Real-time Monitoring**: Continuous sensor data collection and analysis
- **Automatic Watering**: Intelligent plant care based on sensor readings
- **Web Integration**: Connects to existing AutomatedPlanterSite web interface
- **Touch Screen Support**: 7" IPS LCD display for local interaction

## 🎯 Project Milestones

This project implements 5 milestone demonstrations as defined in the senior project contract:

1. **Demo 1: Plant UI & Database Implementation**
   - Web interface with plant database integration
   - Add/modify plant care requirements
   - 10 pre-loaded plants with detailed care parameters

2. **Demo 2: Water Pump Implementation**
   - Peristaltic pump control via Raspberry Pi GPIO
   - Manual and automatic watering functionality
   - Safety features and pump monitoring

3. **Demo 3: Sensor Implementation**
   - DHT22 temperature/humidity sensor
   - Capacitive soil moisture sensor
   - Digital light sensor
   - Contact water level sensors (3 positions)

4. **Demo 4: Sensors, Database, and UI Synchronized**
   - Complete data pipeline from sensors to web interface
   - Real-time sensor data logging
   - Automatic actions based on sensor readings

5. **Demo 5: System Integration + Touch Screen Display**
   - Complete integrated system operation
   - 7" IPS touch screen interface
   - Full automation with manual override capabilities

## 🛠️ Hardware Components

### Core System
- **Raspberry Pi 5 (8GB RAM)** - Main controller
- **Official Raspberry Pi 27W Power Supply** - System power
- **7" IPS LCD Touch Screen** - Local display interface

### Sensors
- **DHT22** - Temperature and humidity monitoring
- **Capacitive Soil Moisture Sensor** - Soil moisture detection
- **Digital Light Sensor** - Ambient light measurement
- **Contact Water Level Sensors (3x)** - Water tank level monitoring

### Actuators
- **Peristaltic Pumps (2x)** - Automated watering system
- **MOSFET Control Circuit** - Safe pump operation
- **Status LEDs** - System status indication

### Enclosure & Materials
- **3D Printed Planter** - Custom designed enclosure
- **eSUN PLA+ Filament** - Durable 3D printing material
- **Smooth-On XTC-3D** - Waterproof coating
- **Pipe Sealant** - Component protection

## 📋 Software Architecture

### Core Components
- **`hardware_drivers.c`** - GPIO control and sensor interfaces using libgpiod
- **`raspberry_pi_core.c`** - Core system logic and plant management
- **`main.c`** - Main application entry point
- **`demo_milestones.c`** - 5 milestone demonstration scripts

### Features
- **Plant Database**: 10 pre-loaded plants with detailed care requirements
- **Real-time Monitoring**: Live sensor data with automatic validation
- **Automatic Watering**: Based on soil moisture and plant requirements
- **Web Interface**: Connects to existing AutomatedPlanterSite
- **Touch Screen**: Local 7" display for direct interaction
- **Data Logging**: Complete sensor history with efficient storage
- **Safety Features**: Pump timeouts, water level monitoring, error handling

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 5 (8GB recommended)
- GCC compiler
- Required system libraries (see Installation section)

### Installation

1. **Install dependencies:**
   ```bash
   # On Raspberry Pi OS
   make install-deps-pi
   
   # On Ubuntu/Debian
   make install-deps
   ```

2. **Check dependencies:**
   ```bash
   make check-deps
   ```

3. **Build the system:**
   ```bash
   make all
   ```

### Running the System

#### Simulation Mode (Testing)
```bash
# Run with simulated hardware
./automated_planter --simulation

# Run specific demo
./demo_milestones 1

# Run all demos
./demo_milestones all
```

#### Real Hardware Mode
```bash
# Run with real hardware
./automated_planter

# Start monitoring only
./automated_planter monitor

# Show system status
./automated_planter status
```

### Demo Scripts

Run individual milestone demos:
```bash
# Demo 1: Plant UI & Database
./demo_milestones 1

# Demo 2: Water Pump Implementation
./demo_milestones 2

# Demo 3: Sensor Implementation
./demo_milestones 3

# Demo 4: Sensors + Database + UI Sync
./demo_milestones 4

# Demo 5: System Integration + Touch Screen
./demo_milestones 5

# Run all demos
./demo_milestones all
```

## 🌐 Web Interface Integration

The system integrates with the existing AutomatedPlanterSite web interface:

- **Real-time Data**: Sensor readings sent to web database
- **Plant Management**: Plant configuration synchronized
- **Remote Monitoring**: Access from any device on the network
- **Touch Screen**: Local 7" display provides same interface

### Touch Screen Interface
The 7" touch screen provides the same interface locally on the device, allowing for:
- Direct plant monitoring
- Manual watering controls
- System status display
- Configuration access

## 📊 Plant Database

The system includes 10 pre-loaded plants with detailed care requirements:

1. **Snake Plant** - Low maintenance, drought tolerant
2. **Peace Lily** - Moderate care, humidity loving
3. **Spider Plant** - Easy care, good for beginners
4. **Pothos** - Low light tolerant, easy propagation
5. **Monstera** - Popular houseplant, moderate care
6. **ZZ Plant** - Extremely low maintenance
7. **Fiddle Leaf Fig** - Higher maintenance, needs good light
8. **Aloe Vera** - Succulent, minimal watering
9. **Chinese Evergreen** - Low light tolerant
10. **Philodendron** - Easy care, fast growing

Each plant includes:
- Water amount and frequency
- Light requirements (min/max lux)
- Temperature range (°C)
- Humidity requirements (%)
- Soil type preferences
- Soil moisture thresholds (%)

## 🔧 Configuration

### Plant Configuration
Plants are configured through the web interface or configuration files:
- Position assignment (0-9)
- Custom care parameters
- Watering schedules
- Sensor thresholds

### Hardware Configuration
GPIO pin assignments and hardware settings:
- Sensor pin mappings
- Pump control pins
- I2C/SPI configurations
- Safety timeouts

### System Configuration
- Monitoring intervals
- Data logging frequency
- Web interface settings
- Notification preferences

## 📈 Monitoring & Data

### Real-time Monitoring
- Continuous sensor readings (every 5 minutes)
- Automatic plant health validation
- Real-time web interface updates
- Touch screen status display

### Data Logging
- Efficient C data structures
- Complete sensor history
- Plant care events
- System performance metrics

### Automatic Actions
- Soil moisture-based watering
- Temperature/humidity alerts
- Water level monitoring
- System health checks

## 🛡️ Safety Features

- **Pump Timeouts**: Maximum watering duration limits
- **Water Level Monitoring**: Prevents dry pump operation
- **GPIO Protection**: Safe voltage levels and current limits
- **Error Handling**: Comprehensive error detection and recovery
- **Manual Override**: User can always take manual control

## 🎓 Educational Value

This project demonstrates:
- **Embedded Systems**: Raspberry Pi GPIO programming with libgpiod
- **Sensor Integration**: Multiple sensor types and protocols
- **Database Design**: Efficient data structures and management
- **Web Development**: Integration with existing web interfaces
- **System Integration**: Hardware/software coordination
- **Project Management**: Milestone-based development approach
- **C Programming**: High-performance embedded systems programming

## 📚 Technical Documentation

### GPIO Pin Assignments
- **DHT22**: Pin 4 (temperature/humidity)
- **Soil Moisture**: Pin 18 (analog via ADC)
- **Light Sensor**: Pins 2, 3 (I2C)
- **Water Level**: Pins 5, 6, 7 (digital)
- **Pumps**: Pins 23, 24 (peristaltic pumps)
- **Pump Enable**: Pin 25 (MOSFET control)

### Communication Protocols
- **I2C**: Light sensor communication
- **SPI**: ADC for soil moisture sensor
- **GPIO**: Digital sensors and pump control
- **HTTP**: Web interface communication

### Data Structures
```c
typedef struct {
    time_t timestamp;
    float temperature_celsius;
    float humidity_percent;
    float soil_moisture_percent;
    float light_lux;
    bool water_level_top;
    bool water_level_middle;
    bool water_level_bottom;
    float water_tank_percentage;
} sensor_data_t;

typedef struct {
    char name[64];
    int position;
    float water_amount;
    int watering_frequency;
    time_t last_watered;
    bool active;
} plant_t;
```

## 🤝 Team Members

- **Ivan Martinez** - Hardware design and system integration
- **James Sanchez** - Component selection and hardware implementation  
- **Andy Madjedi** - Software development and web interface

## 📄 Project Documents

- **Assignment 2 Preliminary 5 Milestone Contract** - Project requirements and milestones
- **Final Team Report** - Complete project documentation
- **Part List** - Detailed hardware components and costs

## 🚀 Future Enhancements

- **Mobile App**: Native mobile application
- **Cloud Integration**: Remote monitoring and control
- **Machine Learning**: Plant health prediction algorithms
- **Multiple Plant Support**: Expand to multiple plant positions
- **Weather Integration**: Outdoor weather data integration
- **Energy Optimization**: Solar power and battery backup

## 🔧 Development

### Building from Source
```bash
# Debug build
make debug

# Release build
make release

# Cross-compile for Raspberry Pi
make cross-compile
```

### Code Quality
```bash
# Format code
make format

# Static analysis
make analyze

# Test compilation
make test-compile
```

### Dependencies
- **libgpiod**: Modern GPIO control library
- **json-c**: JSON data handling
- **libcurl**: HTTP communication
- **pthread**: Multi-threading support
- **math**: Mathematical functions

## 📞 Support

For questions or support regarding this project, please refer to the project documentation or contact the development team.

---

**Automated Planter System** - Making gardening smarter, easier, and more accessible for everyone. 🌱
