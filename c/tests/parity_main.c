/* Host-side test driver: reads cases from stdin, prints probabilities and per-call time.
 * Line format (tab-separated, \n \t \\ escaped): kind  state  instructions  n  name1  desc1 ...
 *   cc -O2 -Isparrow/include sparrow/src/sparrow.c tests/parity_main.c -lm -o build/parity && build/parity model.spb < cases.tsv */
#define _POSIX_C_SOURCE 199309L /* clock_gettime under -std=c99 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "sparrow.h"

static char *unescape(char *s) {
    char *o = s, *r = s;
    while (*r) {
        if (*r == '\\' && r[1]) {
            r++;
            *o++ = *r == 'n' ? '\n' : *r == 't' ? '\t' : *r;
            r++;
        } else {
            *o++ = *r++;
        }
    }
    *o = 0;
    return s;
}

static sparrow_ctx ctx;

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 2;
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    void *blob = malloc((size_t)len);
    if (fread(blob, 1, (size_t)len, f) != (size_t)len) return 2;
    fclose(f);
    sparrow_model m;
    int rc = sparrow_load(&m, blob, (size_t)len);
    if (rc) { fprintf(stderr, "load failed %d\n", rc); return 1; }
    fprintf(stderr, "V=%u D=%u hidden=%u nf=%u kv=%u\n", m.V, m.D, m.hidden, m.nf, m.kv);
    static char line[1 << 20];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        char *fld[2 + 3 + 2 * SPARROW_MAX_OPTIONS];
        int nf = 0;
        char *p = line;
        while (nf < (int)(sizeof fld / sizeof fld[0])) {
            fld[nf++] = p;
            char *t = strchr(p, '\t');
            if (!t) break;
            *t = 0;
            p = t + 1;
        }
        for (int i = 0; i < nf; i++) unescape(fld[i]);
        int kind = atoi(fld[0]), n = atoi(fld[3]);
        sparrow_option opts[SPARROW_MAX_OPTIONS];
        for (int k = 0; k < n; k++) {
            opts[k].name = fld[4 + 2 * k];
            opts[k].desc = fld[5 + 2 * k];
        }
        float pr[SPARROW_MAX_OPTIONS];
        struct timespec a, b;
        clock_gettime(CLOCK_MONOTONIC, &a);
        rc = sparrow_probs(&m, &ctx, fld[1], fld[2], (sparrow_kind)kind, opts, n, pr);
        clock_gettime(CLOCK_MONOTONIC, &b);
        double us = (b.tv_sec - a.tv_sec) * 1e6 + (b.tv_nsec - a.tv_nsec) / 1e3;
        printf("%d %.1f", rc, us);
        for (int k = 0; k < n; k++) printf(" %.6f", pr[k]);
        printf("\n");
    }
    return 0;
}
