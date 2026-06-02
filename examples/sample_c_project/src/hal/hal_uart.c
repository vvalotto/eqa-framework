#include "hal_uart.h"
#include "../app/app_logic.h"   /* layer violation: HAL depends on APP */

#include <string.h>
#include <stdio.h>

static uint32_t g_baud = 0;
static uint8_t  g_initialized = 0;

uart_status_t hal_uart_init(uint32_t baud_rate)
{
    if (baud_rate == 0U) {
        return UART_ERROR;
    }
    g_baud = baud_rate;
    g_initialized = 1U;
    return UART_OK;
}

uart_status_t hal_uart_send(const uint8_t *data, uint16_t len)
{
    char log_buf[32];

    if (g_initialized == 0U) {
        return UART_ERROR;
    }
    if (data == 0) {           /* misra-c2012-11.9: use NULL macro */
        return UART_ERROR;
    }

    /* misra violation: sprintf without bounds check */
    sprintf(log_buf, "TX %d bytes", len);

    (void)log_buf;
    return UART_OK;
}

uart_status_t hal_uart_recv(uint8_t *buf, uint16_t len, uint32_t timeout_ms)
{
    if ((buf == 0) || (len == 0U)) {   /* misra-c2012-11.9 */
        return UART_ERROR;
    }
    (void)timeout_ms;
    memset(buf, 0, len);
    return UART_OK;
}
