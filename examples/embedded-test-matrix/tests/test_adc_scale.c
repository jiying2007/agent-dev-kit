#include "adc_scale.h"

#include <stdio.h>

static int expect_equal(const char *name, int expected, int actual) {
  if (expected != actual) {
    printf("FAIL %s expected=%d actual=%d\n", name, expected, actual);
    return 1;
  }
  printf("PASS %s expected=%d actual=%d\n", name, expected, actual);
  return 0;
}

int main(void) {
  int failures = 0;
  failures += expect_equal("zero", 0, adc_scale_mv(0, 3300, 4095));
  failures += expect_equal("full-scale", 3300, adc_scale_mv(4095, 3300, 4095));
  failures += expect_equal("invalid", -1, adc_scale_mv(-1, 3300, 4095));
  return failures == 0 ? 0 : 1;
}
