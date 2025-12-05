/*
 * pump_off.c - Turn OFF the water pump by setting GPIO 23 LOW
 * 
 * Usage: ./pump_off
 * Returns: 0 on success, 1 on failure
 * 
 * Compile: gcc -o pump_off pump_off.c -lgpiod
 */

#include <stdio.h>
#include <gpiod.h>

#define GPIO_CHIP "/dev/gpiochip4"
#define GPIO_PUMP 23

int main(void) {
    struct gpiod_chip *chip;
    struct gpiod_line_settings *settings;
    struct gpiod_line_config *line_cfg;
    struct gpiod_request_config *req_cfg;
    struct gpiod_line_request *request;
    unsigned int offset = GPIO_PUMP;
    int ret;

    // Open GPIO chip
    chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    // Create line settings for output, set LOW
    settings = gpiod_line_settings_new();
    if (!settings) {
        fprintf(stderr, "Failed to create line settings\n");
        gpiod_chip_close(chip);
        return 1;
    }
    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(settings, GPIOD_LINE_VALUE_INACTIVE);

    // Create line configuration
    line_cfg = gpiod_line_config_new();
    if (!line_cfg) {
        fprintf(stderr, "Failed to create line config\n");
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return 1;
    }

    ret = gpiod_line_config_add_line_settings(line_cfg, &offset, 1, settings);
    if (ret) {
        fprintf(stderr, "Failed to add line settings\n");
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return 1;
    }

    // Create request configuration
    req_cfg = gpiod_request_config_new();
    if (!req_cfg) {
        fprintf(stderr, "Failed to create request config\n");
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return 1;
    }
    gpiod_request_config_set_consumer(req_cfg, "water-pump");

    // Request the line (this sets the output value)
    request = gpiod_chip_request_lines(chip, req_cfg, line_cfg);
    if (!request) {
        perror("Failed to request GPIO line");
        gpiod_request_config_free(req_cfg);
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return 1;
    }

    printf("Pump OFF (GPIO %d set LOW)\n", GPIO_PUMP);

    // Cleanup - the line will stay LOW after release
    gpiod_line_request_release(request);
    gpiod_request_config_free(req_cfg);
    gpiod_line_config_free(line_cfg);
    gpiod_line_settings_free(settings);
    gpiod_chip_close(chip);

    return 0;
}

