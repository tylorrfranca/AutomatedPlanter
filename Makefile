sensor_demo: sensor_demo.c
	gcc sensor_demo.c -o build/sensor_demo -lgpiod -lm

sensor_write_json: sensor_write_json.c
	gcc sensor_write_json.c -o build/sensor_write_json -lgpiod -lm

clean:
	rm -f build/*
