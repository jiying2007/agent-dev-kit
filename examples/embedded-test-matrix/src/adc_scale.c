#include "adc_scale.h"

#include <limits.h>
#include <stdint.h>

_Static_assert(INT_MAX <= INT32_MAX, "adc_scale_mv requires int with at most 31 value bits");

int adc_scale_mv(int raw, int reference_mv, int max_count) {
  if (raw < 0 || reference_mv <= 0 || max_count <= 0) {
    return -1;
  }
  if (raw > max_count) {
    raw = max_count;
  }
  return (int)((int64_t)raw * reference_mv / max_count);
}
