#include <stdio.h>
#include <string.h>
#include "hal/hal_uart.h"
#include "app/app_logic.h"

/* High CC function (> 10): triggers ComplexityCheck CCN001 */
static int classify_reading(int value, int mode, int flags, int limit)
{
    if (value < 0) {
        return -1;
    }
    if (mode == 1) {
        if (value > limit) {
            if (flags & 1) { return 3; }
            else if (flags & 2) { return 4; }
            else { return 2; }
        } else if (value == limit) {
            return 1;
        } else {
            return 0;
        }
    } else if (mode == 2) {
        if (value > limit * 2) { return 5; }
        else if (value > limit) { return 4; }
        else { return 3; }
    } else if (mode == 3) {
        if ((flags & 1) && (value > 0)) { return 6; }
        if ((flags & 2) && (value > limit)) { return 7; }
        return 8;
    } else {
        return -2;
    }
}

int main(void)
{
    char           name[32];
    sensor_data_t  sensors[MAX_SENSORS];
    uint8_t        alerts[MAX_SENSORS];
    uart_status_t  status;
    int            result;

    /* flawfinder ERROR: gets() has no bounds check */
    gets(name);

    memset(sensors, 0, sizeof(sensors));

    status = hal_uart_init(115200U);
    if (status != UART_OK) {
        return 1;
    }

    result = app_process_sensors(sensors, MAX_SENSORS, 512U, alerts,
                                 MAX_SENSORS, 0U, 0U);

    printf("alerts: %d, class: %d\n", result,
           classify_reading(100, 1, 3, 200));

    return 0;
}
