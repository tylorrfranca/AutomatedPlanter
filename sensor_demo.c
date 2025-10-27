#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <gpiod.h>
#include <math.h>

// I2C Addresses
#define ADS1115_ADDRESS 0x48
#define BME280_ADDRESS 0x76  // Change to 0x77 if needed

// GPIO Configuration
#define GPIO_CHIP "/dev/gpiochip4"
#define GPIO_WATER_LEVEL 17

// ADS1115 Registers
#define ADS1115_REG_CONVERSION   0x00
#define ADS1115_REG_CONFIG       0x01

// ADS1115 Configuration
#define ADS1115_CONFIG_OS_SINGLE    0x8000
#define ADS1115_CONFIG_MUX_AIN0     0x4000
#define ADS1115_CONFIG_MUX_AIN1     0x5000
#define ADS1115_CONFIG_PGA_4_096V   0x0200
#define ADS1115_CONFIG_MODE_SINGLE  0x0100
#define ADS1115_CONFIG_DR_128SPS    0x0080
#define ADS1115_CONFIG_COMP_QUE_DIS 0x0003

// BME280 Registers
#define BME280_REG_CTRL_HUM   0xF2
#define BME280_REG_CTRL_MEAS  0xF4
#define BME280_REG_CONFIG     0xF5
#define BME280_REG_DATA       0xF7
#define BME280_REG_CALIB_00   0x88
#define BME280_REG_CALIB_26   0xE1

// BME280 Calibration Data
typedef struct {
    uint16_t dig_T1;
    int16_t  dig_T2, dig_T3;
    uint16_t dig_P1;
    int16_t  dig_P2, dig_P3, dig_P4, dig_P5, dig_P6, dig_P7, dig_P8, dig_P9;
    uint8_t  dig_H1, dig_H3;
    int16_t  dig_H2, dig_H4, dig_H5;
    int8_t   dig_H6;
    int32_t  t_fine;
} bme280_calib_data;

// GPIO Context
typedef struct {
    struct gpiod_chip *chip;
    struct gpiod_line_request *request;
    unsigned int offset;
} gpio_context;

// Function prototypes - I2C
int i2c_init(const char *device, uint8_t address);
int i2c_write_byte(int fd, uint8_t reg, uint8_t value);
int i2c_read_bytes(int fd, uint8_t reg, uint8_t *buffer, int length);

// Function prototypes - ADS1115
int ads1115_read_adc(int fd, uint8_t channel);
float ads1115_convert_to_voltage(int16_t raw_value);

// Function prototypes - BME280
int bme280_init(int fd, bme280_calib_data *calib);
int bme280_read_calibration(int fd, bme280_calib_data *calib);
int bme280_read_data(int fd, bme280_calib_data *calib, float *temp, float *humidity);

// Function prototypes - GPIO
int gpio_init(gpio_context *ctx, const char *chip_path, unsigned int offset);
int gpio_read(gpio_context *ctx);
void gpio_cleanup(gpio_context *ctx);

int main(void) {
    int fd_ads, fd_bme;
    int adc0, adc1;
    float voltage0, voltage1;
    float temperature, humidity;
    int water_level;
    bme280_calib_data calib;
    gpio_context gpio_ctx = {0};

    // Initialize ADS1115
    fd_ads = i2c_init("/dev/i2c-1", ADS1115_ADDRESS);
    if (fd_ads < 0) {
        fprintf(stderr, "Failed to initialize ADS1115\n");
        return 1;
    }

    // Initialize BME280
    fd_bme = i2c_init("/dev/i2c-1", BME280_ADDRESS);
    if (fd_bme < 0) {
        fprintf(stderr, "Failed to initialize BME280\n");
        close(fd_ads);
        return 1;
    }

    if (bme280_init(fd_bme, &calib) < 0) {
        fprintf(stderr, "Failed to configure BME280\n");
        close(fd_ads);
        close(fd_bme);
        return 1;
    }

    // Initialize GPIO
    if (gpio_init(&gpio_ctx, GPIO_CHIP, GPIO_WATER_LEVEL) < 0) {
        fprintf(stderr, "Failed to initialize GPIO\n");
        close(fd_ads);
        close(fd_bme);
        return 1;
    }

    printf("Sensor Reader - Press Ctrl+C to exit\n");
    printf("Soil Moisture (V) | Light (V) | Temp (°C) | Humidity (%%) | Water Level\n");
    printf("------------------+-----------+-----------+--------------+------------\n");

    while (1) {
        // Read ADS1115
        adc0 = ads1115_read_adc(fd_ads, 0);
        voltage0 = (adc0 >= 0) ? ads1115_convert_to_voltage(adc0) : 0.0f;

        adc1 = ads1115_read_adc(fd_ads, 1);
        voltage1 = (adc1 >= 0) ? ads1115_convert_to_voltage(adc1) : 0.0f;

        // Read BME280
        if (bme280_read_data(fd_bme, &calib, &temperature, &humidity) < 0) {
            temperature = 0.0f;
            humidity = 0.0f;
        }

        // Read GPIO
        water_level = gpio_read(&gpio_ctx);
        if (water_level < 0) {
            water_level = 0;
        }

        // Display all values on one line
        printf("      %6.3f      |  %6.3f   | %9.2f |    %8.1f  |      %d     \r", 
               voltage0, voltage1, temperature, humidity, water_level);
        fflush(stdout);

        sleep(1);
    }

    // Cleanup
    gpio_cleanup(&gpio_ctx);
    close(fd_ads);
    close(fd_bme);
    return 0;
}

// ============================================================================
// I2C Functions
// ============================================================================

int i2c_init(const char *device, uint8_t address) {
    int fd = open(device, O_RDWR);
    if (fd < 0) {
        perror("Failed to open I2C device");
        return -1;
    }

    if (ioctl(fd, I2C_SLAVE, address) < 0) {
        perror("Failed to set I2C slave address");
        close(fd);
        return -1;
    }

    return fd;
}

int i2c_write_byte(int fd, uint8_t reg, uint8_t value) {
    uint8_t buffer[2] = {reg, value};
    if (write(fd, buffer, 2) != 2) {
        return -1;
    }
    return 0;
}

int i2c_read_bytes(int fd, uint8_t reg, uint8_t *buffer, int length) {
    if (write(fd, &reg, 1) != 1) {
        return -1;
    }
    if (read(fd, buffer, length) != length) {
        return -1;
    }
    return 0;
}

// ============================================================================
// ADS1115 Functions
// ============================================================================

int ads1115_read_adc(int fd, uint8_t channel) {
    uint8_t buffer[3];
    uint16_t config = ADS1115_CONFIG_OS_SINGLE |
                      ADS1115_CONFIG_MODE_SINGLE |
                      ADS1115_CONFIG_PGA_4_096V |
                      ADS1115_CONFIG_DR_128SPS |
                      ADS1115_CONFIG_COMP_QUE_DIS;

    config |= (channel == 0) ? ADS1115_CONFIG_MUX_AIN0 : ADS1115_CONFIG_MUX_AIN1;

    buffer[0] = ADS1115_REG_CONFIG;
    buffer[1] = (config >> 8) & 0xFF;
    buffer[2] = config & 0xFF;

    if (write(fd, buffer, 3) != 3) return -1;

    usleep(10000);

    buffer[0] = ADS1115_REG_CONVERSION;
    if (write(fd, buffer, 1) != 1) return -1;
    if (read(fd, buffer, 2) != 2) return -1;

    return (int16_t)((buffer[0] << 8) | buffer[1]);
}

float ads1115_convert_to_voltage(int16_t raw_value) {
    return (raw_value * 4.096f) / 32768.0f;
}

// ============================================================================
// BME280 Functions
// ============================================================================

int bme280_init(int fd, bme280_calib_data *calib) {
    if (bme280_read_calibration(fd, calib) < 0) {
        return -1;
    }

    if (i2c_write_byte(fd, BME280_REG_CTRL_HUM, 0x01) < 0) return -1;
    if (i2c_write_byte(fd, BME280_REG_CTRL_MEAS, 0x27) < 0) return -1;
    if (i2c_write_byte(fd, BME280_REG_CONFIG, 0xA0) < 0) return -1;

    usleep(10000);
    return 0;
}

int bme280_read_calibration(int fd, bme280_calib_data *calib) {
    uint8_t calib_data[32];

    if (i2c_read_bytes(fd, BME280_REG_CALIB_00, calib_data, 26) < 0) return -1;

    calib->dig_T1 = (calib_data[1] << 8) | calib_data[0];
    calib->dig_T2 = (calib_data[3] << 8) | calib_data[2];
    calib->dig_T3 = (calib_data[5] << 8) | calib_data[4];
    calib->dig_P1 = (calib_data[7] << 8) | calib_data[6];
    calib->dig_P2 = (calib_data[9] << 8) | calib_data[8];
    calib->dig_P3 = (calib_data[11] << 8) | calib_data[10];
    calib->dig_P4 = (calib_data[13] << 8) | calib_data[12];
    calib->dig_P5 = (calib_data[15] << 8) | calib_data[14];
    calib->dig_P6 = (calib_data[17] << 8) | calib_data[16];
    calib->dig_P7 = (calib_data[19] << 8) | calib_data[18];
    calib->dig_P8 = (calib_data[21] << 8) | calib_data[20];
    calib->dig_P9 = (calib_data[23] << 8) | calib_data[22];
    calib->dig_H1 = calib_data[25];

    if (i2c_read_bytes(fd, BME280_REG_CALIB_26, calib_data, 7) < 0) return -1;

    calib->dig_H2 = (calib_data[1] << 8) | calib_data[0];
    calib->dig_H3 = calib_data[2];
    calib->dig_H4 = (calib_data[3] << 4) | (calib_data[4] & 0x0F);
    calib->dig_H5 = (calib_data[5] << 4) | (calib_data[4] >> 4);
    calib->dig_H6 = calib_data[6];

    return 0;
}

int bme280_read_data(int fd, bme280_calib_data *calib, float *temp, float *humidity) {
    uint8_t data[8];
    int32_t adc_T, adc_H;
    int32_t var1, var2;

    if (i2c_read_bytes(fd, BME280_REG_DATA, data, 8) < 0) return -1;

    adc_T = ((uint32_t)data[3] << 12) | ((uint32_t)data[4] << 4) | ((data[5] >> 4) & 0x0F);
    adc_H = ((uint32_t)data[6] << 8) | data[7];

    // Calculate temperature
    var1 = ((((adc_T >> 3) - ((int32_t)calib->dig_T1 << 1))) * ((int32_t)calib->dig_T2)) >> 11;
    var2 = (((((adc_T >> 4) - ((int32_t)calib->dig_T1)) * 
              ((adc_T >> 4) - ((int32_t)calib->dig_T1))) >> 12) * 
             ((int32_t)calib->dig_T3)) >> 14;
    calib->t_fine = var1 + var2;
    *temp = ((calib->t_fine * 5 + 128) >> 8) / 100.0f;

    // Calculate humidity
    var1 = calib->t_fine - ((int32_t)76800);
    var1 = (((((adc_H << 14) - (((int32_t)calib->dig_H4) << 20) - 
               (((int32_t)calib->dig_H5) * var1)) + ((int32_t)16384)) >> 15) * 
            (((((((var1 * ((int32_t)calib->dig_H6)) >> 10) * 
                 (((var1 * ((int32_t)calib->dig_H3)) >> 11) + ((int32_t)32768))) >> 10) + 
                ((int32_t)2097152)) * ((int32_t)calib->dig_H2) + 8192) >> 14));
    var1 = (var1 - (((((var1 >> 15) * (var1 >> 15)) >> 7) * 
                     ((int32_t)calib->dig_H1)) >> 4));
    var1 = (var1 < 0) ? 0 : var1;
    var1 = (var1 > 419430400) ? 419430400 : var1;
    *humidity = (var1 >> 12) / 1024.0f;

    return 0;
}

// ============================================================================
// GPIO Functions (libgpiod v2.2.1)
// ============================================================================

int gpio_init(gpio_context *ctx, const char *chip_path, unsigned int offset) {
    struct gpiod_line_settings *settings;
    struct gpiod_line_config *line_cfg;
    struct gpiod_request_config *req_cfg;
    int ret;

    ctx->offset = offset;

    // Open GPIO chip
    ctx->chip = gpiod_chip_open(chip_path);
    if (!ctx->chip) {
        perror("Failed to open GPIO chip");
        return -1;
    }

    // Create line settings for input
    settings = gpiod_line_settings_new();
    if (!settings) {
        fprintf(stderr, "Failed to create line settings\n");
        gpiod_chip_close(ctx->chip);
        return -1;
    }
    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_INPUT);

    // Create line configuration
    line_cfg = gpiod_line_config_new();
    if (!line_cfg) {
        fprintf(stderr, "Failed to create line config\n");
        gpiod_line_settings_free(settings);
        gpiod_chip_close(ctx->chip);
        return -1;
    }

    ret = gpiod_line_config_add_line_settings(line_cfg, &offset, 1, settings);
    if (ret) {
        fprintf(stderr, "Failed to add line settings\n");
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(ctx->chip);
        return -1;
    }

    // Create request configuration
    req_cfg = gpiod_request_config_new();
    if (!req_cfg) {
        fprintf(stderr, "Failed to create request config\n");
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(ctx->chip);
        return -1;
    }
    gpiod_request_config_set_consumer(req_cfg, "water-level");

    // Request the line
    ctx->request = gpiod_chip_request_lines(ctx->chip, req_cfg, line_cfg);
    if (!ctx->request) {
        perror("Failed to request GPIO line");
        gpiod_request_config_free(req_cfg);
        gpiod_line_config_free(line_cfg);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(ctx->chip);
        return -1;
    }

    // Cleanup temporary objects
    gpiod_request_config_free(req_cfg);
    gpiod_line_config_free(line_cfg);
    gpiod_line_settings_free(settings);

    return 0;
}

int gpio_read(gpio_context *ctx) {
    enum gpiod_line_value value;
    
    value = gpiod_line_request_get_value(ctx->request, ctx->offset);
    if (value < 0) {
        perror("Failed to read GPIO value");
        return -1;
    }

    return (int)value;
}

void gpio_cleanup(gpio_context *ctx) {
    if (ctx->request) {
        gpiod_line_request_release(ctx->request);
    }
    if (ctx->chip) {
        gpiod_chip_close(ctx->chip);
    }
}
