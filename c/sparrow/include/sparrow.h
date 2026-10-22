/* Sparrow Decider C runtime: static decision models (sparrow-nano, sparrow-micro) on
 * microcontrollers and anything else with a C99 compiler. No malloc, no OS, no dependencies
 * beyond libm. The model is an SPB1 blob (c/tools/pack.py) that can live in flash.
 *
 *   sparrow_model m;  static sparrow_ctx ctx;
 *   sparrow_load(&m, blob, blob_len);
 *   sparrow_option opts[] = {{"continue", "keep going"}, {"dock", "go charge"}, {"stop", "halt"}};
 *   float p[3];
 *   sparrow_probs(&m, &ctx, "battery: 6%\nlidar_min_m: 4.0", "What next?", SPARROW_CHOICE, opts, 3, p);
 *
 * Unofficial community project. Not an AWS or Strands product.
 */
#ifndef SPARROW_H
#define SPARROW_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef SPARROW_MAX_DIM
#define SPARROW_MAX_DIM 256      /* embedding width D the context is sized for */
#endif
#ifndef SPARROW_MAX_HIDDEN
#define SPARROW_MAX_HIDDEN 384
#endif
#ifndef SPARROW_MAX_OPTIONS
#define SPARROW_MAX_OPTIONS 16
#endif
#define SPARROW_MAX_PAIRS 16     /* fixed by the model format: key-value pairs read per state */
#ifndef SPARROW_INT8_ACT
#define SPARROW_INT8_ACT 0       /* 1 = int8 activations in the MLP (int8 x int8 dot products) */
#endif

typedef enum { SPARROW_NOUL = 0, SPARROW_CHOICE = 1, SPARROW_SCORE = 2 } sparrow_kind;

typedef enum {
    SPARROW_OK = 0,
    SPARROW_ERR_FORMAT = -1,   /* not an SPB1 blob, or truncated */
    SPARROW_ERR_SIZE = -2,     /* model wider than SPARROW_MAX_DIM / SPARROW_MAX_HIDDEN */
    SPARROW_ERR_ARGS = -3      /* bad option count for the kind */
} sparrow_status;

typedef struct {
    const char *name;
    const char *desc; /* may be NULL */
} sparrow_option;

/* Views into the blob; nothing is copied. */
typedef struct {
    uint32_t kv, V, D, hidden, nf, max_len, unk_id;
    float temps[3];
    const char *strings;
    const uint32_t *str_off, *str_id;
    const int8_t *emb;
    const float *emb_scale, *kind, *g_w, *g_b, *tau;
    const int8_t *w0, *w2;
    const float *s0, *b0, *s2, *b2, *w4, *b4;
} sparrow_model;

/* Working memory for one call. Large-ish (tens of KB): make it static, not a stack local. */
typedef struct {
    float s[SPARROW_MAX_DIM], q[SPARROW_MAX_DIM], kv[SPARROW_MAX_DIM], omean[SPARROW_MAX_DIM];
    float o[SPARROW_MAX_OPTIONS][SPARROW_MAX_DIM];
    float pv[SPARROW_MAX_PAIRS][SPARROW_MAX_DIM], el[SPARROW_MAX_PAIRS][SPARROW_MAX_DIM];
    float kvo[SPARROW_MAX_DIM];
    float feat[10 * SPARROW_MAX_DIM];
    float h0[SPARROW_MAX_HIDDEN], h1[SPARROW_MAX_HIDDEN];
#if SPARROW_INT8_ACT
    int8_t fq[10 * SPARROW_MAX_DIM], hq[SPARROW_MAX_HIDDEN];
#endif
    char buf[512]; /* option text "name desc" and kv keys are pooled from here */
} sparrow_ctx;

sparrow_status sparrow_load(sparrow_model *m, const void *blob, size_t len);

/* Probabilities over the options, in the order given. For SPARROW_NOUL pass opts = NULL and
 * n_opts = 0 to use the default false/true options; probs[1] is P(true). */
sparrow_status sparrow_probs(const sparrow_model *m, sparrow_ctx *ctx, const char *state,
                             const char *instructions, sparrow_kind kind, const sparrow_option *opts,
                             int n_opts, float *probs);

/* Convenience wrappers matching the Strands Decider answer shapes. */
float sparrow_noul(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question);
int sparrow_choice(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question,
                   const sparrow_option *opts, int n_opts, float *confidence);
float sparrow_score(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question,
                    const char *const *levels, int n_levels, float *confidence);

#if SPARROW_INT8_ACT
int32_t sparrow_dot_s8(const int8_t *a, const int8_t *b, uint32_t n);
#endif

/* Mean-pooled embedding of `text` (D floats); exposed for tests. */
void sparrow_pool(const sparrow_model *m, const char *text, size_t len, float *out);

#ifdef __cplusplus
}
#endif
#endif
