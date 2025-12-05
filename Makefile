sensor_demo: sensor_demo.c
	gcc sensor_demo.c -o build/sensor_demo -lgpiod -lm

sensor_write_json: sensor_write_json.c
	gcc sensor_write_json.c -o build/sensor_write_json -lgpiod -lm

pump_on: pump_on.c
	gcc pump_on.c -o build/pump_on -lgpiod

pump_off: pump_off.c
	gcc pump_off.c -o build/pump_off -lgpiod

pump: pump_on pump_off

clean:
	rm -f build/*
