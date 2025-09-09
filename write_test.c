#include <stdio.h>


int main() {
	const char *json_string = "{\"test\":\"test\"}";

	FILE *fp = fopen("output.json", "w");
	if(fp == NULL) {
		perror("Error opening file");
		return 1;
	}

	fprintf(fp, "%s", json_string);

	fclose(fp);

	return 0;
}

