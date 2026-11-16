#include "adc_scale.h"

#include <limits.h>
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
  /* Endpoint and clamping invariants; do not duplicate the scaling formula. */
  failures += expect_equal("maximum-int-full-scale", INT_MAX,
                           adc_scale_mv(INT_MAX, INT_MAX, INT_MAX));
  failures += expect_equal("maximum-int-clamped", INT_MAX,
                           adc_scale_mv(INT_MAX, INT_MAX, INT_MAX - 1));
  failures += expect_equal("maximum-int-zero", 0,
                           adc_scale_mv(0, INT_MAX, INT_MAX));
  failures += expect_equal("clamped", 3300, adc_scale_mv(4096, 3300, 4095));
  failures += expect_equal("invalid-minimum", -1, adc_scale_mv(INT_MIN, 3300, 4095));
  failures += expect_equal("zero-reference", -1, adc_scale_mv(1, 0, 4095));
  failures += expect_equal("negative-reference", -1, adc_scale_mv(1, -1, 4095));
  failures += expect_equal("zero-maximum", -1, adc_scale_mv(1, 3300, 0));
  failures += expect_equal("negative-maximum", -1, adc_scale_mv(1, 3300, -1));
#if INT_MAX >= 16777216
  failures += expect_equal("24-bit-full-scale", 3300,
                           adc_scale_mv(16777215, 3300, 16777215));
  failures += expect_equal("24-bit-clamped", 3300,
                           adc_scale_mv(16777216, 3300, 16777215));
#else
  puts("SKIP 24-bit cases: int cannot represent these inputs");
#endif
  return failures == 0 ? 0 : 1;
}
