/* On-device benchmark: runs the cases in cases.h through the packed model, prints one line per
 * case and a summary. Driven by bench/esp32/run.py. */
#include <stdio.h>
#include <string.h>

#include "esp_cpu.h"
#include "esp_heap_caps.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sparrow.h"
#include "cases.h"
#include "sparrow_pico_rover.h"

extern const uint8_t model_start[] asm("_binary_model_spb_start");
extern const uint8_t model_end[] asm("_binary_model_spb_end");

#ifdef SPARROW_PROFILE
uint32_t sparrow_cycles(void) { return esp_cpu_get_cycle_count(); }
extern uint32_t sparrow_prof[6];
#endif

static sparrow_model model;
static sparrow_ctx ctx;

void app_main(void) {
    vTaskDelay(pdMS_TO_TICKS(4000)); /* let the host open the port */
    const uint8_t *blob = model_start;
    size_t blob_len = (size_t)(model_end - model_start);
#ifdef SPARROW_BLOB_PSRAM
    uint8_t *copy = heap_caps_aligned_alloc(16, blob_len, MALLOC_CAP_SPIRAM);
    if (copy) {
        memcpy(copy, model_start, blob_len);
        blob = copy;
    }
    printf("blob copied to PSRAM: %s\n", copy ? "yes" : "no");
#endif
    int64_t t0 = esp_timer_get_time();
    int rc = sparrow_load(&model, blob, blob_len);
    int64_t load_us = esp_timer_get_time() - t0;
    printf("SPARROW_BEGIN rc=%d blob=%u V=%u D=%u hidden=%u kv=%u int8=%d ctx=%u load_us=%lld cpu_mhz=%d\n", rc,
           (unsigned)(model_end - model_start), (unsigned)model.V, (unsigned)model.D, (unsigned)model.hidden,
           (unsigned)model.kv, SPARROW_INT8_ACT, (unsigned)sizeof ctx, load_us, CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ);
    if (rc) return;
#ifdef SPARROW_MLP_INTERNAL
    size_t mb = sparrow_mlp_bytes(&model);
    void *mlp = heap_caps_aligned_alloc(16, mb, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    printf("MLP to internal RAM: %u bytes %s\n", (unsigned)mb, mlp && sparrow_move_mlp(&model, mlp, mb) == SPARROW_OK ? "ok" : "FAILED");
#endif
    for (int pass = 0; pass < 2; pass++) { /* pass 0 warms the flash cache; pass 1 is reported */
#ifdef SPARROW_PROFILE
        memset(sparrow_prof, 0, sizeof sparrow_prof);
#endif
        for (int i = 0; i < N_CASES; i++) {
            const bench_case *c = &CASES[i];
            float p[SPARROW_MAX_OPTIONS];
            uint32_t cy = esp_cpu_get_cycle_count();
            int64_t t = esp_timer_get_time();
            sparrow_probs(&model, &ctx, c->state, c->question, (sparrow_kind)c->kind, c->opts, c->n, p);
            int64_t us = esp_timer_get_time() - t;
            uint32_t cycles = esp_cpu_get_cycle_count() - cy;
            int pred = 0;
            for (int k = 1; k < c->n; k++)
                if (p[k] > p[pred]) pred = k;
            if (c->kind == SPARROW_SCORE) {
                float ev = 0;
                for (int k = 0; k < c->n; k++) ev += k * p[k];
                pred = (int)(ev + 0.5f);
            }
            if (pass == 1) {
                printf("C %d %d %d %lld %lu", i, pred, c->expected, us, (unsigned long)cycles);
                for (int k = 0; k < c->n; k++) printf(" %.5f", p[k]);
                printf("\n");
            }
            vTaskDelay(1);
        }
    }
#ifdef SPARROW_PROFILE
    printf("PROF pool_state_q=%lu pool_options=%lu kv_pairs=%lu features=%lu layer1=%lu layer2=%lu\n",
           (unsigned long)sparrow_prof[0], (unsigned long)sparrow_prof[1], (unsigned long)sparrow_prof[2],
           (unsigned long)sparrow_prof[3], (unsigned long)sparrow_prof[4], (unsigned long)sparrow_prof[5]);
#endif
    /* sparrow-pico: same rover decision 10000 times */
    rover_state rs = {.battery = 6, .front_obstacle_m = 7.0f, .goal_m = 30, .path = ROVER_PATH_CLEAR};
    float pa[ROVER_ACTION_N];
    int64_t t = esp_timer_get_time();
    uint32_t cy = esp_cpu_get_cycle_count();
    for (int i = 0; i < 10000; i++) {
        rs.battery = (float)(i % 100);
        rover_action(&rs, pa);
    }
    uint32_t cycles = esp_cpu_get_cycle_count() - cy;
    printf("PICO us_per_call=%.3f cycles_per_call=%lu\n", (esp_timer_get_time() - t) / 10000.0,
           (unsigned long)(cycles / 10000));
    printf("SPARROW_END heap_free=%u heap_min=%u stack_hwm=%u\n", (unsigned)esp_get_free_heap_size(),
           (unsigned)esp_get_minimum_free_heap_size(), (unsigned)uxTaskGetStackHighWaterMark(NULL));
}
