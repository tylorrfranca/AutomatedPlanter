#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

// ADS1115 I2C Address
#define ADS1115_ADDRESS 0x48

// ADS1115 Registers
#define ADS1115_REG_CONVERSION   0x00
#define ADS1115_REG_CONFIG       0x01

// Configuration Register Bits
#define ADS1115_CONFIG_OS_SINGLE    0x8000  // Start single conversion
#define ADS1115_CONFIG_MUX_AIN0     0x4000  // AINP = AIN0, AINN = GND
#define ADS1115_CONFIG_MUX_AIN1     0x5000  // AINP = AIN1, AINN = GND
#define ADS1115_CONFIG_PGA_4_096V   0x0200  // +/-4.096V range
#define ADS1115_CONFIG_MODE_SINGLE  0x0100  // Single-shot mode
#define ADS1115_CONFIG_DR_128SPS    0x0080  // 128 samples per second
#define ADS1115_CONFIG_COMP_QUE_DIS 0x0003  // Disable comparator

// Function prototypes
int ads1115_init(const char *i2c_device);
int ads1115_write_register(int fd, uint8_t reg, uint16_t value);
int ads1115_read_register(int fd, uint8_t reg, uint16_t *value);
int ads1115_read_adc(int fd, uint8_t channel);
float ads1115_convert_to_voltage(int16_t raw_value);

int main(void) {
    int fd;
    int adc0, adc1;
    float voltage0, voltage1;

    // Initialize I2C connection
    fd = ads1115_init("/dev/i2c-1");
    if (fd < 0) {
        fprintf(stderr, "Failed to initialize ADS1115\n");
        return 1;
    }

    printf("ADS1115 ADC Reader\n");
    printf("Reading A0 and A1...\n");
    printf("Press Ctrl+C to exit.\n\n");

    while (1) {
        // Read A0
        adc0 = ads1115_read_adc(fd, 0);
        if (adc0 < 0) {
            fprintf(stderr, "Failed to read A0\n");
            continue;
        }
        voltage0 = ads1115_convert_to_voltage(adc0);

        // Read A1
        adc1 = ads1115_read_adc(fd, 1);
        if (adc1 < 0) {
            fprintf(stderr, "Failed to read A1\n");
            continue;
        }
        voltage1 = ads1115_convert_to_voltage(adc1);

        // Display results
        printf("A0: %6d (%.4f V)  |  A1: %6d (%.4f V)\n", 
               adc0, voltage0, adc1, voltage1);

        sleep(1);
    }

    close(fd);
    return 0;
}

int ads1115_init(const char *i2c_device) {
    int fd;

    // Open I2C device
    fd = open(i2c_device, O_RDWR);
    if (fd < 0) {
        perror("Failed to open I2C device");
        return -1;
    }

    // Set I2C slave address
    if (ioctl(fd, I2C_SLAVE, ADS1115_ADDRESS) < 0) {
        perror("Failed to set I2C slave address");
        close(fd);
        return -1;
    }

    return fd;
}

int ads1115_write_register(int fd, uint8_t reg, uint16_t value) {
    uint8_t buffer[3];
    
    buffer[0] = reg;
    buffer[1] = (value >> 8) & 0xFF;  // MSB
    buffer[2] = value & 0xFF;         // LSB

    if (write(fd, buffer, 3) != 3) {
        perror("Failed to write to I2C device");
        return -1;
    }

    return 0;
}

int ads1115_read_register(int fd, uint8_t reg, uint16_t *value) {
    uint8_t buffer[2];

    // Write register address
    if (write(fd, &reg, 1) != 1) {
        perror("Failed to write register address");
        return -1;
    }

    // Read 2 bytes
    if (read(fd, buffer, 2) != 2) {
        perror("Failed to read from I2C device");
        return -1;
    }

    *value = (buffer[0] << 8) | buffer[1];
    return 0;
}

int ads1115_read_adc(int fd, uint8_t channel) {
    uint16_t config;
    uint16_t conversion;
    int retries = 10;

    // Configure for the specified channel
    config = ADS1115_CONFIG_OS_SINGLE |
             ADS1115_CONFIG_MODE_SINGLE |
             ADS1115_CONFIG_PGA_4_096V |
             ADS1115_CONFIG_DR_128SPS |
             ADS1115_CONFIG_COMP_QUE_DIS;

    // Set channel
    if (channel == 0) {
        config |= ADS1115_CONFIG_MUX_AIN0;
    } else if (channel == 1) {
        config |= ADS1115_CONFIG_MUX_AIN1;
    } else {
        fprintf(stderr, "Invalid channel: %d\n", channel);
        return -1;
    }

    // Start conversion
    if (ads1115_write_register(fd, ADS1115_REG_CONFIG, config) < 0) {
        return -1;
    }

    // Wait for conversion to complete
    usleep(10000);  // 10ms (8ms for 128 SPS + margin)

    // Read conversion result
    if (ads1115_read_register(fd, ADS1115_REG_CONVERSION, &conversion) < 0) {
        return -1;
    }

    return (int16_t)conversion;
}

float ads1115_convert_to_voltage(int16_t raw_value) {
    // For +/-4.096V range, LSB = 0.125mV
    // Full scale = 32767 = 4.096V
    return (raw_value * 4.096f) / 32768.0f;
}
