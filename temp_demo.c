#include <gpiod.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <time.h>

#define GPIO_CHIP "/dev/gpiochip0"
#define DATA_PIN 27
#define MAX_TIMINGS 85

// Microsecond delay using nanosleep
static void delay_us(unsigned int usec)
{
    struct timespec ts;
    ts.tv_sec = usec / 1000000;
    ts.tv_nsec = (usec % 1000000) * 1000;
    nanosleep(&ts, NULL);
}

int main(void)
{
    struct gpiod_chip *chip = NULL;
    struct gpiod_line *line = NULL;
    struct gpiod_line_settings *settings = NULL;
    struct gpiod_request_config *req_cfg = NULL;
    struct gpiod_line_request *request = NULL;
    uint8_t data[5] = {0};
    int last_state = 1, counter = 0, bit_index = 0, i;

    // --- Open GPIO chip ---
    chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) {
        perror("gpiod_chip_open");
        return 1;
    }

    // --- Get the GPIO line ---
    line = gpiod_chip_get_line(chip, DATA_PIN);
    if (!line) {
        perror("gpiod_chip_get_line");
        gpiod_chip_close(chip);
        return 1;
    }

    // --- Allocate settings and request config ---
    settings = gpiod_line_settings_new();
    req_cfg = gpiod_request_config_new();
    if (!settings || !req_cfg) {
        fprintf(stderr, "Failed to allocate gpiod settings.\n");
        goto cleanup;
    }

    // --- Send start signal ---
    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(settings, 1);

    request = gpiod_line_request(line, req_cfg, settings, 0); // 4th argument = default_val
    if (!request) {
        perror("gpiod_line_request output");
        goto cleanup;
    }

    gpiod_line_request_set_value(request, 0, 0); // line 0, value 0
    usleep(18000); // 18ms low
    gpiod_line_request_set_value(request, 0, 1); // line 0, high
    usleep(40);

    gpiod_line_request_release(request);

    // --- Switch to input ---
    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_INPUT);
    request = gpiod_line_request(line, req_cfg, settings, 0);
    if (!request) {
        perror("gpiod_line_request input");
        goto cleanup;
    }

    // --- Read sensor data ---
    for (i = 0; i < MAX_TIMINGS; i++) {
        counter = 0;
        int current = gpiod_line_request_get_value(request, 0);
        while (current == last_state) {
            counter++;
            delay_us(1);
            current = gpiod_line_request_get_value(request, 0);
            if (counter == 255) break;
        }
        last_state = current;

        if (counter == 255) break;

        if ((i >= 4) && (i % 2 == 0)) {
            data[bit_index / 8] <<= 1;
            if (counter > 50)
                data[bit_index / 8] |= 1;
            bit_index++;
        }
    }

    // --- Validate and print results ---
    if (bit_index >= 40 &&
        data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF)) {
        float humidity = ((data[0] << 8) + data[1]) / 10.0;
        float temperature = (((data[2] & 0x7F) << 8) + data[3]) / 10.0;
        if (data[2] & 0x80) temperature = -temperature;

        printf("Humidity: %.1f %%\n", humidity);
        printf("Temperature: %.1f °C\n", temperature);
    } else {
        fprintf(stderr, "AM2303: bad reading or checksum error.\n");
    }

cleanup:
    if (request)
        gpiod_line_request_release(request);
    if (settings)
        gpiod_line_settings_free(settings);
    if (req_cfg)
        gpiod_request_config_free(req_cfg);
    if (chip)
        gpiod_chip_close(chip);

    return 0;
}

