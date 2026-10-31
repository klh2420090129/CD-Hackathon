// Sample 4: Boolean expressions with short-circuit evaluation
int p;
int q;
int r;
p = 5;
q = 12;
r = 0;

if ((p < 10 && q > 5) || r != 0) {
    r = 1;
} else {
    r = 2;
}
