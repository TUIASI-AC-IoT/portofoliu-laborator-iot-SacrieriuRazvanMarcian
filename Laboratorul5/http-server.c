#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_mac.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "lwip/err.h"
#include "lwip/sys.h"
#include "freertos/event_groups.h"

#include "esp_http_server.h"

#define MAX_APs 10

char wifi_scan_results[1024];  

void scan_wifi_networks() {
    wifi_scan_config_t scan_config = {
        .ssid = NULL,
        .bssid = NULL,
        .channel = 0,
        .show_hidden = true
    };

    esp_wifi_scan_start(&scan_config, true);  

    uint16_t ap_count = 0;
    esp_wifi_scan_get_ap_num(&ap_count);
    wifi_ap_record_t ap_info[MAX_APs];

    if (ap_count > MAX_APs) ap_count = MAX_APs;
    esp_wifi_scan_get_ap_records(&ap_count, ap_info);

    strcpy(wifi_scan_results, "<html><body><form action=\"/results.html\" method=\"POST\">");
    strcat(wifi_scan_results, "<select name=\"ssid\">");

    for (int i = 0; i < ap_count; i++) {
        char option[128];
        sprintf(option, "<option value=\"%s\">%s</option>", ap_info[i].ssid, ap_info[i].ssid);
        strcat(wifi_scan_results, option);
    }

    strcat(wifi_scan_results, "</select>");
    strcat(wifi_scan_results, "<input type=\"password\" name=\"password\" placeholder=\"Enter Password\">");
    strcat(wifi_scan_results, "<input type=\"submit\" value=\"Connect\">");
    strcat(wifi_scan_results, "</form></body></html>");
}



/* Our URI handler function to be called during GET /uri request */
esp_err_t get_handler(httpd_req_t *req)
{
    /* Send a simple response */
    uint16_t ap_count = 0;
    wifi_ap_record_t ap_records[20];
    scan_wifi_networks();
    ESP_ERROR_CHECK(esp_wifi_scan_get_ap_num(&ap_count)); 
    ap_count = (ap_count > 20) ? 20 : ap_count;     
    ESP_ERROR_CHECK(esp_wifi_scan_get_ap_records(&ap_count, ap_records)); 

    const char *resp = "<html>\
    <body>\
    <form action='/results.html' target='_blank' method='post'>\
    <label for='ssid'>Networks found:</label>\
    <br>\
    <select name='ssid'>\
    <option value='ssid-exemplu-1'>ssid-exemplu-1</option>\
    <option value='ssid-exemplu-2'>ssid-exemplu-2</option>\
    <option value='ssid-exemplu-3'>ssid-exemplu-3</option>\
    <option value='ssid-exemplu-4'>ssid-exemplu-4</option>\
    </select>\
    <br>\
    <label for='ipass'>Security key:</label><br>\
    <input type='password' name='ipass'><br>\
    <input type='submit' value='Submit'>\
    </form>\
    </body>\
    </html>";

    httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

/* Our URI handler function to be called during POST /uri request */
esp_err_t post_handler(httpd_req_t *req)
{
    /* Destination buffer for content of HTTP POST request.
     * httpd_req_recv() accepts char* only, but content could
     * as well be any binary data (needs type casting).
     * In case of string data, null termination will be absent, and
     * content length would give length of string */
    char content[100];

    /* Truncate if content length larger than the buffer */
    size_t recv_size = MIN(req->content_len, sizeof(content));

    int ret = httpd_req_recv(req, content, recv_size);
    if (ret <= 0) {  /* 0 return value indicates connection closed */
        /* Check if timeout occurred */
        if (ret == HTTPD_SOCK_ERR_TIMEOUT) {
            /* In case of timeout one can choose to retry calling
             * httpd_req_recv(), but to keep it simple, here we
             * respond with an HTTP 408 (Request Timeout) error */
            httpd_resp_send_408(req);
        }
        /* In case of error, returning ESP_FAIL will
         * ensure that the underlying socket is closed */
        
        return ESP_FAIL;
    }

    /* Send a simple response */
    char ssid[32] = {0}, password[64] = {0};
    sscanf(content, "ssid=%31[^&]&password=%63s", ssid, password);  

    char response[256];
    sprintf(response, "<html><body>SSID: %s<br>Password: %s</body></html>", ssid, password);
    httpd_resp_send(req, response, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

/* URI handler structure for GET /uri */
httpd_uri_t uri_get = {
    .uri      = "/index.html",
    .method   = HTTP_GET,
    .handler  = get_handler,
    .user_ctx = NULL
};

/* URI handler structure for POST /uri */
httpd_uri_t uri_post = {
    .uri      = "/results.html",
    .method   = HTTP_POST,
    .handler  = post_handler,
    .user_ctx = NULL
};

/* Function for starting the webserver */
httpd_handle_t start_webserver(void)
{
    /* Generate default configuration */
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    /* Empty handle to esp_http_server */
    httpd_handle_t server = NULL;

    /* Start the httpd server */
    if (httpd_start(&server, &config) == ESP_OK) {
        /* Register URI handlers */
        httpd_register_uri_handler(server, &uri_get);
        httpd_register_uri_handler(server, &uri_post);
    }
    /* If server failed to start, handle will be NULL */
    return server;
}

/* Function for stopping the webserver */
void stop_webserver(httpd_handle_t server)
{
    if (server) {
        /* Stop the httpd server */
        httpd_stop(server);
    }
}