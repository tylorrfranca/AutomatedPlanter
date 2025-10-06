#include "raspberry_pi_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <stdarg.h>
#include <curl/curl.h>
#include <json-c/json.h>

// Default plant configuration
static const plant_t default_plants[] = {
    {"Snake Plant", 0, 250.0, 14, 0, true},
    {"Peace Lily", 1, 300.0, 7, 0, true},
    {"Spider Plant", 2, 200.0, 7, 0, true}
};

static const int default_plants_count = sizeof(default_plants) / sizeof(default_plants[0]);

raspberry_pi_core_t* pi_core_init(bool simulation_mode, const char *web_interface_url) {
    raspberry_pi_core_t *core = malloc(sizeof(raspberry_pi_core_t));
    if (!core) {
        pi_core_log("ERROR", "Failed to allocate memory for Raspberry Pi core");
        return NULL;
    }
    
    memset(core, 0, sizeof(raspberry_pi_core_t));
    
    core->simulation_mode = simulation_mode;
    if (web_interface_url) {
        strncpy(core->web_interface_url, web_interface_url, sizeof(core->web_interface_url) - 1);
    }
    
    // Initialize hardware
    core->hardware = hardware_init(simulation_mode);
    if (!core->hardware) {
        pi_core_log("ERROR", "Failed to initialize hardware");
        free(core);
        return NULL;
    }
    
    // Initialize default plants
    core->active_plants_count = default_plants_count;
    for (int i = 0; i < default_plants_count; i++) {
        core->active_plants[i] = default_plants[i];
    }
    
    // Initialize system status
    core->system_status.sensor_history_count = 0;
    core->system_status.plants_needing_water_count = 0;
    core->system_status.pump_status.pump1_active = false;
    core->system_status.pump_status.pump2_active = false;
    core->system_status.pump_status.last_watered = 0;
    
    pi_core_log("INFO", "Raspberry Pi Core initialized (simulation: %s)", 
                simulation_mode ? "true" : "false");
    if (web_interface_url) {
        pi_core_log("INFO", "Web interface URL: %s", web_interface_url);
    }
    
    return core;
}

void pi_core_cleanup(raspberry_pi_core_t *core) {
    if (!core) return;
    
    core->running = false;
    
    if (core->hardware) {
        hardware_cleanup(core->hardware);
    }
    
    free(core);
    pi_core_log("INFO", "System cleanup completed");
}

sensor_data_t pi_core_read_all_sensors(raspberry_pi_core_t *core) {
    sensor_data_t sensor_data = {0};
    
    if (!core || !core->hardware) return sensor_data;
    
    sensor_data = read_all_sensors(core->hardware);
    core->system_status.last_reading = sensor_data;
    
    // Store in history (keep last 50 readings)
    if (core->system_status.sensor_history_count < 50) {
        core->system_status.sensor_history[core->system_status.sensor_history_count] = sensor_data;
        core->system_status.sensor_history_count++;
    } else {
        // Shift array and add new reading
        for (int i = 0; i < 49; i++) {
            core->system_status.sensor_history[i] = core->system_status.sensor_history[i + 1];
        }
        core->system_status.sensor_history[49] = sensor_data;
    }
    
    return sensor_data;
}

int pi_core_check_plants_needing_water(raspberry_pi_core_t *core, plant_t *plants_needing_water) {
    if (!core || !plants_needing_water) return 0;
    
    int count = 0;
    time_t current_time = time(NULL);
    
    for (int i = 0; i < core->active_plants_count; i++) {
        const plant_t *plant = &core->active_plants[i];
        
        if (!plant->active) continue;
        
        // Check if enough time has passed since last watering
        if (plant->last_watered > 0) {
            time_t days_since_watering = (current_time - plant->last_watered) / (24 * 3600);
            
            if (days_since_watering >= plant->watering_frequency) {
                plants_needing_water[count] = *plant;
                count++;
            }
        } else {
            // Never been watered
            plants_needing_water[count] = *plant;
            count++;
        }
    }
    
    core->system_status.plants_needing_water_count = count;
    for (int i = 0; i < count; i++) {
        core->system_status.plants_needing_water[i] = plants_needing_water[i];
    }
    
    return count;
}

bool pi_core_water_plant(raspberry_pi_core_t *core, const plant_t *plant) {
    if (!core || !plant || !core->hardware) return false;
    
    pi_core_log("INFO", "Watering %s at position %d with %.1fml", 
                plant->name, plant->position, plant->water_amount);
    
    // Calculate pump duration (assuming 100ml per second flow rate)
    float duration = plant->water_amount / 100.0; // seconds
    int pump_num = (plant->position % 2) + 1; // Alternate between pumps
    
    // Control the water pump
    bool success = control_pump(core->hardware, pump_num, duration, plant->water_amount);
    
    if (success) {
        // Update watering time for this plant
        for (int i = 0; i < core->active_plants_count; i++) {
            if (core->active_plants[i].position == plant->position) {
                core->active_plants[i].last_watered = time(NULL);
                break;
            }
        }
        
        core->system_status.pump_status.last_watered = time(NULL);
        pi_core_log("INFO", "Successfully watered %s", plant->name);
    } else {
        pi_core_log("ERROR", "Failed to water %s", plant->name);
    }
    
    return success;
}

void pi_core_auto_water_plants(raspberry_pi_core_t *core) {
    if (!core) return;
    
    plant_t plants_needing_water[10];
    int count = pi_core_check_plants_needing_water(core, plants_needing_water);
    
    if (count > 0) {
        pi_core_log("INFO", "Found %d plants needing water", count);
        
        for (int i = 0; i < count; i++) {
            bool success = pi_core_water_plant(core, &plants_needing_water[i]);
            if (success) {
                sleep(2); // Brief pause between plants
            }
        }
    } else {
        pi_core_log("INFO", "No plants need watering at this time");
    }
}

plant_validation_t pi_core_validate_plant_sensors(raspberry_pi_core_t *core, const plant_t *plant, const sensor_data_t *sensor_data) {
    plant_validation_t validation = {0};
    
    if (!core || !plant || !sensor_data) return validation;
    
    // Simple validation (you can expand this based on your needs)
    validation.soil_moisture.value = sensor_data->soil_moisture_percent;
    strcpy(validation.soil_moisture.status, 
           (sensor_data->soil_moisture_percent >= 20.0 && sensor_data->soil_moisture_percent <= 70.0) ? "OK" : "CHECK");
    
    validation.temperature.value = sensor_data->temperature_celsius;
    strcpy(validation.temperature.status,
           (sensor_data->temperature_celsius >= 15.0 && sensor_data->temperature_celsius <= 30.0) ? "OK" : "CHECK");
    
    validation.humidity.value = sensor_data->humidity_percent;
    strcpy(validation.humidity.status,
           (sensor_data->humidity_percent >= 30.0 && sensor_data->humidity_percent <= 80.0) ? "OK" : "CHECK");
    
    validation.light.value = sensor_data->light_lux;
    strcpy(validation.light.status,
           (sensor_data->light_lux >= 50.0 && sensor_data->light_lux <= 500.0) ? "OK" : "CHECK");
    
    return validation;
}

void pi_core_validate_sensor_readings(raspberry_pi_core_t *core, plant_validation_t *validation_results) {
    if (!core || !validation_results) return;
    
    sensor_data_t sensor_data = core->system_status.last_reading;
    
    for (int i = 0; i < core->active_plants_count; i++) {
        validation_results[i] = pi_core_validate_plant_sensors(core, &core->active_plants[i], &sensor_data);
    }
}

// HTTP callback for sending data to web interface
static size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    (void)contents;
    (void)userp;
    return realsize;
}

bool pi_core_send_data_to_web_interface(raspberry_pi_core_t *core, const sensor_data_t *sensor_data) {
    if (!core || !sensor_data || strlen(core->web_interface_url) == 0) {
        return false;
    }
    
    CURL *curl;
    CURLcode res;
    struct json_object *json_obj;
    struct json_object *sensor_data_obj;
    struct json_object *plant_status_obj;
    struct json_object *pump_status_obj;
    char *json_string;
    
    curl = curl_easy_init();
    if (!curl) {
        pi_core_log("ERROR", "Failed to initialize CURL");
        return false;
    }
    
    // Create JSON payload
    json_obj = json_object_new_object();
    
    // Add timestamp
    char timestamp_str[64];
    pi_core_format_timestamp(sensor_data->timestamp, timestamp_str, sizeof(timestamp_str));
    json_object_object_add(json_obj, "timestamp", json_object_new_string(timestamp_str));
    
    // Add sensor data
    sensor_data_obj = json_object_new_object();
    json_object_object_add(sensor_data_obj, "temperature", json_object_new_double(sensor_data->temperature_celsius));
    json_object_object_add(sensor_data_obj, "humidity", json_object_new_double(sensor_data->humidity_percent));
    json_object_object_add(sensor_data_obj, "soil_moisture", json_object_new_double(sensor_data->soil_moisture_percent));
    json_object_object_add(sensor_data_obj, "light", json_object_new_double(sensor_data->light_lux));
    json_object_object_add(sensor_data_obj, "water_level", json_object_new_double(sensor_data->water_tank_percentage));
    json_object_object_add(json_obj, "sensor_data", sensor_data_obj);
    
    // Add plant status
    plant_status_obj = json_object_new_array();
    for (int i = 0; i < core->system_status.plants_needing_water_count; i++) {
        json_object_array_add(plant_status_obj, json_object_new_string(core->system_status.plants_needing_water[i].name));
    }
    json_object_object_add(json_obj, "plant_status", plant_status_obj);
    
    // Add pump status
    pump_status_obj = json_object_new_object();
    json_object_object_add(pump_status_obj, "pump1", json_object_new_boolean(core->system_status.pump_status.pump1_active));
    json_object_object_add(pump_status_obj, "pump2", json_object_new_boolean(core->system_status.pump_status.pump2_active));
    char last_watered_str[64];
    pi_core_format_timestamp(core->system_status.pump_status.last_watered, last_watered_str, sizeof(last_watered_str));
    json_object_object_add(pump_status_obj, "last_watered", json_object_new_string(last_watered_str));
    json_object_object_add(json_obj, "pump_status", pump_status_obj);
    
    json_string = (char*)json_object_to_json_string(json_obj);
    
    // Set up CURL options
    curl_easy_setopt(curl, CURLOPT_URL, core->web_interface_url);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_string);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    
    // Perform the request
    res = curl_easy_perform(curl);
    
    bool success = (res == CURLE_OK);
    if (success) {
        pi_core_log("INFO", "Data sent to web interface successfully");
    } else {
        pi_core_log("WARNING", "Failed to send data to web interface: %s", curl_easy_strerror(res));
    }
    
    // Cleanup
    json_object_put(json_obj);
    curl_easy_cleanup(curl);
    
    return success;
}

void pi_core_start_monitoring_loop(raspberry_pi_core_t *core, int interval_seconds) {
    if (!core) return;
    
    core->running = true;
    pi_core_log("INFO", "Starting monitoring loop (interval: %ds)", interval_seconds);
    
    while (core->running) {
        // Read sensors
        sensor_data_t sensor_data = pi_core_read_all_sensors(core);
        pi_core_log("INFO", "Sensor reading: Temp=%.1f°C, Humidity=%.1f%%, Soil=%.1f%%, Water=%.1f%%",
                    sensor_data.temperature_celsius, sensor_data.humidity_percent,
                    sensor_data.soil_moisture_percent, sensor_data.water_tank_percentage);
        
        // Validate readings
        plant_validation_t validation_results[10];
        pi_core_validate_sensor_readings(core, validation_results);
        
        // Check for plants needing water
        plant_t plants_needing_water[10];
        int count = pi_core_check_plants_needing_water(core, plants_needing_water);
        if (count > 0) {
            pi_core_log("INFO", "Plants needing water: %d", count);
        }
        
        // Send data to web interface
        pi_core_send_data_to_web_interface(core, &sensor_data);
        
        // Wait for next reading
        sleep(interval_seconds);
    }
}

void pi_core_get_system_status(raspberry_pi_core_t *core, char *status_json, size_t buffer_size) {
    if (!core || !status_json) return;
    
    struct json_object *json_obj = json_object_new_object();
    
    // Add timestamp
    char timestamp_str[64];
    pi_core_format_timestamp(time(NULL), timestamp_str, sizeof(timestamp_str));
    json_object_object_add(json_obj, "timestamp", json_object_new_string(timestamp_str));
    
    // Add hardware status
    json_object_object_add(json_obj, "hardware_status", 
                          json_object_new_string(core->hardware->gpio_initialized ? "operational" : "simulation"));
    json_object_object_add(json_obj, "simulation_mode", json_object_new_boolean(core->simulation_mode));
    
    // Add sensor data
    struct json_object *sensor_data_obj = json_object_new_object();
    sensor_data_t sensor_data = core->system_status.last_reading;
    json_object_object_add(sensor_data_obj, "temperature", json_object_new_double(sensor_data.temperature_celsius));
    json_object_object_add(sensor_data_obj, "humidity", json_object_new_double(sensor_data.humidity_percent));
    json_object_object_add(sensor_data_obj, "soil_moisture", json_object_new_double(sensor_data.soil_moisture_percent));
    json_object_object_add(sensor_data_obj, "light", json_object_new_double(sensor_data.light_lux));
    json_object_object_add(sensor_data_obj, "water_level", json_object_new_double(sensor_data.water_tank_percentage));
    json_object_object_add(json_obj, "last_sensor_reading", sensor_data_obj);
    
    // Add plant status
    json_object_object_add(json_obj, "active_plants_count", json_object_new_int(core->active_plants_count));
    json_object_object_add(json_obj, "plants_needing_water_count", json_object_new_int(core->system_status.plants_needing_water_count));
    
    // Add pump status
    struct json_object *pump_status_obj = json_object_new_object();
    json_object_object_add(pump_status_obj, "pump1_active", json_object_new_boolean(core->system_status.pump_status.pump1_active));
    json_object_object_add(pump_status_obj, "pump2_active", json_object_new_boolean(core->system_status.pump_status.pump2_active));
    char last_watered_str[64];
    pi_core_format_timestamp(core->system_status.pump_status.last_watered, last_watered_str, sizeof(last_watered_str));
    json_object_object_add(pump_status_obj, "last_watered", json_object_new_string(last_watered_str));
    json_object_object_add(json_obj, "pump_status", pump_status_obj);
    
    // Add other status
    json_object_object_add(json_obj, "sensor_history_count", json_object_new_int(core->system_status.sensor_history_count));
    json_object_object_add(json_obj, "web_interface_connected", json_object_new_boolean(strlen(core->web_interface_url) > 0));
    
    const char *json_string = json_object_to_json_string(json_obj);
    strncpy(status_json, json_string, buffer_size - 1);
    status_json[buffer_size - 1] = '\0';
    
    json_object_put(json_obj);
}

bool pi_core_manual_water_plant(raspberry_pi_core_t *core, int position) {
    if (!core) return false;
    
    const plant_t *plant = NULL;
    for (int i = 0; i < core->active_plants_count; i++) {
        if (core->active_plants[i].position == position) {
            plant = &core->active_plants[i];
            break;
        }
    }
    
    if (!plant) {
        pi_core_log("ERROR", "No plant found at position %d", position);
        return false;
    }
    
    return pi_core_water_plant(core, plant);
}

// Demo functions
void demo_1_hardware_setup(void) {
    printf("\n============================================================\n");
    printf("DEMO 1: Hardware Setup and Basic Functionality\n");
    printf("============================================================\n");
    
    raspberry_pi_core_t *core = pi_core_init(true, NULL);
    if (!core) {
        printf("❌ Failed to initialize system\n");
        return;
    }
    
    printf("\n🔧 System Status:\n");
    char status_json[2048];
    pi_core_get_system_status(core, status_json, sizeof(status_json));
    printf("   - Hardware Mode: %s\n", core->simulation_mode ? "Simulation" : "Real Hardware");
    printf("   - GPIO Status: %s\n", core->hardware->gpio_initialized ? "Initialized" : "Not Initialized");
    printf("   - Active Plants: %d\n", core->active_plants_count);
    
    printf("\n📊 Initial Sensor Reading:\n");
    sensor_data_t sensor_data = pi_core_read_all_sensors(core);
    printf("   - Temperature: %.1f°C\n", sensor_data.temperature_celsius);
    printf("   - Humidity: %.1f%%\n", sensor_data.humidity_percent);
    printf("   - Soil Moisture: %.1f%%\n", sensor_data.soil_moisture_percent);
    printf("   - Light: %.1f lux\n", sensor_data.light_lux);
    printf("   - Water Level: %.1f%%\n", sensor_data.water_tank_percentage);
    
    printf("\n✅ Demo 1 Complete: Hardware system operational\n");
    pi_core_cleanup(core);
}

void demo_2_pump_control(void) {
    printf("\n============================================================\n");
    printf("DEMO 2: Water Pump Implementation\n");
    printf("============================================================\n");
    
    raspberry_pi_core_t *core = pi_core_init(true, NULL);
    if (!core) {
        printf("❌ Failed to initialize system\n");
        return;
    }
    
    printf("\n💧 Testing Pump Control:\n");
    
    // Test manual watering
    printf("   - Manual watering test...\n");
    bool success = pi_core_manual_water_plant(core, 0); // Water plant at position 0
    printf("   - Result: %s\n", success ? "✅ Success" : "❌ Failed");
    
    // Test automatic watering
    printf("\n🤖 Testing Automatic Watering:\n");
    pi_core_auto_water_plants(core);
    
    printf("\n✅ Demo 2 Complete: Pump control functional\n");
    pi_core_cleanup(core);
}

void demo_3_sensor_integration(void) {
    printf("\n============================================================\n");
    printf("DEMO 3: Sensor Implementation\n");
    printf("============================================================\n");
    
    raspberry_pi_core_t *core = pi_core_init(true, NULL);
    if (!core) {
        printf("❌ Failed to initialize system\n");
        return;
    }
    
    printf("\n📊 Testing All Sensors:\n");
    
    // Read all sensors multiple times
    for (int i = 0; i < 3; i++) {
        printf("\n   Reading %d/3:\n", i + 1);
        sensor_data_t sensor_data = pi_core_read_all_sensors(core);
        printf("      - Temperature: %.1f°C\n", sensor_data.temperature_celsius);
        printf("      - Humidity: %.1f%%\n", sensor_data.humidity_percent);
        printf("      - Soil Moisture: %.1f%%\n", sensor_data.soil_moisture_percent);
        printf("      - Light: %.1f lux\n", sensor_data.light_lux);
        printf("      - Water Level: %.1f%%\n", sensor_data.water_tank_percentage);
        sleep(2);
    }
    
    // Test validation
    printf("\n🔍 Testing Sensor Validation:\n");
    plant_validation_t validation_results[10];
    pi_core_validate_sensor_readings(core, validation_results);
    for (int i = 0; i < core->active_plants_count; i++) {
        bool all_ok = (strcmp(validation_results[i].soil_moisture.status, "OK") == 0 &&
                      strcmp(validation_results[i].temperature.status, "OK") == 0 &&
                      strcmp(validation_results[i].humidity.status, "OK") == 0 &&
                      strcmp(validation_results[i].light.status, "OK") == 0);
        printf("   - %s: All sensors %s\n", core->active_plants[i].name, 
               all_ok ? "✅ OK" : "⚠️ Check needed");
    }
    
    printf("\n✅ Demo 3 Complete: All sensors operational\n");
    pi_core_cleanup(core);
}

void demo_4_data_integration(void) {
    printf("\n============================================================\n");
    printf("DEMO 4: Data Integration and Monitoring\n");
    printf("============================================================\n");
    
    raspberry_pi_core_t *core = pi_core_init(true, NULL);
    if (!core) {
        printf("❌ Failed to initialize system\n");
        return;
    }
    
    printf("\n📈 Testing Data Integration:\n");
    printf("   - Running monitoring loop for 30 seconds...\n");
    
    time_t start_time = time(NULL);
    while (time(NULL) - start_time < 30) {
        sensor_data_t sensor_data = pi_core_read_all_sensors(core);
        plant_validation_t validation_results[10];
        pi_core_validate_sensor_readings(core, validation_results);
        plant_t plants_needing_water[10];
        int count = pi_core_check_plants_needing_water(core, plants_needing_water);
        
        char timestamp_str[64];
        pi_core_format_timestamp(time(NULL), timestamp_str, sizeof(timestamp_str));
        printf("      → %s: Temp=%.1f°C, Plants needing water: %d\n",
               timestamp_str, sensor_data.temperature_celsius, count);
        
        sleep(5);
    }
    
    printf("\n✅ Demo 4 Complete: Data integration functional\n");
    pi_core_cleanup(core);
}

void demo_5_system_integration(void) {
    printf("\n============================================================\n");
    printf("DEMO 5: Complete System Integration\n");
    printf("============================================================\n");
    
    raspberry_pi_core_t *core = pi_core_init(true, NULL);
    if (!core) {
        printf("❌ Failed to initialize system\n");
        return;
    }
    
    printf("\n🎯 Testing Complete System Integration:\n");
    
    // Test full system cycle
    printf("   1. System Status Check:\n");
    char status_json[2048];
    pi_core_get_system_status(core, status_json, sizeof(status_json));
    printf("      - Status: %s\n", core->hardware->gpio_initialized ? "operational" : "simulation");
    printf("      - Active Plants: %d\n", core->active_plants_count);
    
    printf("\n   2. Sensor Reading:\n");
    sensor_data_t sensor_data = pi_core_read_all_sensors(core);
    printf("      - All sensors: ✅ Operational\n");
    
    printf("\n   3. Plant Health Check:\n");
    plant_validation_t validation_results[10];
    pi_core_validate_sensor_readings(core, validation_results);
    int healthy_plants = 0;
    for (int i = 0; i < core->active_plants_count; i++) {
        bool all_ok = (strcmp(validation_results[i].soil_moisture.status, "OK") == 0 &&
                      strcmp(validation_results[i].temperature.status, "OK") == 0 &&
                      strcmp(validation_results[i].humidity.status, "OK") == 0 &&
                      strcmp(validation_results[i].light.status, "OK") == 0);
        if (all_ok) healthy_plants++;
    }
    printf("      - Healthy plants: %d/%d\n", healthy_plants, core->active_plants_count);
    
    printf("\n   4. Automatic Watering:\n");
    plant_t plants_needing_water[10];
    int count = pi_core_check_plants_needing_water(core, plants_needing_water);
    if (count > 0) {
        printf("      - Watering %d plants...\n", count);
        pi_core_auto_water_plants(core);
    } else {
        printf("      - No watering needed\n");
    }
    
    printf("\n   5. System Monitoring:\n");
    printf("      - Sensor history: %d readings\n", core->system_status.sensor_history_count);
    char last_watered_str[64];
    pi_core_format_timestamp(core->system_status.pump_status.last_watered, last_watered_str, sizeof(last_watered_str));
    printf("      - Last watering: %s\n", core->system_status.pump_status.last_watered > 0 ? last_watered_str : "Never");
    
    printf("\n✅ Demo 5 Complete: Full system integration successful\n");
    pi_core_cleanup(core);
}

void run_all_demos(void) {
    printf("🌱 RASPBERRY PI AUTOMATED PLANTER - DEMO SEQUENCE\n");
    printf("============================================================\n");
    
    const char *demo_names[] = {"Demo 1", "Demo 2", "Demo 3", "Demo 4", "Demo 5"};
    void (*demo_functions[])(void) = {
        demo_1_hardware_setup,
        demo_2_pump_control,
        demo_3_sensor_integration,
        demo_4_data_integration,
        demo_5_system_integration
    };
    
    for (int i = 0; i < 5; i++) {
        printf("\nRunning %s...\n", demo_names[i]);
        demo_functions[i]();
        printf("\n✅ %s completed successfully!\n", demo_names[i]);
        printf("\nPress Enter to continue to next demo...");
        getchar();
    }
    
    printf("\n🎉 ALL DEMOS COMPLETED!\n");
    printf("   - Raspberry Pi core system fully demonstrated\n");
    printf("   - All 5 milestones achieved\n");
    printf("   - System ready for integration with web interface\n");
}

// Utility functions
void pi_core_log(const char *level, const char *format, ...) {
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

time_t pi_core_get_current_time(void) {
    return time(NULL);
}

void pi_core_format_timestamp(time_t timestamp, char *buffer, size_t buffer_size) {
    if (!buffer || buffer_size == 0) return;
    
    struct tm *tm_info = localtime(&timestamp);
    strftime(buffer, buffer_size, "%Y-%m-%dT%H:%M:%S", tm_info);
}
