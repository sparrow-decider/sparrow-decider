/* Sparrow Decider C runtime. See include/sparrow.h. Mirrors python/sparrow_decider/static.py:
 * BERT-uncased WordPiece, mean-pooled int8 embeddings, key-value number pooling, and a 2-layer
 * GELU MLP over option features. Text normalisation is exact for ASCII and Latin-1/Latin
 * Extended-A; other scripts are passed through unchanged (no case folding). */
#include "sparrow.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* ---------------------------------------------------------------- blob loading */

typedef struct {
    const uint8_t *p, *end;
} rd;

static const void *take(rd *r, size_t n) {
    const uint8_t *p = r->p;
    size_t padded = (n + 3u) & ~(size_t)3u;
    if ((size_t)(r->end - r->p) < n) return NULL;
    r->p += ((size_t)(r->end - r->p) < padded) ? n : padded;
    return p;
}

static uint32_t u32(const void *p) {
    uint32_t v;
    memcpy(&v, p, 4);
    return v;
}

sparrow_status sparrow_load(sparrow_model *m, const void *blob, size_t len) {
    rd r = {(const uint8_t *)blob, (const uint8_t *)blob + len};
    const uint8_t *h = take(&r, 32);
    if (!h || memcmp(h, "SPB1", 4) != 0 || u32(h + 4) != 1) return SPARROW_ERR_FORMAT;
    memset(m, 0, sizeof *m);
    m->kv = u32(h + 8) & 1u;
    m->V = u32(h + 12);
    m->D = u32(h + 16);
    m->hidden = u32(h + 20);
    m->nf = u32(h + 24);
    m->max_len = u32(h + 28);
    if (m->D > SPARROW_MAX_DIM || m->hidden > SPARROW_MAX_HIDDEN || m->nf > 10) return SPARROW_ERR_SIZE;
    const uint8_t *t = take(&r, 16);
    if (!t) return SPARROW_ERR_FORMAT;
    memcpy(m->temps, t, 12);
    m->unk_id = u32(t + 12);
    const uint8_t *sb = take(&r, 4);
    if (!sb) return SPARROW_ERR_FORMAT;
    uint32_t strbytes = u32(sb);
    size_t V = m->V, D = m->D, H = m->hidden;
#define TAKE(dst, type, n)                                  \
    do {                                                    \
        dst = (const type *)take(&r, (size_t)(n) * sizeof(type)); \
        if (!dst) return SPARROW_ERR_FORMAT;                \
    } while (0)
    TAKE(m->strings, char, strbytes);
    TAKE(m->str_off, uint32_t, V);
    TAKE(m->str_id, uint32_t, V);
    TAKE(m->emb, int8_t, V * D);
    TAKE(m->emb_scale, float, V);
    TAKE(m->kind, float, 3 * D);
    if (m->kv) {
        TAKE(m->g_w, float, D * 4);
        TAKE(m->g_b, float, D);
        TAKE(m->tau, float, 1);
    }
    TAKE(m->w0, int8_t, H * m->nf * D);
    TAKE(m->s0, float, H);
    TAKE(m->b0, float, H);
    TAKE(m->w2, int8_t, H * H);
    TAKE(m->s2, float, H);
    TAKE(m->b2, float, H);
    TAKE(m->w4, float, H);
    TAKE(m->b4, float, 1);
#undef TAKE
    return SPARROW_OK;
}

/* ---------------------------------------------------------------- normalisation */

/* Latin-1 Supplement and Latin Extended-A, U+00C0..U+017F: lower() then NFD minus combining marks,
 * as up to two code points (generated from Python's unicodedata). */
static const uint16_t LATIN[192][2] = {
    {0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0xe6,0x0},{0x63,0x0},
    {0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},
    {0xf0,0x0},{0x6e,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0xd7,0x0},
    {0xf8,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x79,0x0},{0xfe,0x0},{0xdf,0x0},
    {0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0xe6,0x0},{0x63,0x0},
    {0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},
    {0xf0,0x0},{0x6e,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0xf7,0x0},
    {0xf8,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x79,0x0},{0xfe,0x0},{0x79,0x0},
    {0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x61,0x0},{0x63,0x0},{0x63,0x0},
    {0x63,0x0},{0x63,0x0},{0x63,0x0},{0x63,0x0},{0x63,0x0},{0x63,0x0},{0x64,0x0},{0x64,0x0},
    {0x111,0x0},{0x111,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},
    {0x65,0x0},{0x65,0x0},{0x65,0x0},{0x65,0x0},{0x67,0x0},{0x67,0x0},{0x67,0x0},{0x67,0x0},
    {0x67,0x0},{0x67,0x0},{0x67,0x0},{0x67,0x0},{0x68,0x0},{0x68,0x0},{0x127,0x0},{0x127,0x0},
    {0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},{0x69,0x0},
    {0x69,0x0},{0x131,0x0},{0x133,0x0},{0x133,0x0},{0x6a,0x0},{0x6a,0x0},{0x6b,0x0},{0x6b,0x0},
    {0x138,0x0},{0x6c,0x0},{0x6c,0x0},{0x6c,0x0},{0x6c,0x0},{0x6c,0x0},{0x6c,0x0},{0x140,0x0},
    {0x140,0x0},{0x142,0x0},{0x142,0x0},{0x6e,0x0},{0x6e,0x0},{0x6e,0x0},{0x6e,0x0},{0x6e,0x0},
    {0x6e,0x0},{0x149,0x0},{0x14b,0x0},{0x14b,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},{0x6f,0x0},
    {0x6f,0x0},{0x6f,0x0},{0x153,0x0},{0x153,0x0},{0x72,0x0},{0x72,0x0},{0x72,0x0},{0x72,0x0},
    {0x72,0x0},{0x72,0x0},{0x73,0x0},{0x73,0x0},{0x73,0x0},{0x73,0x0},{0x73,0x0},{0x73,0x0},
    {0x73,0x0},{0x73,0x0},{0x74,0x0},{0x74,0x0},{0x74,0x0},{0x74,0x0},{0x167,0x0},{0x167,0x0},
    {0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},
    {0x75,0x0},{0x75,0x0},{0x75,0x0},{0x75,0x0},{0x77,0x0},{0x77,0x0},{0x79,0x0},{0x79,0x0},
    {0x79,0x0},{0x7a,0x0},{0x7a,0x0},{0x7a,0x0},{0x7a,0x0},{0x7a,0x0},{0x7a,0x0},{0x17f,0x0}};

static int is_control(uint32_t c) {
    if (c == '\t' || c == '\n' || c == '\r') return 0;
    return c < 0x20 || (c >= 0x7f && c < 0xa0) || c == 0xad || (c >= 0x200b && c <= 0x200f) ||
           (c >= 0x202a && c <= 0x202e) || (c >= 0x2060 && c <= 0x2064) || c == 0xfeff;
}

static int is_space(uint32_t c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == 0xa0 || c == 0x1680 ||
           (c >= 0x2000 && c <= 0x200a) || c == 0x202f || c == 0x205f || c == 0x3000;
}

static int is_punct(uint32_t c) {
    if ((c >= 33 && c <= 47) || (c >= 58 && c <= 64) || (c >= 91 && c <= 96) || (c >= 123 && c <= 126)) return 1;
    return c == 0xa1 || c == 0xa7 || c == 0xab || c == 0xb6 || c == 0xb7 || c == 0xbb || c == 0xbf ||
           (c >= 0x2010 && c <= 0x2027) || (c >= 0x2030 && c <= 0x205e) || (c >= 0x3001 && c <= 0x3003) ||
           (c >= 0x3008 && c <= 0x3011) || (c >= 0xff01 && c <= 0xff0f);
}

static int is_cjk(uint32_t c) {
    return (c >= 0x4e00 && c <= 0x9fff) || (c >= 0x3400 && c <= 0x4dbf) || (c >= 0x20000 && c <= 0x2a6df) ||
           (c >= 0x2a700 && c <= 0x2b73f) || (c >= 0x2b740 && c <= 0x2b81f) || (c >= 0x2b820 && c <= 0x2ceaf) ||
           (c >= 0xf900 && c <= 0xfaff) || (c >= 0x2f800 && c <= 0x2fa1f);
}

static uint32_t utf8_next(const char *s, size_t len, size_t *i) {
    const unsigned char *u = (const unsigned char *)s;
    uint32_t c = u[*i];
    size_t n = c < 0x80 ? 1 : (c >> 5) == 6 ? 2 : (c >> 4) == 14 ? 3 : (c >> 3) == 30 ? 4 : 1;
    if (*i + n > len) n = 1;
    if (n == 1) {
        (*i)++;
        return c < 0x80 ? c : 0xfffd;
    }
    c &= (0x7f >> n);
    for (size_t k = 1; k < n; k++) c = (c << 6) | (u[*i + k] & 0x3f);
    *i += n;
    return c;
}

static int utf8_put(uint32_t c, char *o) {
    if (c < 0x80) { o[0] = (char)c; return 1; }
    if (c < 0x800) { o[0] = (char)(0xc0 | (c >> 6)); o[1] = (char)(0x80 | (c & 0x3f)); return 2; }
    if (c < 0x10000) {
        o[0] = (char)(0xe0 | (c >> 12)); o[1] = (char)(0x80 | ((c >> 6) & 0x3f)); o[2] = (char)(0x80 | (c & 0x3f));
        return 3;
    }
    o[0] = (char)(0xf0 | (c >> 18)); o[1] = (char)(0x80 | ((c >> 12) & 0x3f));
    o[2] = (char)(0x80 | ((c >> 6) & 0x3f)); o[3] = (char)(0x80 | (c & 0x3f));
    return 4;
}

/* Lowercase + strip accents into out[0..1]; returns the number of code points (0 = dropped). */
static int fold(uint32_t c, uint32_t *out) {
    if (c >= 'A' && c <= 'Z') c += 32;
    else if (c >= 0x300 && c <= 0x36f) return 0;
    else if (c >= 0xc0 && c <= 0x17f) {
        out[0] = LATIN[c - 0xc0][0];
        out[1] = LATIN[c - 0xc0][1];
        return out[0] ? (out[1] ? 2 : 1) : 0;
    }
    out[0] = c;
    return 1;
}

/* ---------------------------------------------------------------- vocabulary + WordPiece */

static int vocab_find(const sparrow_model *m, const char *s, size_t n, int cont) {
    /* binary search over byte-sorted pieces; `cont` prepends "##" */
    uint32_t lo = 0, hi = m->V;
    while (lo < hi) {
        uint32_t mid = (lo + hi) / 2;
        const unsigned char *p = (const unsigned char *)(m->strings + m->str_off[mid]);
        int c = 0;
        size_t k = 0;
        if (cont) {
            c = (int)p[0] - '#';
            if (!c) c = (int)p[1] - '#';
            if (!c) p += 2;
        }
        if (!c) {
            for (k = 0; k < n; k++) {
                c = (int)p[k] - (int)(unsigned char)s[k];
                if (c || !p[k]) break;
            }
            if (!c && k == n) c = p[n] ? 1 : 0;
        }
        if (c == 0) return (int)m->str_id[mid];
        if (c < 0) lo = mid + 1;
        else hi = mid;
    }
    return -1;
}

typedef struct {
    float *acc;
    uint32_t count;
} pooler;

static void add_row(const sparrow_model *m, pooler *pl, uint32_t id) {
    const int8_t *row = m->emb + (size_t)id * m->D;
    float sc = m->emb_scale[id];
    for (uint32_t d = 0; d < m->D; d++) pl->acc[d] += (float)row[d] * sc;
    pl->count++;
}

/* WordPiece one normalised word (UTF-8, `nc` code points, boundaries in `cb`). */
static void wordpiece(const sparrow_model *m, pooler *pl, const char *w, const uint16_t *cb, int nc) {
    if (pl->count >= m->max_len) return;
    uint32_t ids[100];
    int n = 0;
    if (nc > 100) {
        add_row(m, pl, m->unk_id);
        return;
    }
    int start = 0;
    while (start < nc) {
        int end = nc, id = -1;
        while (start < end) {
            id = vocab_find(m, w + cb[start], (size_t)(cb[end] - cb[start]), start > 0);
            if (id >= 0) break;
            end--;
        }
        if (id < 0) {
            add_row(m, pl, m->unk_id);
            return;
        }
        ids[n++] = (uint32_t)id;
        start = end;
    }
    for (int k = 0; k < n && pl->count < m->max_len; k++) add_row(m, pl, ids[k]);
}

static void pool_text(const sparrow_model *m, pooler *pl, const char *text, size_t len) {
    char w[404];
    uint16_t cb[102];
    int nb = 0, nc = 0, over = 0;
    size_t i = 0;
#define FLUSH()                                             \
    do {                                                    \
        if (nc) {                                           \
            if (over) add_row(m, pl, m->unk_id);            \
            else wordpiece(m, pl, w, cb, nc);               \
        }                                                   \
        nb = nc = over = 0;                                 \
    } while (0)
    while (i < len && pl->count < m->max_len) {
        uint32_t c = utf8_next(text, len, &i);
        if (c == 0 || c == 0xfffd || is_control(c)) continue;
        if (is_space(c)) { FLUSH(); continue; }
        int cjk = is_cjk(c);
        uint32_t fc[2];
        int nf = fold(c, fc);
        for (int k = 0; k < nf; k++) {
            c = fc[k];
            if (cjk || is_punct(c)) {
                FLUSH();
                nb = utf8_put(c, w);
                cb[0] = 0;
                cb[1] = (uint16_t)nb;
                nc = 1;
                FLUSH();
                continue;
            }
            if (nc >= 101 || nb + 4 > 400) { over = 1; nc = 101; continue; }
            cb[nc] = (uint16_t)nb;
            nb += utf8_put(c, w + nb);
            cb[++nc] = (uint16_t)nb;
        }
    }
    FLUSH();
#undef FLUSH
}

static void pool_finish(const sparrow_model *m, pooler *pl, float *out) {
    if (!pl->count) {
        for (uint32_t d = 0; d < m->D; d++) out[d] = 0;
        add_row(m, pl, 0);
    }
    float inv = 1.0f / (float)pl->count;
    for (uint32_t d = 0; d < m->D; d++) out[d] = pl->acc[d] * inv;
}

void sparrow_pool(const sparrow_model *m, const char *text, size_t len, float *out) {
    pooler pl = {out, 0};
    memset(out, 0, m->D * sizeof(float));
    pool_text(m, &pl, text, len);
    pool_finish(m, &pl, out);
}

/* ---------------------------------------------------------------- key-value pairs */

static int is_alpha(int c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'); }
static int is_digit(int c) { return c >= '0' && c <= '9'; }
static int is_keych(int c) { return is_alpha(c) || is_digit(c) || c == '_' || c == ' ' || c == '.' || c == '-'; }
static int is_ws(int c) { return c == ' ' || c == '\t' || c == '\f' || c == '\v'; }

/* Match /([A-Za-z][A-Za-z0-9_ .\-]{0,40}?)\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*(%?)/ at s[p]. Returns
 * the match end or -1; key span and number span via out params. */
static long kv_match(const char *s, long n, long p, long *ke, long *ns, long *ne) {
    if (!is_alpha((unsigned char)s[p])) return -1;
    for (long L = 1; L <= 41 && p + L <= n; L++) {
        if (L > 1 && !is_keych((unsigned char)s[p + L - 1])) break;
        long j = p + L;
        while (j < n && is_ws((unsigned char)s[j])) j++;
        if (j >= n || (s[j] != ':' && s[j] != '=')) continue;
        j++;
        while (j < n && is_ws((unsigned char)s[j])) j++;
        long st = j;
        if (j < n && s[j] == '-') j++;
        if (j >= n || !is_digit((unsigned char)s[j])) continue;
        while (j < n && is_digit((unsigned char)s[j])) j++;
        if (j + 1 < n && s[j] == '.' && is_digit((unsigned char)s[j + 1])) {
            j++;
            while (j < n && is_digit((unsigned char)s[j])) j++;
        }
        long en = j;
        while (j < n && is_ws((unsigned char)s[j])) j++;
        if (j < n && s[j] == '%') j++;
        *ke = p + L;
        *ns = st;
        *ne = en;
        return j;
    }
    return -1;
}

static void strip(const char *s, long a, long b, long *oa, long *ob) {
    while (a < b && (is_ws((unsigned char)s[a]) || s[a] == '\n' || s[a] == '\r')) a++;
    while (b > a && (is_ws((unsigned char)s[b - 1]) || s[b - 1] == '\n' || s[b - 1] == '\r')) b--;
    *oa = a;
    *ob = b;
}

static void normalize(float *v, uint32_t D) {
    float n = 0;
    for (uint32_t d = 0; d < D; d++) n += v[d] * v[d];
    n = sqrtf(n);
    if (n < 1e-12f) n = 1e-12f;
    for (uint32_t d = 0; d < D; d++) v[d] /= n;
}

static int is_linebreak(int c) { return c == '\n' || c == '\r' || c == '\v' || c == '\f' || (c >= 0x1c && c <= 0x1e); }

/* Fills ctx->pv (emb(key) * g(value)) and ctx->el (normalised line label); returns pair count. */
static int read_pairs(const sparrow_model *m, sparrow_ctx *ctx, const char *s, long n) {
    int np = 0;
    uint32_t D = m->D;
    long ls = 0;
    while (ls < n && np < SPARROW_MAX_PAIRS) {
        long le = ls;
        while (le < n && !is_linebreak((unsigned char)s[le])) le++;
        long hb = ls;
        while (hb < le && s[hb] != ':') hb++;
        long ha, hz;
        strip(s, ls, hb, &ha, &hz);
        long p = ls;
        while (p < le && np < SPARROW_MAX_PAIRS) {
            long ke, ns, ne;
            long e = kv_match(s, le, p, &ke, &ns, &ne);
            if (e < 0) { p++; continue; }
            long ka, kz;
            strip(s, p, ke, &ka, &kz);
            char num[48];
            long nl = ne - ns < 47 ? ne - ns : 47;
            memcpy(num, s + ns, (size_t)nl);
            num[nl] = 0;
            float v = strtof(num, NULL);
            float *pv = ctx->pv[np], *el = ctx->el[np];
            sparrow_pool(m, s + ka, (size_t)(kz - ka), pv);
            normalize(pv, D);
            int same = (hz - ha == kz - ka) && !memcmp(s + ha, s + ka, (size_t)(kz - ka));
            if (hz > ha && !same) sparrow_pool(m, s + ha, (size_t)(hz - ha), el);
            else sparrow_pool(m, s + ka, (size_t)(kz - ka), el);
            normalize(el, D);
            float a = fabsf(v), vf[4];
            vf[0] = fmaxf(-1.f, fminf(1.f, v / 100.f));
            vf[1] = copysignf(log1pf(a), v) / 5.f;
            vf[2] = (a > 0 && a < 1) ? 1.f : 0.f;
            vf[3] = fmaxf(-1.f, fminf(1.f, v / 10.f));
            for (uint32_t d = 0; d < D; d++) {
                const float *g = m->g_w + (size_t)d * 4;
                pv[d] *= tanhf(g[0] * vf[0] + g[1] * vf[1] + g[2] * vf[2] + g[3] * vf[3] + m->g_b[d]);
            }
            np++;
            p = e > p ? e : p + 1;
        }
        ls = le;
        if (ls < n && s[ls] == '\r' && ls + 1 < n && s[ls + 1] == '\n') ls++;
        ls++;
    }
    return np;
}

/* ---------------------------------------------------------------- scoring */

static float gelu(float x) { return 0.5f * x * (1.0f + erff(x * 0.70710678f)); }

#if SPARROW_INT8_ACT
/* Weak so a port can supply a SIMD version (e.g. the ESP32-S3 PIE unit). */
__attribute__((weak)) int32_t sparrow_dot_s8(const int8_t *a, const int8_t *b, uint32_t n) {
    int32_t acc = 0;
    for (uint32_t i = 0; i < n; i++) acc += (int32_t)a[i] * (int32_t)b[i];
    return acc;
}

/* Symmetric int8 with one scale for the vector; returns the scale. */
static float quantize(const float *x, uint32_t n, int8_t *q) {
    float mx = 0;
    for (uint32_t i = 0; i < n; i++) mx = fmaxf(mx, fabsf(x[i]));
    float s = mx > 0 ? mx / 127.f : 1.f, inv = 1.f / s;
    for (uint32_t i = 0; i < n; i++) q[i] = (int8_t)lrintf(x[i] * inv);
    return s;
}
#endif

static const char *NOUL_NAMES[2] = {"false", "true"};
static const char *NOUL_DESC[2] = {"the statement does not hold for this state", "the statement holds for this state"};

static void pool_option(const sparrow_model *m, const char *name, const char *desc, float *out) {
    pooler pl = {out, 0};
    memset(out, 0, m->D * sizeof(float));
    pool_text(m, &pl, name, strlen(name));
    if (desc) pool_text(m, &pl, desc, strlen(desc));
    pool_finish(m, &pl, out);
}

static size_t trimmed(const char *s, const char **start) {
    size_t n = strlen(s);
    while (n && (is_ws((unsigned char)*s) || *s == '\n' || *s == '\r')) { s++; n--; }
    while (n && (is_ws((unsigned char)s[n - 1]) || s[n - 1] == '\n' || s[n - 1] == '\r')) n--;
    *start = s;
    return n;
}

sparrow_status sparrow_probs(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *instructions,
                             sparrow_kind kind, const sparrow_option *opts, int n_opts, float *probs) {
    uint32_t D = m->D, H = m->hidden;
    sparrow_option noul[2];
    if (kind == SPARROW_NOUL && !opts) {
        noul[0].name = NOUL_NAMES[0]; noul[0].desc = NOUL_DESC[0];
        noul[1].name = NOUL_NAMES[1]; noul[1].desc = NOUL_DESC[1];
        opts = noul;
        n_opts = 2;
    }
    if (n_opts < 2 || n_opts > SPARROW_MAX_OPTIONS || (unsigned)kind > 2) return SPARROW_ERR_ARGS;
    const char *st;
    size_t sl = trimmed(state ? state : "", &st);
    sparrow_pool(m, st, sl, ctx->s);
    const char *qs;
    size_t ql = trimmed(instructions ? instructions : "", &qs);
    sparrow_pool(m, qs, ql, ctx->q);
    for (uint32_t d = 0; d < D; d++) ctx->q[d] += m->kind[kind * D + d];
    normalize(ctx->s, D);
    normalize(ctx->q, D);
    memset(ctx->omean, 0, D * sizeof(float));
    for (int k = 0; k < n_opts; k++) {
        pool_option(m, opts[k].name, opts[k].desc, ctx->o[k]);
        normalize(ctx->o[k], D);
        for (uint32_t d = 0; d < D; d++) ctx->omean[d] += ctx->o[k][d] / (float)n_opts;
    }
    int np = 0;
    if (m->kv) {
        np = read_pairs(m, ctx, st, (long)sl);
        memset(ctx->kv, 0, D * sizeof(float));
        for (int j = 0; j < np; j++)
            for (uint32_t d = 0; d < D; d++) ctx->kv[d] += ctx->pv[j][d] / (float)np;
    }
    float temp = m->temps[kind] > 0 ? m->temps[kind] : 1.0f, mx = -1e30f;
    for (int k = 0; k < n_opts; k++) {
        const float *o = ctx->o[k], *s = ctx->s, *q = ctx->q, *om = ctx->omean;
        float *f = ctx->feat;
        for (uint32_t d = 0; d < D; d++) {
            f[d] = o[d];
            f[D + d] = s[d] * o[d];
            f[2 * D + d] = q[d] * o[d];
            f[3 * D + d] = s[d] * q[d] * o[d];
            f[4 * D + d] = o[d] - om[d];
            f[5 * D + d] = (s[d] - om[d]) * o[d];
        }
        if (m->kv) {
            memset(ctx->kvo, 0, D * sizeof(float));
            if (np) {
                float att[SPARROW_MAX_PAIRS], amx = -1e30f, z = 0;
                for (int j = 0; j < np; j++) {
                    float dot = 0;
                    for (uint32_t d = 0; d < D; d++) dot += o[d] * ctx->el[j][d];
                    att[j] = m->tau[0] * dot;
                    if (att[j] > amx) amx = att[j];
                }
                for (int j = 0; j < np; j++) z += (att[j] = expf(att[j] - amx));
                for (int j = 0; j < np; j++)
                    for (uint32_t d = 0; d < D; d++) ctx->kvo[d] += att[j] / z * ctx->pv[j][d];
            }
            for (uint32_t d = 0; d < D; d++) {
                f[6 * D + d] = ctx->kv[d] * o[d];
                f[7 * D + d] = ctx->kv[d] * q[d] * o[d];
                f[8 * D + d] = ctx->kvo[d];
                f[9 * D + d] = ctx->kvo[d] * q[d];
            }
        }
        uint32_t IN = m->nf * D;
#if SPARROW_INT8_ACT
        /* int8 x int8 -> int32 dot products; each D-wide feature block gets its own scale */
        float bs[10], hs;
        for (uint32_t b = 0; b < m->nf; b++) bs[b] = quantize(f + b * D, D, ctx->fq + b * D);
        for (uint32_t h = 0; h < H; h++) {
            const int8_t *w = m->w0 + (size_t)h * IN;
            float acc = 0;
            for (uint32_t b = 0; b < m->nf; b++) acc += (float)sparrow_dot_s8(w + b * D, ctx->fq + b * D, D) * bs[b];
            ctx->h0[h] = gelu(acc * m->s0[h] + m->b0[h]);
        }
        hs = quantize(ctx->h0, H, ctx->hq);
        float logit = m->b4[0];
        for (uint32_t h = 0; h < H; h++) {
            float acc = (float)sparrow_dot_s8(m->w2 + (size_t)h * H, ctx->hq, H) * hs;
            logit += m->w4[h] * gelu(acc * m->s2[h] + m->b2[h]);
        }
#else
        for (uint32_t h = 0; h < H; h++) {
            const int8_t *w = m->w0 + (size_t)h * IN;
            float acc = 0;
            for (uint32_t i = 0; i < IN; i++) acc += (float)w[i] * f[i];
            ctx->h0[h] = gelu(acc * m->s0[h] + m->b0[h]);
        }
        float logit = m->b4[0];
        for (uint32_t h = 0; h < H; h++) {
            const int8_t *w = m->w2 + (size_t)h * H;
            float acc = 0;
            for (uint32_t i = 0; i < H; i++) acc += (float)w[i] * ctx->h0[i];
            logit += m->w4[h] * gelu(acc * m->s2[h] + m->b2[h]);
        }
#endif
        probs[k] = logit / temp;
        if (probs[k] > mx) mx = probs[k];
    }
    float z = 0;
    for (int k = 0; k < n_opts; k++) z += (probs[k] = expf(probs[k] - mx));
    for (int k = 0; k < n_opts; k++) probs[k] /= z;
    return SPARROW_OK;
}

/* ---------------------------------------------------------------- answer shapes */

float sparrow_noul(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question) {
    float p[2];
    if (sparrow_probs(m, ctx, state, question, SPARROW_NOUL, NULL, 0, p) != SPARROW_OK) return -1.f;
    return p[1];
}

int sparrow_choice(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question,
                   const sparrow_option *opts, int n_opts, float *confidence) {
    float p[SPARROW_MAX_OPTIONS];
    if (sparrow_probs(m, ctx, state, question, SPARROW_CHOICE, opts, n_opts, p) != SPARROW_OK) return -1;
    int best = 0;
    for (int k = 1; k < n_opts; k++)
        if (p[k] > p[best]) best = k;
    if (confidence) *confidence = ((float)n_opts * p[best] - 1.f) / (float)(n_opts - 1);
    return best;
}

float sparrow_score(const sparrow_model *m, sparrow_ctx *ctx, const char *state, const char *question,
                    const char *const *levels, int n_levels, float *confidence) {
    sparrow_option opts[SPARROW_MAX_OPTIONS];
    static const char *digits[] = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"};
    float p[SPARROW_MAX_OPTIONS];
    if (n_levels < 2 || n_levels > 10) return -1.f;
    for (int i = 0; i < n_levels; i++) {
        opts[i].name = digits[i];
        opts[i].desc = levels[i];
    }
    if (sparrow_probs(m, ctx, state, question, SPARROW_SCORE, opts, n_levels, p) != SPARROW_OK) return -1.f;
    float ev = 0, var = 0;
    for (int i = 0; i < n_levels; i++) ev += (float)i * p[i];
    for (int i = 0; i < n_levels; i++) var += ((float)i - ev) * ((float)i - ev) * p[i];
    if (confidence) *confidence = 1.f - sqrtf(var) / ((float)(n_levels - 1) / 2.f);
    return ev;
}
