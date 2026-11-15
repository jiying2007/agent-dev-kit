#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>

__attribute__((noinline)) static int marked_function(int value)
{
    return value + 7;
}

int main(void)
{
    Dl_info image;
    if (!dladdr((void *)&marked_function, &image))
        return 2;
    printf("%zx %zx\n", (uintptr_t)&marked_function, (uintptr_t)image.dli_fbase);
    return marked_function(0) == 7 ? 0 : 3;
}
