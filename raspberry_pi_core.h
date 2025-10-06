#ifndef RASPBERRY_PI_CORE_H
#define RASPBERRY_PI_CORE_H

#include "hardware_drivers.h"
#include <stdbool.h>
#include <time.h>

// Plant structure
typedef struct {
    char name[64];
    int position;
    float water_amount;
    int watering_frequency;
    time_t last_watered;
    bool active;
} plant_t;

// Plant validation structure
typedef struct {
    float value;
    char status[16];
} sensor_validation_t;

typedef struct {
    sensor_validation_t soil_moisture;
    sensor_validation_t temperature;
    sensor_validation_t humidity;
    sensor_validation_t light;
} plant_validation_t;

// System status structure
typedef struct {
    sensor_data_t last_reading;
    plant_t plants_needing_water[10];
    int plants_needing_water_count;
    sensor_data_t sensor_history[50];
    int sensor_history_count;
    pump_status_t pump_status;
} system_status_t;

// Raspberry Pi core structure
typedef struct {
    hardware_interface_t *hardware;
    bool simulation_mode;
    char web_interface_url[256];
    bool running;
    plant_t active_plants[10];
    int active_plants_count;
    system_status_t system_status;
} raspberry_pi_core_t;

// Function prototypes
raspberry_pi_core_t* pi_core_init(bool simulation_mode, const char *web_interface_url);
void pi_core_cleanup(raspberry_pi_core_t *core);

sensor_data_t pi_core_read_all_sensors(raspberry_pi_core_t *core);
int pi_core_check_plants_needing_water(raspberry_pi_core_t *core, plant_t *plants_needing_water);
bool pi_core_water_plant(raspberry_pi_core_t *core, const plant_t *plant);
void pi_core_auto_water_plants(raspberry_pi_core_t *core);

plant_validation_t pi_core_validate_plant_sensors(raspberry_pi_core_t *core, const plant_t *plant, const sensor_data_t *sensor_data);
void pi_core_validate_sensor_readings(raspberry_pi_core_t *core, plant_validation_t *validation_results);

bool pi_core_send_data_to_web_interface(raspberry_pi_core_t *core, const sensor_data_t *sensor_data);
void pi_core_start_monitoring_loop(raspberry_pi_core_t *core, int interval_seconds);

void pi_core_get_system_status(raspberry_pi_core_t *core, char *status_json, size_t buffer_size);
bool pi_core_manual_water_plant(raspberry_pi_core_t *core, int position);

// Demo functions
void demo_1_hardware_setup(void);
void demo_2_pump_control(void);
void demo_3_sensor_integration(void);
void demo_4_data_integration(void);
void demo_5_system_integration(void);
void run_all_demos(void);

// Utility functions
void pi_core_log(const char *level, const char *format, ...);
time_t pi_core_get_current_time(void);
void pi_core_format_timestamp(time_t timestamp, char *buffer, size_t buffer_size);

#endif // RASPBERRY_PI_CORE_H
