#include "adc_scale.h"
#include <limits.h>
#include <stdio.h>

struct case_record { const char *name; int raw; int reference; int maximum; int expected; };

int main(void) {
    /* Expectations are literal full-scale/zero/clamping invariants, not the implementation formula. */
    const struct case_record cases[] = {
        {"12-bit-full-scale", 4095, 3300, 4095, 3300},
        {"24-bit-full-scale", 16777215, 3300, 16777215, 3300},
        {"int-max-full-scale", INT_MAX, 3300, INT_MAX, 3300},
        {"24-bit-clamped", 16777216, 3300, 16777215, 3300},
        {"zero", 0, 3300, 16777215, 0},
        {"invalid-reference", 1, 0, 4095, -1},
        {"invalid-maximum", 1, 3300, 0, -1},
    };
    int failures = 0;
    for (unsigned int i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
        const struct case_record *c = &cases[i];
        int actual = adc_scale_mv(c->raw, c->reference, c->maximum);
        printf("%s: expected=%d actual=%d\n", c->name, c->expected, actual);
        failures += actual != c->expected;
    }
    return failures ? 1 : 0;
}
