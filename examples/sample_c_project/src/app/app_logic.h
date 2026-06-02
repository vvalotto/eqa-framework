/* app_logic.h — intentionally missing include guard (MISRA 4.10 violation) */

#include <stdint.h>

#define MAX_SENSORS 8

typedef struct {
    uint8_t  id;
    uint16_t value;
    uint8_t  status;
} sensor_data_t;

int  app_process_sensors(sensor_data_t *sensors, uint8_t count, uint16_t threshold,
                         uint8_t *alerts, uint8_t alert_size, uint32_t timestamp,
                         uint8_t flags);
void app_reset(void);
