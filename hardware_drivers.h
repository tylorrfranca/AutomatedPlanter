#ifndef HARDWARE_DRIVERS_H
#define HARDWARE_DRIVERS_H

#include <gpiod.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

// GPIO pin configuration
#define DHT22_PIN 4
#define SOIL_MOISTURE_PIN 18
#define LIGHT_SENSOR_SDA 2
#define LIGHT_SENSOR_SCL 3
#define WATER_LEVEL_PINS {5, 6, 7}
#define PUMP1_PIN 23
#define PUMP2_PIN 24
#define PUMP_ENABLE_PIN 25
#define STATUS_LED_PIN 12
#define WARNING_LED_PIN 13

// Sensor data structure
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

// Pump status structure
typedef struct {
    bool pump1_active;
    bool pump2_active;
    time_t last_watered;
} pump_status_t;

// Hardware interface structure
typedef struct {
    struct gpiod_chip *chip;
    struct gpiod_line *dht22_line;
    struct gpiod_line *soil_moisture_line;
    struct gpiod_line *water_level_lines[3];
    struct gpiod_line *pump1_line;
    struct gpiod_line *pump2_line;
    struct gpiod_line *pump_enable_line;
    struct gpiod_line *status_led_line;
    struct gpiod_line *warning_led_line;
    bool simulation_mode;
    bool gpio_initialized;
    pump_status_t pump_status;
} hardware_interface_t;

// Function prototypes
hardware_interface_t* hardware_init(bool simulation_mode);
void hardware_cleanup(hardware_interface_t *hw);

bool read_dht22(hardware_interface_t *hw, float *temperature, float *humidity);
float read_soil_moisture(hardware_interface_t *hw);
float read_light_sensor(hardware_interface_t *hw);
void read_water_level(hardware_interface_t *hw, bool *top, bool *middle, bool *bottom);

bool control_pump(hardware_interface_t *hw, int pump_number, float duration_seconds, float water_amount_ml);
void set_status_led(hardware_interface_t *hw, const char *status);

sensor_data_t read_all_sensors(hardware_interface_t *hw);
float calculate_water_percentage(bool top, bool middle, bool bottom);

// Utility functions
void hardware_log(const char *level, const char *format, ...);
time_t get_current_timestamp(void);

#endif // HARDWARE_DRIVERS_H
