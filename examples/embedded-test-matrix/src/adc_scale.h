#ifndef ADK_ADC_SCALE_H
#define ADK_ADC_SCALE_H

/* C11 fixture: int <= 32 bits and int64_t are required by the implementation.
 * Return -1 for raw < 0 or nonpositive reference/max; clamp raw above max.
 * Valid results are truncated millivolts in [0, reference_mv]. */
int adc_scale_mv(int raw, int reference_mv, int max_count);

#endif
