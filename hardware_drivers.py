#!/usr/bin/env python3
"""
Hardware Drivers for Automated Planter
Raspberry Pi GPIO control for sensors and actuators
"""

import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPIO pins configuration (based on your hardware setup)
GPIO_CONFIG = {
    # Sensors
    "dht22_pin": 4,           # DHT22 temperature/humidity sensor
    "soil_moisture_pin": 18,  # Capacitive soil moisture sensor (analog)
    "light_sensor_sda": 2,    # Digital light sensor I2C SDA
    "light_sensor_scl": 3,    # Digital light sensor I2C SCL
    "water_level_pins": [5, 6, 7],  # Contact water level sensors (3 positions)
    
    # Actuators
    "pump1_pin": 23,          # Peristaltic pump 1
    "pump2_pin": 24,          # Peristaltic pump 2
    "pump_enable_pin": 25,    # MOSFET enable for pumps
    
    # Status LEDs
    "status_led": 12,
    "warning_led": 13
}

class HardwareInterface:
    """Main hardware interface class for Raspberry Pi"""
    
    def __init__(self, simulation_mode: bool = False):
        """
        Initialize hardware interface
        Args:
            simulation_mode: If True, use simulated data instead of real hardware
        """
        self.simulation_mode = simulation_mode
        self.gpio_initialized = False
        
        if not simulation_mode:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                self._init_gpio()
                logger.info("Hardware interface initialized successfully")
            except ImportError:
                logger.warning("RPi.GPIO not available, using simulation mode")
                self.simulation_mode = True
        
        # Initialize sensor data
        self.last_sensor_readings = {}
        self.sensor_history = []
        
        # Initialize pumps
        self.pump_status = {
            "pump1": False,
            "pump2": False,
            "last_watered": None
        }
    
    def _init_gpio(self):
        """Initialize GPIO pins"""
        if self.simulation_mode:
            return
            
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        
        # Set up output pins (pumps, LEDs)
        output_pins = [
            GPIO_CONFIG["pump1_pin"],
            GPIO_CONFIG["pump2_pin"], 
            GPIO_CONFIG["pump_enable_pin"],
            GPIO_CONFIG["status_led"],
            GPIO_CONFIG["warning_led"]
        ]
        
        for pin in output_pins:
            self.GPIO.setup(pin, self.GPIO.OUT)
            self.GPIO.output(pin, self.GPIO.LOW)
        
        # Set up input pins (sensors)
        input_pins = [
            GPIO_CONFIG["dht22_pin"],
            GPIO_CONFIG["soil_moisture_pin"]
        ] + GPIO_CONFIG["water_level_pins"]
        
        for pin in input_pins:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        
        self.gpio_initialized = True
        logger.info("GPIO pins initialized")
    
    def read_dht22(self) -> Tuple[float, float]:
        """
        Read temperature and humidity from DHT22 sensor
        Returns:
            Tuple of (temperature_celsius, humidity_percent)
        """
        if self.simulation_mode:
            # Simulate realistic values
            import random
            temp = round(20 + random.uniform(-3, 8), 1)  # 17-28°C
            humidity = round(40 + random.uniform(-10, 20), 1)  # 30-60%
            return temp, humidity
        
        try:
            import Adafruit_DHT
            humidity, temperature = Adafruit_DHT.read_retry(
                Adafruit_DHT.DHT22, 
                GPIO_CONFIG["dht22_pin"]
            )
            
            if humidity is not None and temperature is not None:
                return round(temperature, 1), round(humidity, 1)
            else:
                logger.warning("DHT22 sensor read failed")
                return None, None
                
        except ImportError:
            logger.error("Adafruit_DHT library not installed")
            return None, None
        except Exception as e:
            logger.error(f"DHT22 read error: {e}")
            return None, None
    
    def read_soil_moisture(self) -> float:
        """
        Read soil moisture from capacitive sensor
        Returns:
            Soil moisture percentage (0-100%)
        """
        if self.simulation_mode:
            # Simulate soil moisture values
            import random
            return round(30 + random.uniform(-15, 25), 1)  # 15-55%
        
        try:
            # For analog sensor, we need ADC conversion
            # This is a simplified version - you'll need proper ADC setup
            import spidev
            
            spi = spidev.SpiDev()
            spi.open(0, 0)  # SPI bus 0, device 0
            
            # Read from MCP3008 ADC (common for Raspberry Pi)
            adc_channel = 0  # Channel for soil moisture sensor
            raw_value = self._read_adc(spi, adc_channel)
            
            # Convert to percentage (0-1023 -> 0-100%)
            moisture_percent = (raw_value / 1023.0) * 100
            spi.close()
            
            return round(moisture_percent, 1)
            
        except ImportError:
            logger.error("spidev library not installed for ADC")
            return None
        except Exception as e:
            logger.error(f"Soil moisture read error: {e}")
            return None
    
    def _read_adc(self, spi, channel):
        """Read value from MCP3008 ADC"""
        # MCP3008 protocol
        cmd = 0x06  # Start bit + single-ended
        cmd <<= 5   # Shift to make room for channel
        cmd |= channel
        cmd <<= 2   # Make room for null bit
        
        resp = spi.xfer2([cmd, 0x00, 0x00])
        result = (resp[0] & 0x01) << 9
        result |= (resp[1] & 0xFF) << 1
        result |= (resp[2] & 0x80) >> 7
        
        return result
    
    def read_light_sensor(self) -> float:
        """
        Read ambient light from digital light sensor
        Returns:
            Light level in lux
        """
        if self.simulation_mode:
            # Simulate light levels
            import random
            return round(50 + random.uniform(0, 500), 1)  # 50-550 lux
        
        try:
            import smbus
            
            # I2C address for light sensor (check your sensor's datasheet)
            I2C_ADDRESS = 0x29  # Common for TSL2561
            bus = smbus.SMBus(1)  # I2C bus 1
            
            # Read light sensor (simplified - check your sensor's protocol)
            # This is a generic example for TSL2561
            data = bus.read_i2c_block_data(I2C_ADDRESS, 0x0C, 2)
            lux = (data[1] << 8) | data[0]
            
            bus.close()
            return round(lux, 1)
            
        except ImportError:
            logger.error("smbus library not installed for I2C")
            return None
        except Exception as e:
            logger.error(f"Light sensor read error: {e}")
            return None
    
    def read_water_level(self) -> Dict[str, bool]:
        """
        Read water level sensors (3 positions: top, middle, bottom)
        Returns:
            Dictionary with water level status for each position
        """
        if self.simulation_mode:
            # Simulate water levels
            import random
            return {
                "top": random.choice([True, False]),
                "middle": random.choice([True, False]),
                "bottom": random.choice([True, False])
            }
        
        try:
            water_levels = {}
            positions = ["top", "middle", "bottom"]
            
            for i, position in enumerate(positions):
                pin = GPIO_CONFIG["water_level_pins"][i]
                # Contact sensors: HIGH when water detected, LOW when dry
                water_detected = self.GPIO.input(pin) == self.GPIO.HIGH
                water_levels[position] = water_detected
            
            return water_levels
            
        except Exception as e:
            logger.error(f"Water level read error: {e}")
            return {"top": False, "middle": False, "bottom": False}
    
    def control_pump(self, pump_number: int, duration_seconds: float, water_amount_ml: float = None):
        """
        Control peristaltic pump
        Args:
            pump_number: 1 or 2 (which pump to control)
            duration_seconds: How long to run the pump
            water_amount_ml: Expected water amount (for logging)
        """
        if pump_number not in [1, 2]:
            logger.error(f"Invalid pump number: {pump_number}")
            return False
        
        pump_name = f"pump{pump_number}"
        pump_pin = GPIO_CONFIG[f"pump{pump_number}_pin"]
        
        try:
            if not self.simulation_mode:
                # Enable pump via MOSFET
                self.GPIO.output(GPIO_CONFIG["pump_enable_pin"], self.GPIO.HIGH)
                time.sleep(0.1)  # Brief delay for MOSFET activation
                
                # Turn on specific pump
                self.GPIO.output(pump_pin, self.GPIO.HIGH)
                logger.info(f"Pump {pump_number} started for {duration_seconds} seconds")
            
            # Record pump start time
            start_time = time.time()
            self.pump_status[pump_name] = True
            
            # Run pump for specified duration
            time.sleep(duration_seconds)
            
            if not self.simulation_mode:
                # Turn off pump
                self.GPIO.output(pump_pin, self.GPIO.LOW)
                self.GPIO.output(GPIO_CONFIG["pump_enable_pin"], self.GPIO.LOW)
            
            # Update status
            self.pump_status[pump_name] = False
            self.pump_status["last_watered"] = datetime.now().isoformat()
            
            # Log watering event
            event = {
                "timestamp": datetime.now().isoformat(),
                "pump": pump_number,
                "duration": duration_seconds,
                "water_amount_ml": water_amount_ml,
                "status": "completed"
            }
            
            logger.info(f"Pump {pump_number} watering completed: {event}")
            return True
            
        except Exception as e:
            logger.error(f"Pump {pump_number} control error: {e}")
            if not self.simulation_mode:
                # Ensure pumps are turned off on error
                self.GPIO.output(pump_pin, self.GPIO.LOW)
                self.GPIO.output(GPIO_CONFIG["pump_enable_pin"], self.GPIO.LOW)
            return False
    
    def read_all_sensors(self) -> Dict:
        """
        Read all sensors and return comprehensive data
        Returns:
            Dictionary with all sensor readings
        """
        timestamp = datetime.now().isoformat()
        
        # Read individual sensors
        temperature, humidity = self.read_dht22()
        soil_moisture = self.read_soil_moisture()
        light_level = self.read_light_sensor()
        water_levels = self.read_water_level()
        
        # Calculate water tank level percentage
        water_percentage = self._calculate_water_percentage(water_levels)
        
        sensor_data = {
            "timestamp": timestamp,
            "temperature_celsius": temperature,
            "humidity_percent": humidity,
            "soil_moisture_percent": soil_moisture,
            "light_lux": light_level,
            "water_levels": water_levels,
            "water_tank_percentage": water_percentage,
            "pump_status": self.pump_status.copy()
        }
        
        # Store in history
        self.sensor_history.append(sensor_data)
        self.last_sensor_readings = sensor_data
        
        # Keep only last 100 readings
        if len(self.sensor_history) > 100:
            self.sensor_history = self.sensor_history[-100:]
        
        return sensor_data
    
    def _calculate_water_percentage(self, water_levels: Dict[str, bool]) -> float:
        """Calculate water tank percentage based on sensor readings"""
        if water_levels["top"]:
            return 100.0
        elif water_levels["middle"]:
            return 66.7
        elif water_levels["bottom"]:
            return 33.3
        else:
            return 0.0
    
    def set_status_led(self, status: str):
        """Control status LED"""
        if self.simulation_mode:
            logger.info(f"Status LED: {status}")
            return
        
        try:
            if status == "normal":
                self.GPIO.output(GPIO_CONFIG["status_led"], self.GPIO.HIGH)
                self.GPIO.output(GPIO_CONFIG["warning_led"], self.GPIO.LOW)
            elif status == "warning":
                self.GPIO.output(GPIO_CONFIG["status_led"], self.GPIO.LOW)
                self.GPIO.output(GPIO_CONFIG["warning_led"], self.GPIO.HIGH)
            else:
                self.GPIO.output(GPIO_CONFIG["status_led"], self.GPIO.LOW)
                self.GPIO.output(GPIO_CONFIG["warning_led"], self.GPIO.LOW)
                
        except Exception as e:
            logger.error(f"LED control error: {e}")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        sensor_data = self.read_all_sensors()
        
        return {
            "hardware_status": "operational" if self.gpio_initialized else "simulation",
            "simulation_mode": self.simulation_mode,
            "last_reading": sensor_data,
            "pump_status": self.pump_status,
            "sensor_history_count": len(self.sensor_history),
            "gpio_initialized": self.gpio_initialized
        }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not self.simulation_mode and self.gpio_initialized:
            try:
                # Turn off all outputs
                output_pins = [
                    GPIO_CONFIG["pump1_pin"],
                    GPIO_CONFIG["pump2_pin"],
                    GPIO_CONFIG["pump_enable_pin"],
                    GPIO_CONFIG["status_led"],
                    GPIO_CONFIG["warning_led"]
                ]
                
                for pin in output_pins:
                    self.GPIO.output(pin, self.GPIO.LOW)
                
                self.GPIO.cleanup()
                logger.info("GPIO cleanup completed")
                
            except Exception as e:
                logger.error(f"GPIO cleanup error: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test hardware interface
    hardware = HardwareInterface(simulation_mode=True)
    
    print("=== Hardware Interface Test ===")
    print(f"Simulation mode: {hardware.simulation_mode}")
    
    # Test sensor readings
    print("\n--- Sensor Readings ---")
    sensor_data = hardware.read_all_sensors()
    for key, value in sensor_data.items():
        print(f"{key}: {value}")
    
    # Test pump control
    print("\n--- Pump Test ---")
    success = hardware.control_pump(1, 2.0, 100)
    print(f"Pump test result: {success}")
    
    # Test system status
    print("\n--- System Status ---")
    status = hardware.get_system_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Cleanup
    hardware.cleanup()
    print("\nTest completed!")
