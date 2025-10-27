#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#define ADS1115_ADDRESS 0x48   // Default if ADDR pin is tied to GND

// ADS1115 Register addresses
#define REG_CONVERSION 0x00
#define REG_CONFIG     0x01

// ADS1115 Configuration bits
#define CONFIG_OS_SINGLE     0x8000  // Start single conversion
#define CONFIG_MUX_AIN0_GND  0x4000  // Measure AIN0 vs GND
#define CONFIG_PGA_4_096V    0x0200  // ±4.096V range
#define CONFIG_MODE_SINGLE   0x0100  // Single-shot mode
#define CONFIG_DR_128SPS     0x0080  // 128 samples per second
#define CONFIG_COMP_QUE_DISABLE 0x0003 // Disable comparator

int main(void) {
    const char *dev = "/dev/i2c-1";
    int fd;

    if ((fd = open(dev, O_RDWR)) < 0) {
        perror("Failed to open I2C bus");
        return 1;
    }

    if (ioctl(fd, I2C_SLAVE, ADS1115_ADDRESS) < 0) {
        perror("Failed to acquire bus access or talk to slave");
        close(fd);
        return 1;
    }

    while(1) {
	    // Build config word
	    uint16_t config = CONFIG_OS_SINGLE     |
			      CONFIG_MUX_AIN0_GND  |
			      CONFIG_PGA_4_096V    |
			      CONFIG_MODE_SINGLE   |
			      CONFIG_DR_128SPS     |
			      CONFIG_COMP_QUE_DISABLE;

	    // Write config to ADS1115
	    uint8_t writeBuf[3];
	    writeBuf[0] = REG_CONFIG;
	    writeBuf[1] = (config >> 8) & 0xFF;   // MSB
	    writeBuf[2] = config & 0xFF;          // LSB
	    if (write(fd, writeBuf, 3) != 3) {
		perror("Failed to write config");
		close(fd);
		break;
	    }

	    // Wait for conversion (depends on data rate; ~8ms for 128 SPS)
	    usleep(8000);

	    // Set pointer register to conversion register
	    uint8_t reg[1] = { REG_CONVERSION };
	    if (write(fd, reg, 1) != 1) {
		perror("Failed to set pointer register");
		close(fd);
		break;
	    }

	    // Read conversion result (2 bytes)
	    uint8_t readBuf[2];
	    if (read(fd, readBuf, 2) != 2) {
		perror("Failed to read conversion");
		close(fd);
		break;
	    }

	    // Combine bytes into 16-bit value
	    int16_t raw = (readBuf[0] << 8) | readBuf[1];

	    // Convert raw value to voltage (using ±4.096 V range)
	    float voltage = raw * (4.096 / 32768.0);
	    printf("Raw: %d\tVoltage: %.4f V\n", raw, voltage);
	    sleep(1);
    }

    close(fd);
    return 0;
}
