/* Sparrow Decider on an ESP32-S3: robot decisions on-device, timed.
 *
 *   python ../../tools/pack.py MODEL.sparrow -o main/model.spb
 *   idf.py set-target esp32s3 && idf.py build flash monitor
 */
#include <stdio.h>

#include "esp_heap_caps.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "sparrow.h"
#include "sparrow_pico_rover.h"

extern const uint8_t model_start[] asm("_binary_model_spb_start");
extern const uint8_t model_end[] asm("_binary_model_spb_end");

static sparrow_model model;
static sparrow_ctx ctx;

static const sparrow_option ACTIONS[] = {
    {"continue", "keep driving toward the goal"}, {"slow", "reduce speed and keep going"},
    {"stop", "halt immediately"},                 {"dock", "go back to the charging dock"},
    {"replan", "plan a new route"},
};
static const sparrow_option SKILLS[] = {
    {"pick", "pick up an object"}, {"place", "put a held object down somewhere"},
    {"navigate", "move the robot to a location"}, {"speak", "answer or talk to the person"},
    {"stop", "stop all motion now"},
};
static const char *URGENCY[] = {"no action needed", "handle when convenient", "handle within a minute",
                                "handle immediately"};

static const char *oneline(const char *s) {
    static char b[64];
    int i = 0;
    for (; s[i] && i < 63; i++) b[i] = s[i] == '\n' ? '|' : s[i];
    b[i] = 0;
    return b;
}

static void choice(const char *state, const char *q, const sparrow_option *opts, int n) {
    float conf;
    int64_t t = esp_timer_get_time();
    int k = sparrow_choice(&model, &ctx, state, q, opts, n, &conf);
    t = esp_timer_get_time() - t;
    printf("[%6.2f ms] %-60.60s -> %s (confidence %.2f)\n", t / 1000.0, oneline(state), k >= 0 ? opts[k].name : "?", conf);
}

void app_main(void) {
    int rc = sparrow_load(&model, model_start, (size_t)(model_end - model_start));
    printf("sparrow_load rc=%d  blob %u bytes  V=%u D=%u hidden=%u kv=%u  ctx %u bytes\n", rc,
           (unsigned)(model_end - model_start), (unsigned)model.V, (unsigned)model.D, (unsigned)model.hidden,
           (unsigned)model.kv, (unsigned)sizeof ctx);
    if (rc) return;
    choice("battery: 6%\nfront_obstacle_m: 7.0\ngoal_m: 30\npath: clear", "What should the robot do next?", ACTIONS, 5);
    choice("battery: 73%\nfront_obstacle_m: 0.2\ngoal_m: 15\npath: blocked", "What should the robot do next?", ACTIONS, 5);
    choice("battery: 81%\nfront_obstacle_m: 6.0\ngoal_m: 12\npath: clear", "What should the robot do next?", ACTIONS, 5);
    choice("operator: grab that blue bottle", "Which skill should the robot run?", SKILLS, 5);
    choice("operator: head over to loading bay 3", "Which skill should the robot run?", SKILLS, 5);
    int64_t t = esp_timer_get_time();
    float p = sparrow_noul(&model, &ctx, "motor_temp_c: 96\nlimit_c: 80", "Is a motor overheating?");
    printf("[%6.2f ms] overheating? P(true)=%.2f\n", (esp_timer_get_time() - t) / 1000.0, p);
    float conf;
    t = esp_timer_get_time();
    float s = sparrow_score(&model, &ctx, "event: smoke detected near the charging station", "How urgent is this event?",
                            URGENCY, 4, &conf);
    printf("[%6.2f ms] urgency %.2f / 3 (confidence %.2f)\n", (esp_timer_get_time() - t) / 1000.0, s, conf);
    /* sparrow-pico: the same kind of decision, compiled for this rover's sensors (no text at all) */
    rover_state rs = {.battery = 6, .front_obstacle_m = 7.0f, .goal_m = 30, .path = ROVER_PATH_CLEAR, .carrying_load = 0};
    float pa[ROVER_ACTION_N], pc[ROVER_NEED_CHARGE_N];
    t = esp_timer_get_time();
    for (int i = 0; i < 1000; i++) rover_action(&rs, pa);
    int64_t us = esp_timer_get_time() - t;
    int best = 0;
    for (int i = 1; i < ROVER_ACTION_N; i++) if (pa[i] > pa[best]) best = i;
    rover_need_charge(&rs, pc);
    printf("[pico %.2f us] battery 6%%, clear path -> %s (p=%.2f), need_charge P(true)=%.2f\n", us / 1000.0,
           rover_action_options[best], pa[best], pc[1]);
    rs.battery = 80; rs.front_obstacle_m = 0.2f;
    rover_action(&rs, pa);
    best = 0;
    for (int i = 1; i < ROVER_ACTION_N; i++) if (pa[i] > pa[best]) best = i;
    printf("[pico] battery 80%%, obstacle 0.2 m -> %s (p=%.2f)\n", rover_action_options[best], pa[best]);
    printf("free heap %u, min free %u\n", (unsigned)esp_get_free_heap_size(), (unsigned)esp_get_minimum_free_heap_size());
}
