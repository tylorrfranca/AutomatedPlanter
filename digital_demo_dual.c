#include <gpiod.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define CHIPNAME "/dev/gpiochip0"  // For Raspberry Pi 3/4/5, GPIOs are on chip0

// Function to read a GPIO line value (0 or 1)
int read_gpio_value(struct gpiod_chip *chip, unsigned int line_num) {
    struct gpiod_line *line;
    int value;

    // Request the line for input
    line = gpiod_chip_get_line(chip, line_num);
    if (!line) {
        perror("Failed to get line");
        return -1;
    }

    if (gpiod_line_request_input(line, "gpio_reader") < 0) {
        perror("Failed to request line as input");
        gpiod_line_release(line);
        return -1;
    }

    // Read the line value
    value = gpiod_line_get_value(line);
    if (value < 0) {
        perror("Failed to read line value");
        gpiod_line_release(line);
        return -1;
    }

    // Clean up
    gpiod_line_release(line);
    return value;
}

int main(void) {
    struct gpiod_chip *chip;
    int val17, val27;

    // Open the GPIO chip
    chip = gpiod_chip_open(CHIPNAME);
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    printf("Reading GPIO17 and GPIO27 every second...\n");
    printf("Press Ctrl+C to stop.\n");

    while (1) {
        val17 = read_gpio_value(chip, 17);
        val27 = read_gpio_value(chip, 27);

        if (val17 < 0 || val27 < 0) {
            fprintf(stderr, "Error reading GPIO line(s)\n");
            break;
        }

        printf("GPIO17 = %d\tGPIO27 = %d\n", val17, val27);
        sleep(1);
    }

    gpiod_chip_close(chip);
    return 0;
}

