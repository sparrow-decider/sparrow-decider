/* sparrow-pico on-device timing: probabilities vs logits vs argmax, over varied rover states.
 * Driven by bench/esp32/pico_run.py. */
#include <stdio.h>
#include "esp_cpu.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sparrow_pico_rover.h"

#define N 10000
static rover_state S[256];

static uint32_t rng = 12345;
static float frand(float lo, float hi) { rng = rng * 1664525u + 1013904223u; return lo + (hi - lo) * (rng >> 8) / 16777216.0f; }

void app_main(void) {
    vTaskDelay(pdMS_TO_TICKS(3000));
    for (int i = 0; i < 256; i++) {
        S[i].battery = frand(0, 100);
        S[i].front_obstacle_m = frand(0, 8);
        S[i].goal_m = frand(0, 60);
        S[i].path = (rover_path_t)(i % 4);
        S[i].carrying_load = i & 1;
    }
    float p[ROVER_ACTION_N];
    volatile int sink = 0;
    int agree = 0;
    for (int i = 0; i < 256; i++) {  /* argmax must pick what the probabilities pick */
        rover_action(&S[i], p);
        int b = 0;
        for (int k = 1; k < ROVER_ACTION_N; k++) if (p[k] > p[b]) b = k;
        agree += (b == rover_action_argmax(&S[i]));
    }
    uint32_t c0 = esp_cpu_get_cycle_count();
    for (int i = 0; i < N; i++) { rover_action(&S[i & 255], p); sink += p[0] > 0.5f; }
    uint32_t c1 = esp_cpu_get_cycle_count();
    for (int i = 0; i < N; i++) { rover_action_logits(&S[i & 255], p); sink += p[0] > 0; }
    uint32_t c2 = esp_cpu_get_cycle_count();
    for (int i = 0; i < N; i++) sink += rover_action_argmax(&S[i & 255]);
    uint32_t c3 = esp_cpu_get_cycle_count();
    float mhz = CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ;
    printf("PICO_RESULT probs_cycles=%lu logits_cycles=%lu argmax_cycles=%lu probs_us=%.3f logits_us=%.3f argmax_us=%.3f agree=%d/256 sink=%d\n",
           (unsigned long)((c1 - c0) / N), (unsigned long)((c2 - c1) / N), (unsigned long)((c3 - c2) / N),
           (c1 - c0) / N / mhz, (c2 - c1) / N / mhz, (c3 - c2) / N / mhz, agree, sink);
}
