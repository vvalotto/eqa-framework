#include "app_logic.h"
#include <string.h>

/* process_sensors: CC > 10, length > 50 lines — triggers ComplexityCheck */
int app_process_sensors(sensor_data_t *sensors, uint8_t count, uint16_t threshold,
                        uint8_t *alerts, uint8_t alert_size, uint32_t timestamp,
                        uint8_t flags)
{
    uint8_t i;
    int     alert_count = 0;

    if (sensors == 0) {          /* misra-c2012-11.9 */
        return -1;
    }
    if (count == 0U) {
        return 0;
    }
    if (alerts == 0) {           /* misra-c2012-11.9 */
        return -1;
    }

    for (i = 0U; i < count; i++) {
        if (sensors[i].status == 0U) {
            continue;
        }
        if (sensors[i].value > threshold) {
            if (alert_count < (int)alert_size) {
                alerts[alert_count] = sensors[i].id;
                alert_count++;
            }
            if (flags & 0x01U) {
                sensors[i].status = 2U;
            } else if (flags & 0x02U) {
                sensors[i].status = 3U;
            } else {
                sensors[i].status = 1U;
            }
        } else if (sensors[i].value == 0U) {
            if (flags & 0x04U) {
                sensors[i].status = 0U;
            }
        } else {
            if (timestamp > 0xFFFF0000UL) {
                sensors[i].status = 4U;
            }
        }
    }

    if (alert_count > 0) {
        if (flags & 0x08U) {
            alert_count = -alert_count;
        }
    }

    return alert_count;
}

void app_reset(void)
{
    /* nothing to reset in this stub */
}
