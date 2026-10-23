/* ESP32-S3 port: int8 dot products on the PIE vector unit (16 int8 MACs per instruction), using
 * ESP-NN dot kernel (esp_nn_dot_s8_esp32s3.S, Apache-2.0, Espressif Systems). Replaces the
 * portable sparrow_dot_s8 in sparrow.c (SPARROW_DOT_PORT) when SPARROW_INT8_ACT=1. */
#include "sparrow.h"

#if SPARROW_INT8_ACT
int32_t esp_nn_dot_s8_unaligned_esp32s3(const int8_t *a_aligned, const int8_t *b, int32_t len_div16);

int32_t sparrow_dot_s8(const int8_t *a, const int8_t *b, uint32_t n) {
    /* the kernel wants its first operand 16-byte aligned; the dot product is symmetric */
    if ((n & 15u) == 0 && n) {
        if ((((uintptr_t)b) & 15u) == 0) return esp_nn_dot_s8_unaligned_esp32s3(b, a, (int32_t)(n >> 4));
        if ((((uintptr_t)a) & 15u) == 0) return esp_nn_dot_s8_unaligned_esp32s3(a, b, (int32_t)(n >> 4));
    }
    int32_t acc = 0;
    for (uint32_t i = 0; i < n; i++) acc += (int32_t)a[i] * (int32_t)b[i];
    return acc;
}
#endif
