#include "raspberry_pi_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>

// Global variables for signal handling
static raspberry_pi_core_t *g_core = NULL;
static volatile bool g_running = true;

// Signal handler for graceful shutdown
void signal_handler(int sig) {
    (void)sig; // Suppress unused parameter warning
    printf("\n🛑 Shutting down...\n");
    g_running = false;
    if (g_core) {
        g_core->running = false;
    }
}

// Monitoring thread function
void* monitoring_thread(void *arg) {
    raspberry_pi_core_t *core = (raspberry_pi_core_t*)arg;
    
    printf("🔄 Starting monitoring loop...\n");
    
    while (g_running && core->running) {
        // Check plants and take necessary actions
        plant_t plants_needing_water[10];
        int count = pi_core_check_plants_needing_water(core, plants_needing_water);
        
        if (count > 0) {
            printf("💧 %d plants need watering:\n", count);
            for (int i = 0; i < count; i++) {
                printf("   - %s at position %d\n", plants_needing_water[i].name, plants_needing_water[i].position);
                pi_core_water_plant(core, &plants_needing_water[i]);
            }
        }
        
        // Log sensor data
        sensor_data_t sensor_data = pi_core_read_all_sensors(core);
        printf("📊 Sensor data: Temp=%.1f°C, Humidity=%.1f%%, Soil=%.1f%%, Water=%.1f%%\n",
               sensor_data.temperature_celsius, sensor_data.humidity_percent,
               sensor_data.soil_moisture_percent, sensor_data.water_tank_percentage);
        
        // Validate sensor readings
        plant_validation_t validation_results[10];
        pi_core_validate_sensor_readings(core, validation_results);
        
        for (int i = 0; i < core->active_plants_count; i++) {
            const plant_t *plant = &core->active_plants[i];
            const plant_validation_t *validation = &validation_results[i];
            
            // Check for issues and take automatic action
            if (strcmp(validation->soil_moisture.status, "CHECK") == 0) {
                printf("⚠️  %s: Soil moisture issue - %.1f%%\n", plant->name, validation->soil_moisture.value);
                if (validation->soil_moisture.value < 20.0) {
                    printf("🚿 Auto-watering %s due to low soil moisture\n", plant->name);
                    pi_core_water_plant(core, plant);
                }
            }
            
            if (strcmp(validation->temperature.status, "CHECK") == 0) {
                printf("⚠️  %s: Temperature issue - %.1f°C\n", plant->name, validation->temperature.value);
            }
            
            if (strcmp(validation->humidity.status, "CHECK") == 0) {
                printf("⚠️  %s: Humidity issue - %.1f%%\n", plant->name, validation->humidity.value);
            }
            
            if (strcmp(validation->light.status, "CHECK") == 0) {
                printf("⚠️  %s: Light issue - %.1f lux\n", plant->name, validation->light.value);
            }
        }
        
        sleep(60); // Check every minute
    }
    
    printf("🛑 Monitoring loop stopped\n");
    return NULL;
}

void show_status(raspberry_pi_core_t *core) {
    printf("\n📊 System Status:\n");
    printf("==================================================\n");
    
    // Plant status
    printf("Active Plants: %d\n", core->active_plants_count);
    for (int i = 0; i < core->active_plants_count; i++) {
        const plant_t *plant = &core->active_plants[i];
        printf("  - %s (Position %d) - %s\n", plant->name, plant->position, 
               plant->active ? "active" : "inactive");
    }
    
    // Plants needing water
    plant_t plants_needing_water[10];
    int count = pi_core_check_plants_needing_water(core, plants_needing_water);
    printf("\nPlants Needing Water: %d\n", count);
    for (int i = 0; i < count; i++) {
        printf("  - %s (Position %d)\n", plants_needing_water[i].name, plants_needing_water[i].position);
    }
    
    // System configuration
    printf("\nSystem Configuration:\n");
    printf("  - Hardware Mode: %s\n", core->simulation_mode ? "Simulation" : "Real Hardware");
    printf("  - GPIO Status: %s\n", core->hardware->gpio_initialized ? "Initialized" : "Not Initialized");
    printf("  - Web Interface: %s\n", strlen(core->web_interface_url) > 0 ? "Connected" : "Not Connected");
    printf("  - Sensor History: %d readings\n", core->system_status.sensor_history_count);
}

void run_demo(raspberry_pi_core_t *core, int demo_number) {
    printf("\n🎯 Running Demo %d...\n", demo_number);
    
    switch (demo_number) {
        case 1:
            demo_1_hardware_setup();
            break;
        case 2:
            demo_2_pump_control();
            break;
        case 3:
            demo_3_sensor_integration();
            break;
        case 4:
            demo_4_data_integration();
            break;
        case 5:
            demo_5_system_integration();
            break;
        default:
            printf("❌ Invalid demo number: %d\n", demo_number);
            break;
    }
}

void print_help(void) {
    printf("\nAvailable commands:\n");
    printf("  ./automated_planter monitor   - Start monitoring loop\n");
    printf("  ./automated_planter status    - Show system status\n");
    printf("  ./automated_planter demo N    - Run demo N (1-5)\n");
    printf("  ./automated_planter demo all  - Run all demos\n");
    printf("  ./automated_planter help      - Show this help\n");
    printf("\nOptions:\n");
    printf("  --simulation, -s             - Use simulation mode\n");
    printf("  --web-url URL                - Connect to web interface\n");
    printf("\nDefault: Start monitoring loop\n");
}

int main(int argc, char *argv[]) {
    printf("🌱 Automated Planter System\n");
    printf("========================================\n");
    
    // Set up signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Parse command line arguments
    bool simulation_mode = false;
    char *web_url = NULL;
    char *command = NULL;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--simulation") == 0 || strcmp(argv[i], "-s") == 0) {
            simulation_mode = true;
        } else if (strcmp(argv[i], "--web-url") == 0 && i + 1 < argc) {
            web_url = argv[++i];
        } else if (strcmp(argv[i], "demo") == 0 || strcmp(argv[i], "monitor") == 0 || 
                   strcmp(argv[i], "status") == 0 || strcmp(argv[i], "help") == 0) {
            command = argv[i];
        }
    }
    
    // Initialize system
    g_core = pi_core_init(simulation_mode, web_url);
    if (!g_core) {
        printf("❌ Failed to initialize system\n");
        return 1;
    }
    
    printf("🌱 Automated Planter System Initialized\n");
    printf("   - Active plants: %d\n", g_core->active_plants_count);
    printf("   - Hardware mode: %s\n", simulation_mode ? "Simulation" : "Real Hardware");
    printf("   - GPIO status: %s\n", g_core->hardware->gpio_initialized ? "Initialized" : "Not initialized");
    if (web_url) {
        printf("   - Web interface: %s\n", web_url);
    }
    
    // Execute command
    if (command == NULL) {
        // Default: start monitoring loop
        printf("\nStarting monitoring loop...\n");
        printf("Press Ctrl+C to stop\n");
        
        pthread_t monitor_thread;
        if (pthread_create(&monitor_thread, NULL, monitoring_thread, g_core) != 0) {
            printf("❌ Failed to create monitoring thread\n");
            pi_core_cleanup(g_core);
            return 1;
        }
        
        // Wait for monitoring thread to finish
        pthread_join(monitor_thread, NULL);
        
    } else if (strcmp(command, "monitor") == 0) {
        // Start monitoring only
        printf("\nStarting monitoring loop...\n");
        printf("Press Ctrl+C to stop\n");
        
        pthread_t monitor_thread;
        if (pthread_create(&monitor_thread, NULL, monitoring_thread, g_core) != 0) {
            printf("❌ Failed to create monitoring thread\n");
            pi_core_cleanup(g_core);
            return 1;
        }
        
        pthread_join(monitor_thread, NULL);
        
    } else if (strcmp(command, "status") == 0) {
        // Show status
        show_status(g_core);
        
    } else if (strcmp(command, "demo") == 0) {
        // Run demos
        if (argc > 2) {
            if (strcmp(argv[2], "all") == 0) {
                run_all_demos();
            } else {
                int demo_num = atoi(argv[2]);
                if (demo_num >= 1 && demo_num <= 5) {
                    run_demo(g_core, demo_num);
                } else {
                    printf("❌ Invalid demo number: %d\n", demo_num);
                    printf("Please specify demo number (1-5) or 'all'\n");
                    printf("Usage: ./automated_planter demo [1|2|3|4|5|all]\n");
                }
            }
        } else {
            printf("Please specify demo number (1-5) or 'all'\n");
            printf("Usage: ./automated_planter demo [1|2|3|4|5|all]\n");
        }
        
    } else if (strcmp(command, "help") == 0) {
        print_help();
        
    } else {
        printf("Unknown command: %s\n", command);
        printf("Use './automated_planter help' for available commands\n");
    }
    
    // Cleanup
    pi_core_cleanup(g_core);
    
    printf("👋 Goodbye!\n");
    return 0;
}
