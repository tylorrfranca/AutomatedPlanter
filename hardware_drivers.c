#include "hardware_drivers.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <math.h>
#include <sys/time.h>
#include <stdarg.h>

// I2C and SPI includes for sensors
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <sys/ioctl.h>

// DHT22 sensor implementation
static bool dht22_read_raw(hardware_interface_t *hw, uint8_t *data) {
    if (hw->simulation_mode) {
        // Simulate realistic values
        data[0] = 0x40; // humidity high
        data[1] = 0x20; // humidity low
        data[2] = 0x20; // temperature high
        data[3] = 0x10; // temperature low
        data[4] = 0x90; // checksum
        return true;
    }
    
    // DHT22 protocol implementation
    // This is a simplified version - full implementation would require precise timing
    gpiod_line_set_value(hw->dht22_line, 0);
    usleep(18000); // 18ms low signal
    gpiod_line_set_value(hw->dht22_line, 1);
    usleep(30); // 30us high signal
    
    // Read data bits (simplified)
    // In a real implementation, you'd need precise timing for each bit
    for (int i = 0; i < 5; i++) {
        data[i] = 0;
        for (int j = 0; j < 8; j++) {
            usleep(50); // Wait for bit
            int bit = gpiod_line_get_value(hw->dht22_line);
            data[i] |= (bit << (7 - j));
            usleep(70); // Wait for next bit
        }
    }
    
    // Verify checksum
    uint8_t checksum = data[0] + data[1] + data[2] + data[3];
    return (checksum == data[4]);
}

// ADC reading for soil moisture (MCP3008)
static uint16_t read_adc_channel(int spi_fd, int channel) {
    if (spi_fd < 0) return 0;
    
    uint8_t tx[3] = {0x01, (0x08 | channel) << 4, 0x00};
    uint8_t rx[3];
    
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = 3,
        .speed_hz = 1000000,
        .delay_usecs = 0,
        .bits_per_word = 8,
    };
    
    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr) < 0) {
        return 0;
    }
    
    return ((rx[1] & 0x03) << 8) | rx[2];
}

// I2C light sensor reading (TSL2561)
static float read_tsl2561_lux(int i2c_fd) {
    if (i2c_fd < 0) return 0.0;
    
    // Enable sensor
    uint8_t enable_cmd = 0x03;
    if (write(i2c_fd, &enable_cmd, 1) != 1) return 0.0;
    
    usleep(100000); // Wait 100ms for integration
    
    // Read channel 0 (visible + IR)
    uint8_t cmd0 = 0x0C;
    if (write(i2c_fd, &cmd0, 1) != 1) return 0.0;
    
    uint8_t data[2];
    if (read(i2c_fd, data, 2) != 2) return 0.0;
    
    uint16_t ch0 = (data[1] << 8) | data[0];
    
    // Read channel 1 (IR only)
    uint8_t cmd1 = 0x0E;
    if (write(i2c_fd, &cmd1, 1) != 1) return 0.0;
    
    if (read(i2c_fd, data, 2) != 2) return 0.0;
    
    uint16_t ch1 = (data[1] << 8) | data[0];
    
    // Calculate lux (simplified formula)
    if (ch0 == 0) return 0.0;
    
    float ratio = (float)ch1 / ch0;
    float lux = 0.0;
    
    if (ratio <= 0.50) {
        lux = 0.0304 * ch0 - 0.062 * ch0 * pow(ratio, 1.4);
    } else if (ratio <= 0.61) {
        lux = 0.0224 * ch0 - 0.031 * ch1;
    } else if (ratio <= 0.80) {
        lux = 0.0128 * ch0 - 0.0153 * ch1;
    } else if (ratio <= 1.30) {
        lux = 0.00146 * ch0 - 0.00112 * ch1;
    } else {
        lux = 0.0;
    }
    
    return lux;
}

hardware_interface_t* hardware_init(bool simulation_mode) {
    hardware_interface_t *hw = malloc(sizeof(hardware_interface_t));
    if (!hw) {
        hardware_log("ERROR", "Failed to allocate memory for hardware interface");
        return NULL;
    }
    
    memset(hw, 0, sizeof(hardware_interface_t));
    hw->simulation_mode = simulation_mode;
    
    if (!simulation_mode) {
        // Open GPIO chip
        hw->chip = gpiod_chip_open_by_name("gpiochip0");
        if (!hw->chip) {
            hardware_log("ERROR", "Failed to open GPIO chip: %s", strerror(errno));
            free(hw);
            return NULL;
        }
        
        // Request GPIO lines
        hw->dht22_line = gpiod_chip_get_line(hw->chip, DHT22_PIN);
        hw->soil_moisture_line = gpiod_chip_get_line(hw->chip, SOIL_MOISTURE_PIN);
        hw->water_level_lines[0] = gpiod_chip_get_line(hw->chip, 5);
        hw->water_level_lines[1] = gpiod_chip_get_line(hw->chip, 6);
        hw->water_level_lines[2] = gpiod_chip_get_line(hw->chip, 7);
        hw->pump1_line = gpiod_chip_get_line(hw->chip, PUMP1_PIN);
        hw->pump2_line = gpiod_chip_get_line(hw->chip, PUMP2_PIN);
        hw->pump_enable_line = gpiod_chip_get_line(hw->chip, PUMP_ENABLE_PIN);
        hw->status_led_line = gpiod_chip_get_line(hw->chip, STATUS_LED_PIN);
        hw->warning_led_line = gpiod_chip_get_line(hw->chip, WARNING_LED_PIN);
        
        // Configure input lines
        if (gpiod_line_request_input(hw->dht22_line, "automated_planter") < 0) {
            hardware_log("ERROR", "Failed to request DHT22 line");
            goto cleanup;
        }
        
        if (gpiod_line_request_input(hw->soil_moisture_line, "automated_planter") < 0) {
            hardware_log("ERROR", "Failed to request soil moisture line");
            goto cleanup;
        }
        
        for (int i = 0; i < 3; i++) {
            if (gpiod_line_request_input(hw->water_level_lines[i], "automated_planter") < 0) {
                hardware_log("ERROR", "Failed to request water level line %d", i);
                goto cleanup;
            }
        }
        
        // Configure output lines
        if (gpiod_line_request_output(hw->pump1_line, "automated_planter", 0) < 0) {
            hardware_log("ERROR", "Failed to request pump1 line");
            goto cleanup;
        }
        
        if (gpiod_line_request_output(hw->pump2_line, "automated_planter", 0) < 0) {
            hardware_log("ERROR", "Failed to request pump2 line");
            goto cleanup;
        }
        
        if (gpiod_line_request_output(hw->pump_enable_line, "automated_planter", 0) < 0) {
            hardware_log("ERROR", "Failed to request pump enable line");
            goto cleanup;
        }
        
        if (gpiod_line_request_output(hw->status_led_line, "automated_planter", 0) < 0) {
            hardware_log("ERROR", "Failed to request status LED line");
            goto cleanup;
        }
        
        if (gpiod_line_request_output(hw->warning_led_line, "automated_planter", 0) < 0) {
            hardware_log("ERROR", "Failed to request warning LED line");
            goto cleanup;
        }
        
        hw->gpio_initialized = true;
        hardware_log("INFO", "Hardware interface initialized successfully");
    } else {
        hardware_log("INFO", "Hardware interface initialized in simulation mode");
    }
    
    return hw;
    
cleanup:
    hardware_cleanup(hw);
    return NULL;
}

void hardware_cleanup(hardware_interface_t *hw) {
    if (!hw) return;
    
    if (hw->gpio_initialized) {
        // Turn off all outputs
        if (hw->pump1_line) gpiod_line_set_value(hw->pump1_line, 0);
        if (hw->pump2_line) gpiod_line_set_value(hw->pump2_line, 0);
        if (hw->pump_enable_line) gpiod_line_set_value(hw->pump_enable_line, 0);
        if (hw->status_led_line) gpiod_line_set_value(hw->status_led_line, 0);
        if (hw->warning_led_line) gpiod_line_set_value(hw->warning_led_line, 0);
        
        // Release lines
        if (hw->dht22_line) gpiod_line_release(hw->dht22_line);
        if (hw->soil_moisture_line) gpiod_line_release(hw->soil_moisture_line);
        for (int i = 0; i < 3; i++) {
            if (hw->water_level_lines[i]) gpiod_line_release(hw->water_level_lines[i]);
        }
        if (hw->pump1_line) gpiod_line_release(hw->pump1_line);
        if (hw->pump2_line) gpiod_line_release(hw->pump2_line);
        if (hw->pump_enable_line) gpiod_line_release(hw->pump_enable_line);
        if (hw->status_led_line) gpiod_line_release(hw->status_led_line);
        if (hw->warning_led_line) gpiod_line_release(hw->warning_led_line);
        
        // Close chip
        if (hw->chip) gpiod_chip_close(hw->chip);
        
        hardware_log("INFO", "GPIO cleanup completed");
    }
    
    free(hw);
}

bool read_dht22(hardware_interface_t *hw, float *temperature, float *humidity) {
    if (!hw || !temperature || !humidity) return false;
    
    uint8_t data[5];
    
    if (!dht22_read_raw(hw, data)) {
        hardware_log("WARNING", "DHT22 sensor read failed");
        return false;
    }
    
    // Convert raw data to temperature and humidity
    *humidity = ((data[0] << 8) | data[1]) / 10.0;
    *temperature = (((data[2] & 0x7F) << 8) | data[3]) / 10.0;
    
    // Handle negative temperature
    if (data[2] & 0x80) {
        *temperature = -(*temperature);
    }
    
    return true;
}

float read_soil_moisture(hardware_interface_t *hw) {
    if (!hw) return 0.0;
    
    if (hw->simulation_mode) {
        // Simulate soil moisture values
        return 30.0 + (rand() % 400) / 10.0; // 30.0-70.0%
    }
    
    // Open SPI device for ADC
    int spi_fd = open("/dev/spidev0.0", O_RDWR);
    if (spi_fd < 0) {
        hardware_log("ERROR", "Failed to open SPI device: %s", strerror(errno));
        return 0.0;
    }
    
    uint16_t raw_value = read_adc_channel(spi_fd, 0);
    close(spi_fd);
    
    // Convert to percentage (0-1023 -> 0-100%)
    float moisture_percent = (raw_value / 1023.0) * 100.0;
    
    return moisture_percent;
}

float read_light_sensor(hardware_interface_t *hw) {
    if (!hw) return 0.0;
    
    if (hw->simulation_mode) {
        // Simulate light levels
        return 50.0 + (rand() % 5000) / 10.0; // 50.0-550.0 lux
    }
    
    // Open I2C device
    int i2c_fd = open("/dev/i2c-1", O_RDWR);
    if (i2c_fd < 0) {
        hardware_log("ERROR", "Failed to open I2C device: %s", strerror(errno));
        return 0.0;
    }
    
    // Set I2C slave address
    if (ioctl(i2c_fd, I2C_SLAVE, 0x29) < 0) {
        hardware_log("ERROR", "Failed to set I2C slave address: %s", strerror(errno));
        close(i2c_fd);
        return 0.0;
    }
    
    float lux = read_tsl2561_lux(i2c_fd);
    close(i2c_fd);
    
    return lux;
}

void read_water_level(hardware_interface_t *hw, bool *top, bool *middle, bool *bottom) {
    if (!hw || !top || !middle || !bottom) return;
    
    if (hw->simulation_mode) {
        // Simulate water levels
        *top = (rand() % 2) == 1;
        *middle = (rand() % 2) == 1;
        *bottom = (rand() % 2) == 1;
        return;
    }
    
    if (!hw->gpio_initialized) return;
    
    // Read water level sensors (HIGH when water detected, LOW when dry)
    *top = gpiod_line_get_value(hw->water_level_lines[0]) == 1;
    *middle = gpiod_line_get_value(hw->water_level_lines[1]) == 1;
    *bottom = gpiod_line_get_value(hw->water_level_lines[2]) == 1;
}

bool control_pump(hardware_interface_t *hw, int pump_number, float duration_seconds, float water_amount_ml) {
    if (!hw || pump_number < 1 || pump_number > 2) {
        hardware_log("ERROR", "Invalid pump number: %d", pump_number);
        return false;
    }
    
    struct gpiod_line *pump_line = (pump_number == 1) ? hw->pump1_line : hw->pump2_line;
    
    if (!hw->simulation_mode && hw->gpio_initialized) {
        // Enable pump via MOSFET
        gpiod_line_set_value(hw->pump_enable_line, 1);
        usleep(100000); // 100ms delay for MOSFET activation
        
        // Turn on specific pump
        gpiod_line_set_value(pump_line, 1);
        hardware_log("INFO", "Pump %d started for %.1f seconds", pump_number, duration_seconds);
    }
    
    // Record pump start time
    hw->pump_status.last_watered = time(NULL);
    if (pump_number == 1) {
        hw->pump_status.pump1_active = true;
    } else {
        hw->pump_status.pump2_active = true;
    }
    
    // Run pump for specified duration
    usleep((int)(duration_seconds * 1000000));
    
    if (!hw->simulation_mode && hw->gpio_initialized) {
        // Turn off pump
        gpiod_line_set_value(pump_line, 0);
        gpiod_line_set_value(hw->pump_enable_line, 0);
    }
    
    // Update status
    if (pump_number == 1) {
        hw->pump_status.pump1_active = false;
    } else {
        hw->pump_status.pump2_active = false;
    }
    
    hardware_log("INFO", "Pump %d watering completed", pump_number);
    return true;
}

void set_status_led(hardware_interface_t *hw, const char *status) {
    if (!hw || !status) return;
    
    if (hw->simulation_mode) {
        hardware_log("INFO", "Status LED: %s", status);
        return;
    }
    
    if (!hw->gpio_initialized) return;
    
    if (strcmp(status, "normal") == 0) {
        gpiod_line_set_value(hw->status_led_line, 1);
        gpiod_line_set_value(hw->warning_led_line, 0);
    } else if (strcmp(status, "warning") == 0) {
        gpiod_line_set_value(hw->status_led_line, 0);
        gpiod_line_set_value(hw->warning_led_line, 1);
    } else {
        gpiod_line_set_value(hw->status_led_line, 0);
        gpiod_line_set_value(hw->warning_led_line, 0);
    }
}

sensor_data_t read_all_sensors(hardware_interface_t *hw) {
    sensor_data_t data = {0};
    
    if (!hw) return data;
    
    data.timestamp = time(NULL);
    
    // Read individual sensors
    read_dht22(hw, &data.temperature_celsius, &data.humidity_percent);
    data.soil_moisture_percent = read_soil_moisture(hw);
    data.light_lux = read_light_sensor(hw);
    read_water_level(hw, &data.water_level_top, &data.water_level_middle, &data.water_level_bottom);
    
    // Calculate water tank level percentage
    data.water_tank_percentage = calculate_water_percentage(
        data.water_level_top, 
        data.water_level_middle, 
        data.water_level_bottom
    );
    
    return data;
}

float calculate_water_percentage(bool top, bool middle, bool bottom) {
    if (top) return 100.0;
    if (middle) return 66.7;
    if (bottom) return 33.3;
    return 0.0;
}

void hardware_log(const char *level, const char *format, ...) {
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm_info);
    
    printf("[%s] [%s] ", timestamp, level);
    
    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
    
    printf("\n");
}

time_t get_current_timestamp(void) {
    return time(NULL);
}
