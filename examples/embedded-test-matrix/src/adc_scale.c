#include "adc_scale.h"

int adc_scale_mv(int raw, int reference_mv, int max_count) {
  if (raw < 0 || reference_mv <= 0 || max_count <= 0) {
    return -1;
  }
  if (raw > max_count) {
    raw = max_count;
  }
  return (raw * reference_mv) / max_count;
}
