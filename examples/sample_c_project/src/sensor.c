/*
 * sensor.c — Sample file for eqa-framework demos and e2e tests.
 * Intentionally contains defects detectable by codeguard-c.
 */
#include <stdio.h>
#include <string.h>

/* Intentional defects:
 *   - gets()        → flawfinder ERROR  (FF1014, level 5)
 *   - strcpy()      → flawfinder ERROR  (FF1001, level 4)
 *   - uninitvar     → cppcheck  ERROR
 *   - nullPointer   → cppcheck  ERROR
 *   - misra-c2012-11.9 (NULL literal) → CRITICAL
 */

static void read_sensor_name(void)
{
    char buf[64];
    gets(buf);   /* CWE-120: no bounds check */
}

static void copy_label(const char *src)
{
    char dst[64];
    strcpy(dst, src);   /* CWE-120: unbounded copy */
}

static int compute(int a)
{
    int result;               /* uninitialized */
    int *p = 0;               /* NULL pointer  */
    printf("%d %d\n", result, *p);
    return a + result;
}
