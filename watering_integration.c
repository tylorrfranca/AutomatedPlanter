/*
 * Watering Integration for Automated Planter
 * 
 * This code shows how to integrate with the website's watering API
 * to check if watering is needed and report when watering is complete.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>
#include "cJSON.h"  // You'll need to include cJSON library

// Configuration
#define API_BASE_URL "http://localhost:3000/api"
#define PLANT_ID 1  // Change this to your plant's ID
#define CHECK_INTERVAL_SECONDS 300  // Check every 5 minutes

// Response buffer for CURL
struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if(!ptr) {
        printf("Not enough memory!\n");
        return 0;
    }

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

// Check if watering is needed
int check_watering_needed(int *pump_duration) {
    CURL *curl;
    CURLcode res;
    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;
    
    char url[256];
    snprintf(url, sizeof(url), "%s/watering?plantId=%d", API_BASE_URL, PLANT_ID);
    
    curl = curl_easy_init();
    if(!curl) {
        printf("Failed to initialize CURL\n");
        return -1;
    }
    
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    
    res = curl_easy_perform(curl);
    
    if(res != CURLE_OK) {
        printf("CURL request failed: %s\n", curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        free(chunk.memory);
        return -1;
    }
    
    // Parse JSON response
    cJSON *json = cJSON_Parse(chunk.memory);
    if(!json) {
        printf("Failed to parse JSON\n");
        curl_easy_cleanup(curl);
        free(chunk.memory);
        return -1;
    }
    
    // Get values from JSON
    cJSON *needs_watering = cJSON_GetObjectItem(json, "needs_watering");
    cJSON *pump_duration_json = cJSON_GetObjectItem(json, "pump_duration_seconds");
    
    int should_water = 0;
    if(cJSON_IsBool(needs_watering)) {
        should_water = cJSON_IsTrue(needs_watering);
    }
    
    if(cJSON_IsNumber(pump_duration_json)) {
        *pump_duration = pump_duration_json->valueint;
    }
    
    printf("Watering check: needs_watering=%d, pump_duration=%d seconds\n", 
           should_water, *pump_duration);
    
    cJSON_Delete(json);
    curl_easy_cleanup(curl);
    free(chunk.memory);
    
    return should_water;
}

// Report that watering is complete
int report_watering_complete() {
    CURL *curl;
    CURLcode res;
    char url[256];
    snprintf(url, sizeof(url), "%s/watering", API_BASE_URL);
    
    // Create JSON payload
    char json_data[128];
    snprintf(json_data, sizeof(json_data), "{\"plantId\": %d}", PLANT_ID);
    
    curl = curl_easy_init();
    if(!curl) {
        printf("Failed to initialize CURL\n");
        return -1;
    }
    
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data);
    
    res = curl_easy_perform(curl);
    
    if(res != CURLE_OK) {
        printf("Failed to report watering: %s\n", curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        return -1;
    }
    
    printf("Successfully reported watering completion\n");
    
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    return 0;
}

// Simulate running the pump (replace with actual GPIO control)
void run_pump(int duration_seconds) {
    printf("Starting pump for %d seconds...\n", duration_seconds);
    
    // TODO: Replace with actual pump GPIO control
    // Example:
    // gpio_set_pin(PUMP_PIN, HIGH);
    
    sleep(duration_seconds);
    
    // gpio_set_pin(PUMP_PIN, LOW);
    
    printf("Pump stopped\n");
}

// Main watering loop
int main() {
    printf("Automated Planter - Watering Controller\n");
    printf("Plant ID: %d\n", PLANT_ID);
    printf("Checking every %d seconds\n\n", CHECK_INTERVAL_SECONDS);
    
    while(1) {
        int pump_duration = 0;
        
        // Check if watering is needed
        int needs_watering = check_watering_needed(&pump_duration);
        
        if(needs_watering == 1) {
            printf("🚰 Watering needed! Running pump for %d seconds...\n", pump_duration);
            
            // Run the pump
            run_pump(pump_duration);
            
            // Report completion to website
            if(report_watering_complete() == 0) {
                printf("✓ Watering complete and logged\n");
            } else {
                printf("✗ Failed to log watering (plant was still watered)\n");
            }
        } else if(needs_watering == 0) {
            printf("✓ No watering needed\n");
        } else {
            printf("✗ Error checking watering status\n");
        }
        
        printf("Waiting %d seconds until next check...\n\n", CHECK_INTERVAL_SECONDS);
        sleep(CHECK_INTERVAL_SECONDS);
    }
    
    return 0;
}

/*
 * Compilation instructions:
 * 
 * 1. Install dependencies:
 *    sudo apt-get install libcurl4-openssl-dev
 *    git clone https://github.com/DaveGamble/cJSON.git
 *    cd cJSON && make && sudo make install
 * 
 * 2. Compile:
 *    gcc -o watering_controller watering_integration.c -lcurl -lcjson
 * 
 * 3. Run:
 *    ./watering_controller
 * 
 * Integration with your existing code:
 * - Copy check_watering_needed() and report_watering_complete() functions
 * - Add them to your main sensor reading loop
 * - Call check_watering_needed() every 5 minutes
 * - If true, activate your pump GPIO for the specified duration
 * - Call report_watering_complete() when done
 */

