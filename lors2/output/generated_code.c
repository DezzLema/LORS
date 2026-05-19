int Test5(void) {
    int a;
    int b;
    int c;
    a = 1;
    b = 2;
    c = 10;
    do {
        a = (a * 2);
        b = ((a + b) * 2);
    } while (a > c);
}