#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    struct gpiod_chip *chip;
    struct gpiod_line_request *request;
    struct gpiod_request_config *req_cfg;
    struct gpiod_line_config *line_cfg;
    struct gpiod_line_settings *settings;
    unsigned int offset = 17;  // GPIO17
    enum gpiod_line_value value;
    int ret;

    // Open GPIO chip (gpiochip4 on Raspberry Pi 5)
    chip = gpiod_chip_open("/dev/gpiochip4");
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    // Create line settings for input
    settings = gpiod_line_settings_new();
    if (!settings) {
        fprintf(stderr, "Failed to create line settings\n");
        gpiod_chip_close(chip);
        return 1;
    }
    
    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_INPUT);

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
    
    gpiod_request_config_set_consumer(req_cfg, "gpio-read");

    // Request the line
    request = gpiod_chip_request_lines(chip, req_cfg, line_cfg);
    if (!request) {
        perror("Failed to request GPIO line");
        gpiod_request_config_free(req_cfg);
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return 1;
    }

    printf("Reading GPIO17. Press Ctrl+C to exit.\n\n");

    // Read GPIO value continuously
    while (1) {
        value = gpiod_line_request_get_value(request, offset);
        if (value < 0) {
            perror("Failed to read GPIO value");
            break;
        }

        printf("GPIO17 = %d\n", value);
        sleep(1);  // Read every second
    }

    // Cleanup
    gpiod_line_request_release(request);
    gpiod_request_config_free(req_cfg);
    gpiod_line_config_free(line_cfg);
    gpiod_line_settings_free(settings);
    gpiod_chip_close(chip);

    return 0;
}
