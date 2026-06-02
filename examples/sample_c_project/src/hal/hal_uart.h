#ifndef HAL_UART_H
#define HAL_UART_H

#include <stdint.h>

typedef enum {
    UART_OK    = 0,
    UART_ERROR = 1,
    UART_BUSY  = 2
} uart_status_t;

uart_status_t hal_uart_init(uint32_t baud_rate);
uart_status_t hal_uart_send(const uint8_t *data, uint16_t len);
uart_status_t hal_uart_recv(uint8_t *buf, uint16_t len, uint32_t timeout_ms);

#endif /* HAL_UART_H */
