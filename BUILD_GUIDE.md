# Automated Planter C Implementation - Build Guide

This guide covers building and running the C implementation of the Automated Planter system.

## Prerequisites

### System Requirements
- Raspberry Pi 5 (8GB RAM recommended)
- Raspberry Pi OS (latest version)
- GCC compiler
- Make build system

### Required Libraries
- **libgpiod**: Modern GPIO control library
- **json-c**: JSON data handling
- **libcurl**: HTTP communication
- **pthread**: Multi-threading support (usually included)

## Installation

### 1. Install Dependencies

#### On Raspberry Pi OS:
```bash
sudo apt-get update
sudo apt-get install -y \
    libgpiod-dev \
    libjson-c-dev \
    libcurl4-openssl-dev \
    pkg-config \
    gcc \
    make
```

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    libgpiod-dev \
    libjson-c-dev \
    libcurl4-openssl-dev \
    pkg-config \
    gcc \
    make
```

### 2. Verify Dependencies
```bash
make check-deps
```

Expected output:
```
✅ libgpiod found
✅ json-c found
✅ libcurl found
```

## Building

### 1. Build All Components
```bash
make all
```

This creates two executables:
- `automated_planter` - Main application
- `demo_milestones` - Demo system

### 2. Build Options

#### Debug Build
```bash
make debug
```

#### Release Build
```bash
make release
```

#### Cross-compile for Raspberry Pi
```bash
make cross-compile
```

### 3. Clean Build Artifacts
```bash
make clean
```

## Running the System

### 1. Simulation Mode (Recommended for Testing)

#### Main Application
```bash
./automated_planter --simulation
```

#### Demo System
```bash
# Run individual demos
./demo_milestones 1
./demo_milestones 2
./demo_milestones 3
./demo_milestones 4
./demo_milestones 5

# Run all demos
./demo_milestones all
```

### 2. Real Hardware Mode

#### Main Application
```bash
# Start full system
./automated_planter

# Start monitoring only
./automated_planter monitor

# Show system status
./automated_planter status
```

#### Demo System
```bash
# Run with real hardware
./demo_milestones 1 --real-hardware
```

## GPIO Configuration

### Pin Assignments
- **DHT22**: GPIO 4 (temperature/humidity)
- **Soil Moisture**: GPIO 18 (analog via ADC)
- **Light Sensor**: GPIO 2, 3 (I2C)
- **Water Level**: GPIO 5, 6, 7 (digital)
- **Pumps**: GPIO 23, 24 (peristaltic pumps)
- **Pump Enable**: GPIO 25 (MOSFET control)
- **Status LEDs**: GPIO 12, 13

### GPIO Permissions
Ensure your user has access to GPIO:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Log out and back in for changes to take effect
```

## Hardware Setup

### 1. Sensor Connections
- Connect DHT22 to GPIO 4
- Connect soil moisture sensor to GPIO 18 (via ADC)
- Connect light sensor to I2C pins (GPIO 2, 3)
- Connect water level sensors to GPIO 5, 6, 7

### 2. Actuator Connections
- Connect pump 1 to GPIO 23
- Connect pump 2 to GPIO 24
- Connect pump enable to GPIO 25
- Connect status LEDs to GPIO 12, 13

### 3. Power Supply
- Use official Raspberry Pi 27W power supply
- Ensure adequate power for pumps and sensors

## Troubleshooting

### Common Issues

#### 1. GPIO Permission Denied
```bash
# Check if user is in gpio group
groups $USER

# Add user to gpio group if not present
sudo usermod -a -G gpio $USER
```

#### 2. Library Not Found
```bash
# Update library cache
sudo ldconfig

# Check library paths
ldconfig -p | grep gpiod
```

#### 3. Compilation Errors
```bash
# Check GCC version
gcc --version

# Update packages
sudo apt-get update && sudo apt-get upgrade
```

#### 4. Runtime Errors
```bash
# Check system logs
journalctl -f

# Run with debug output
./automated_planter --simulation --debug
```

### Debug Mode
```bash
# Build with debug symbols
make debug

# Run with GDB
gdb ./automated_planter
```

## Performance Optimization

### 1. Compiler Optimizations
```bash
# Release build with optimizations
make release
```

### 2. System Tuning
```bash
# Increase GPIO performance
echo 1 | sudo tee /sys/class/gpio/export

# Optimize I2C speed
sudo modprobe i2c-dev
```

### 3. Memory Usage
```bash
# Monitor memory usage
htop

# Check for memory leaks
valgrind ./automated_planter --simulation
```

## Integration with Web Interface

### 1. Connect to AutomatedPlanterSite
```bash
# Run with web interface URL
./automated_planter --web-url http://localhost:3000
```

### 2. Data Synchronization
The system automatically sends sensor data to the web interface:
- Temperature and humidity readings
- Soil moisture levels
- Light sensor data
- Water tank levels
- Pump status

### 3. Plant Management
Plant configuration is synchronized with the web database:
- Plant care requirements
- Watering schedules
- Sensor thresholds
- Position assignments

## Development

### 1. Code Quality
```bash
# Format code
make format

# Static analysis
make analyze

# Test compilation
make test-compile
```

### 2. Adding New Features
1. Modify source files
2. Update header files
3. Rebuild with `make all`
4. Test in simulation mode
5. Test with real hardware

### 3. Debugging
```bash
# Enable debug output
export DEBUG=1

# Run with verbose logging
./automated_planter --simulation --verbose
```

## Maintenance

### 1. Regular Updates
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade

# Rebuild application
make clean && make all
```

### 2. Log Monitoring
```bash
# Monitor system logs
journalctl -f -u automated-planter

# Check application logs
tail -f /var/log/automated-planter.log
```

### 3. Hardware Maintenance
- Clean sensors regularly
- Check pump connections
- Monitor water levels
- Inspect GPIO connections

## Support

For technical support:
1. Check this build guide
2. Review system logs
3. Test in simulation mode
4. Contact development team

---

**Build Guide** - Automated Planter C Implementation
