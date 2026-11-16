#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/* Owned host fixture: no kernel fault injector or device access. */
static unsigned calls, injected, fail_at, live;

void *__real_malloc(size_t size);
void __real_free(void *pointer);

void *__wrap_malloc(size_t size) {
    calls++;
    if (fail_at != 0 && calls == fail_at) {
        injected++;
        errno = ENOMEM;
        return NULL;
    }
    void *pointer = __real_malloc(size);
    if (pointer != NULL) live++;
    return pointer;
}

void __wrap_free(void *pointer) {
    if (pointer != NULL) live--;
    __real_free(pointer);
}

/* Contract: 20 + 22 is 42; allocation failure preserves output and resources. */
static int operation(int *output) {
    int *left = malloc(sizeof(*left));
    if (left == NULL) return ENOMEM;
    int *right = malloc(sizeof(*right));
    if (right == NULL) {
#ifndef BROKEN_CLEANUP
        free(left);
#endif
        return ENOMEM;
    }
    *left = 20;
    *right = 22;
    *output = *left + *right;
    free(right);
    free(left);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) return 64;
    char *end;
    unsigned long configured = strtoul(argv[1], &end, 10);
    if (*argv[1] == '\0' || *end != '\0' || configured > 3) return 64;
    int observable = argv[2][0] == '1' && argv[2][1] == '\0';
    if (!observable && !(argv[2][0] == '0' && argv[2][1] == '\0')) return 64;
    fail_at = (unsigned)configured;
    int output = -1;
    int result = operation(&output);
    unsigned first_calls = calls, first_hits = injected, first_live = live;

    fail_at = 0;
    calls = injected = 0;
    int follow_up_output = -1;
    int follow_up_result = operation(&follow_up_output);
    printf("{\"configured_fail_at\":%lu,\"initial_calls\":%u,\"initial_injected\":",
           configured, first_calls);
    if (observable) printf("%u", first_hits);
    else printf("null");
    printf(",\"initial_result\":%d,\"initial_output\":%d,\"live_after_initial\":%u,"
           "\"follow_up_calls\":%u,\"follow_up_injected\":%u,"
           "\"follow_up_result\":%d,\"follow_up_output\":%d,"
           "\"live_after_follow_up\":%u}\n",
           result, output, first_live, calls, injected,
           follow_up_result, follow_up_output, live);
    return 0;
}
