# Makefile for Automated Planter C Implementation
# Uses libgpiod for GPIO control

CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g
LDFLAGS = -lgpiod -ljson-c -lcurl -lpthread -lm

# Source files
HARDWARE_SOURCES = hardware_drivers.c
CORE_SOURCES = raspberry_pi_core.c
MAIN_SOURCES = main.c
DEMO_SOURCES = demo_milestones.c

# Object files
HARDWARE_OBJECTS = $(HARDWARE_SOURCES:.c=.o)
CORE_OBJECTS = $(CORE_SOURCES:.c=.o)
MAIN_OBJECTS = $(MAIN_SOURCES:.c=.o)
DEMO_OBJECTS = $(DEMO_SOURCES:.c=.o)

# Executables
MAIN_TARGET = automated_planter
DEMO_TARGET = demo_milestones

# Default target
all: $(MAIN_TARGET) $(DEMO_TARGET)

# Main application
$(MAIN_TARGET): $(MAIN_OBJECTS) $(CORE_OBJECTS) $(HARDWARE_OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Demo application
$(DEMO_TARGET): $(DEMO_OBJECTS) $(CORE_OBJECTS) $(HARDWARE_OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Object file compilation
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f *.o $(MAIN_TARGET) $(DEMO_TARGET)

# Install dependencies (Ubuntu/Debian)
install-deps:
	sudo apt-get update
	sudo apt-get install -y \
		libgpiod-dev \
		libjson-c-dev \
		libcurl4-openssl-dev \
		pkg-config \
		gcc \
		make

# Install dependencies (Raspberry Pi OS)
install-deps-pi:
	sudo apt-get update
	sudo apt-get install -y \
		libgpiod-dev \
		libjson-c-dev \
		libcurl4-openssl-dev \
		pkg-config \
		gcc \
		make

# Check dependencies
check-deps:
	@pkg-config --exists libgpiod && echo "✅ libgpiod found" || echo "❌ libgpiod not found"
	@pkg-config --exists json-c && echo "✅ json-c found" || echo "❌ json-c not found"
	@pkg-config --exists libcurl && echo "✅ libcurl found" || echo "❌ libcurl not found"

# Run main application in simulation mode
run-sim: $(MAIN_TARGET)
	./$(MAIN_TARGET) --simulation

# Run main application with real hardware
run-real: $(MAIN_TARGET)
	./$(MAIN_TARGET)

# Run demo in simulation mode
demo-sim: $(DEMO_TARGET)
	./$(DEMO_TARGET) 1

# Run all demos
demo-all: $(DEMO_TARGET)
	./$(DEMO_TARGET) all

# Show system status
status: $(MAIN_TARGET)
	./$(MAIN_TARGET) status

# Start monitoring
monitor: $(MAIN_TARGET)
	./$(MAIN_TARGET) monitor

# Help
help:
	@echo "Available targets:"
	@echo "  all          - Build all executables"
	@echo "  clean        - Remove build artifacts"
	@echo "  install-deps - Install dependencies (Ubuntu/Debian)"
	@echo "  install-deps-pi - Install dependencies (Raspberry Pi OS)"
	@echo "  check-deps   - Check if dependencies are installed"
	@echo "  run-sim      - Run main application in simulation mode"
	@echo "  run-real     - Run main application with real hardware"
	@echo "  demo-sim     - Run demo 1 in simulation mode"
	@echo "  demo-all     - Run all demos"
	@echo "  status       - Show system status"
	@echo "  monitor      - Start monitoring loop"
	@echo "  help         - Show this help"

# Debug build
debug: CFLAGS += -DDEBUG -g3
debug: clean all

# Release build
release: CFLAGS += -DNDEBUG -O3
release: clean all

# Cross-compile for Raspberry Pi (if cross-compiler is available)
cross-compile: CC = arm-linux-gnueabihf-gcc
cross-compile: clean all

# Package for distribution
package: release
	mkdir -p automated_planter_c
	cp $(MAIN_TARGET) $(DEMO_TARGET) automated_planter_c/
	cp *.h automated_planter_c/
	cp README.md automated_planter_c/
	tar -czf automated_planter_c.tar.gz automated_planter_c/
	rm -rf automated_planter_c/

# Test compilation without linking
test-compile:
	$(CC) $(CFLAGS) -c hardware_drivers.c
	$(CC) $(CFLAGS) -c raspberry_pi_core.c
	$(CC) $(CFLAGS) -c main.c
	$(CC) $(CFLAGS) -c demo_milestones.c
	@echo "✅ All files compile successfully"

# Format code (requires clang-format)
format:
	clang-format -i *.c *.h

# Static analysis (requires cppcheck)
analyze:
	cppcheck --enable=all --std=c99 *.c

.PHONY: all clean install-deps install-deps-pi check-deps run-sim run-real demo-sim demo-all status monitor help debug release cross-compile package test-compile format analyze
