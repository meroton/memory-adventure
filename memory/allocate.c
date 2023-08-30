#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>

int
parse(char* str) {
    char* end;
    int res = strtol(str, &end, 10);

    return res;
}

int
main(int argc, char* argv[]) {
    if (argc <= 2) {
        fprintf(stderr, "Usage <allocate> <filepath> <number>\n");
        exit(1);
    }
    char* filepath = argv[1];
    int number = parse(argv[2]);
    int dur = 10;

    size_t size = number * 10 * 1048 * 1048;
    printf("allocating %d * 10 MB\n", number);
    printf("sleeping for %d seconds\n", dur);

    sleep(dur);
    int* memory = (int*) malloc(size);

    for (int i = 1; i < size; i *= 1048) {
        memory[i] = number * i;
    }

    FILE* fd = fopen(filepath, "w");
    fwrite(memory, size, 1, fd);
}
