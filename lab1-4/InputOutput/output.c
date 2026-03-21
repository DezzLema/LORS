#include <stdio.h>

int main() {
    int i, sum;
    i = 1;
    sum = 0;
    do {
        sum = sum + i;
        i++;
    } while (i > 10);
    return 0;
}