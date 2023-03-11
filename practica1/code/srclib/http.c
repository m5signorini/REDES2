#include "sockets.h"
#include "picohttpparser.h"
#include "cgi.h"
#include <time.h>
#include "http.h"
#include <sys/stat.h>

// Max header para facilitar la reserva de memoria, el mismo que usa mozilla
#define MAX_HEADERS_SIZE 8192
#define MAX_REQUEST_SIZE 8192
#define MAX_HEADERS_NUMBER 100
#define MAX_PATH_SIZE 1024
#define MAX_VALUE_SIZE 1024

/**********************/
/* PRIVATE PROTOTYPES */
/**********************/
int http_get_response_line               (char *header, int len, int code);
int http_get_header_allow                (char *header, int len, struct stat *stat);
int http_get_header_date                 (char *header, int len);
int http_get_header_last_modify          (char *header, int len, char *path);
int http_get_header_server               (char *header, int len, char *signature);
int http_get_header_content_type         (char *header, int len, char *path);
int http_get_header_content_length_string(char *header, int len, char *str, long *str_len);
int http_get_header_content_length_file  (char *header, int len, FILE *fp, long *file_len);

int http_get_headers_cgi(char *headers, int headers_max, int code, char *output, long *output_len, http_conf *config, int *error);
int http_get_headers(char *headers, int headers_max, int code, FILE *fp, long *file_len, char *path, http_conf *config, struct stat* stat, int *error);
char* http_get_error_doc(char *path, int len, int code, http_conf *config);

int http_read_request(int sockfd, char* request, int request_len);
int http_init_response(int sockfd, http_conf *config, int minor_version, struct phr_header *headers, int headers_len);

int http_check_close_connection(struct phr_header *headers, int num_headers);
int http_send_cgi_response(int sockfd, char *path, char *args, http_conf *config);
/********************/
/* PUBLIC FUNCTIONS */
/********************/

int http_process_request(int sockfd, http_conf *config) {
    //if(config == NULL) return -1;

    char buffer[MAX_REQUEST_SIZE];
    size_t buffer_len = 0;
    size_t prev_buffer_len;
    int parse_ret = 0;
    int read_ret;
    int send_ret = 0;
    int ret;
    int i;

    // Retornos del parseo
    struct phr_header headers[MAX_HEADERS_NUMBER];
    size_t num_headers = 0;
    int minor_version;
    const char *method;
    size_t method_len;
    const char *path;
    size_t path_len;
    char *file_path = NULL;
    int body_len = 0;
    char *body = NULL;

    // Si parse_ret > 0 exito en el parseo de la request
    while(parse_ret <= 0) {
        // Read request
        read_ret = http_read_request(sockfd, &buffer[buffer_len], sizeof(buffer) - buffer_len);
        if (read_ret < 0) {
            // Error: read
            return -1;
        }
        if (read_ret == 0) {
            // 0 bytes leidos
            return 2;
        }
        // Actualizamos longitudes
        prev_buffer_len = buffer_len;
        buffer_len += read_ret;

        // Parseamos
        num_headers = sizeof(headers) / sizeof(headers[0]);
        parse_ret = phr_parse_request(buffer, buffer_len, &method, &method_len, &path, &path_len,
                                 &minor_version, headers, &num_headers, prev_buffer_len);

        if (parse_ret == -1) {
            // Error: parse
            return http_send_error(sockfd, 400, config);
        }

        if (buffer_len == sizeof(buffer)) {
            return http_send_error(sockfd, 413, config);
        }
        // Si parse_ret no es > 0, pero no hay error, se sigue parseando
    }
    // Si el parseo ha sido un exito, tenemos los datos necesarios para saber a que funcion llamar

    // Obtener body si hay content length
    for (i = 0; i != num_headers; ++i) {
        if(strncmp(headers[i].name, "Content-Length", (int)headers[i].name_len) == 0) {
            body_len = atoi(headers[i].value);
            break;
        }
    }
    if(body_len > 0) {
        body = malloc(sizeof(char)*(body_len+1));
        if(body == NULL) {
            // Error: malloc
            return -1;
        }
        const char *next_body = &buffer[parse_ret];
        strncpy(body, next_body, body_len);
        body[body_len] = 0;
    }
    // Chequear cabeceras basicas correctas
    send_ret = http_init_response(sockfd, config, minor_version, headers, num_headers);

    file_path = malloc(sizeof(char)*((int)path_len + 1));
    if(file_path == NULL) {
        // Error: malloc
        return -1;
    }
    strncpy(file_path, path, (int)path_len);
    file_path[(int)path_len] = 0;

    if(strncmp(method, "GET", (int)method_len) == 0) {
        send_ret = http_send_get_response(sockfd, file_path, config);
    }
    else if(strncmp(method, "HEAD", (int)method_len) == 0) {
        send_ret = http_send_head_response(sockfd, file_path, config);
    }
    else if(strncmp(method, "OPTIONS", (int)method_len) == 0) {
        send_ret = http_send_options_response(sockfd, file_path, config);
    }
    else if(strncmp(method, "POST", (int)method_len) == 0) {
        send_ret = http_send_post_response(sockfd, file_path, body, body_len, config);
    }
    else {
        // Bad Request: 400
        send_ret = http_send_error(sockfd, 400, config);
    }
    if(file_path != NULL) free(file_path);
    if(body != NULL) free(body);
    if(send_ret < 0) {
        return -1;
    }
    ret = http_check_close_connection(headers, num_headers);
    if(ret == 1) {
        // keep-alive
        return 1;
    }
    if(ret == 2) {
        // close
        return 2;
    }
    return 2;
}

int http_init_response(int sockfd, http_conf *config, int minor_version, struct phr_header *headers, int headers_len) {
    if(headers == NULL) return -1;

    int i;
    int host_index = -1;
    char message[128] = {0};
    int len = 0;

    if(minor_version == 1) {
        // HTTP 1.1: requiere un 100 continue inicial y validación del host
        for(i = 0; i < headers_len; i++) {
            if(strncmp(headers[i].name, "Host", headers[i].name_len) == 0) {
                host_index = i;
                break;
            }
        }
        if(host_index < 0) {
            return http_send_error(sockfd, 400, config);
        }
        len += http_get_response_line(message, 128, 100);
        strcat(message, "\r\n");
        sockets_send_all(sockfd, message, len+2);
        return 0;
    }
    return 0;
}

int http_send_error(int sockfd, int code, http_conf *config) {
    if(config == NULL) return -1;

    FILE *fp = NULL;
    char headers[MAX_HEADERS_SIZE] = {0};
    long file_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;
    char tpath[MAX_PATH_SIZE] = {0};        //Path temporal
    char *path = NULL;                      //Path final

    // Obtener path al custom error message html
    path = http_get_error_doc(tpath, MAX_PATH_SIZE, code, config);
    if(path != NULL) {
        fp = fopen(path, "rb");
        if(fp == NULL) {
            path = NULL;
        }
    }

    headers_len = http_get_headers(headers, headers_max, code, fp, &file_len, path, config, NULL, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        if(fp != NULL) fclose(fp);
        return -1;
    }
    // Mandar error doc junto con el code adecuado en los headers
    sockets_send_all(sockfd, headers, headers_len);
    sockets_send_file(sockfd, fp, file_len);
    if(fp != NULL) fclose(fp);
    return 0;
}

int http_send_get_response(int sockfd, const char *rpath, http_conf *config) {
    if(config == NULL || rpath == NULL) return -1;

    FILE *fp = NULL;
    char headers[MAX_HEADERS_SIZE] = {0};
    long file_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;
    char path[MAX_PATH_SIZE] = {0};
    char **argv = NULL;
    int ret;

    // Formar path absoluto a partir del root y el path relativo
    strncat(path, config->root, MAX_PATH_SIZE-1);
    strncat(path, rpath, MAX_PATH_SIZE-1 - strlen(path));

    if(is_script_php(path) == true || is_script_python(path) == true) {
        // Ejecutar script y devolver resultado
        argv = get_args(path);
        if(argv == NULL) {
            return http_send_error(sockfd, 500, config);
        }
        ret = http_send_cgi_response(sockfd, argv[0], argv[1], config);
        free(argv);
        return ret;
    }

    fp = fopen(path, "rb");
    if(fp == NULL) {
        // Error: fopen
        if(errno == ENOENT) {
            // Error: 404 not found
            return http_send_error(sockfd, 404, config);
        }
        return -1;
    }

    headers_len = http_get_headers(headers, headers_max, 200, fp, &file_len, path, config, NULL, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        fclose(fp);
        if(error != 0) {
            // Custom error from headers
            return http_send_error(sockfd, error, config);
        }
        return -1;
    }

    sockets_send_all(sockfd, headers, headers_len);
    sockets_send_file(sockfd, fp, file_len);
    fclose(fp);
    return 0;
}

int http_send_head_response(int sockfd, const char *rpath, http_conf *config) {
    if(config == NULL || rpath == NULL) return -1;

    FILE *fp = NULL;
    char headers[MAX_HEADERS_SIZE] = {0};
    long file_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;

    char path[MAX_PATH_SIZE] = {0};

    // Formar path absoluto a partir del root y el path relativo
    strncat(path, config->root, MAX_PATH_SIZE-1);
    strncat(path, rpath, MAX_PATH_SIZE-1 - strlen(path));

    fp = fopen(path, "rb");
    if(fp == NULL) {
        // Error: fopen
        if(errno == ENOENT) {
            // Error: 404 not found
            return http_send_error(sockfd, 404, config);
        }
        return -1;
    }

    headers_len = http_get_headers(headers, headers_max, 200, fp, &file_len, path, config, NULL, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        fclose(fp);
        if(error != 0) {
            return http_send_error(sockfd, error, config);
        }
        return -1;
    }

    fclose(fp);
    sockets_send_all(sockfd, headers, headers_len);
    return 0;
}

int http_send_options_response(int sockfd, const char *rpath, http_conf *config) {
    if(config == NULL || rpath == NULL) return -1;

    char headers[MAX_HEADERS_SIZE] = {0};
    long file_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;
    struct stat fileStat;

    char path[MAX_PATH_SIZE] = {0};

    // Formar path absoluto a partir del root y el path relativo
    strncat(path, config->root, MAX_PATH_SIZE-1);
    strncat(path, rpath, MAX_PATH_SIZE-1 - strlen(path));

    if(stat(path, &fileStat) < 0) {
        // Error: stat
        if(errno == ENOENT) {
            // Error: 404 not found
            return http_send_error(sockfd, 404, config);
        }
        return -1;
    }

    headers_len = http_get_headers(headers, headers_max, 200, NULL, &file_len, NULL, config, &fileStat, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        if(error != 0) {
            return http_send_error(sockfd, error, config);
        }
        return -1;
    }

    sockets_send_all(sockfd, headers, headers_len);
    return 0;
}

int http_send_post_response(int sockfd, const char *rpath, char *body, int body_len, http_conf *config) {
    if(config == NULL || rpath == NULL) return -1;

    FILE *fp = NULL;
    char headers[MAX_HEADERS_SIZE] = {0};
    long file_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;

    char path[MAX_PATH_SIZE] = {0};

    // Formar path absoluto a partir del root y el path relativo
    strncat(path, config->root, MAX_PATH_SIZE-1);
    strncat(path, rpath, MAX_PATH_SIZE-1 - strlen(path));

    if(is_script_php(path) == true || is_script_python(path) == true) {
        // Ejecutar script php y devolver resultado
        return http_send_cgi_response(sockfd, path, body, config);
    }

    fp = fopen(path, "wb");
    if(fp == NULL) {
        // Error: fopen
        if(errno == ENOENT) {
            // Error: 404 not found
            return http_send_error(sockfd, 404, config);
        }
        return -1;
    }
    if (fwrite(body, body_len, 1, fp) != body_len) {
        fclose(fp);
        return http_send_error(sockfd, 500, config);
    }

    headers_len = http_get_headers(headers, headers_max, 200, fp, &file_len, path, config, NULL, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        fclose(fp);
        if(error != 0) {
            return http_send_error(sockfd, error, config);
        }
        return -1;
    }
    fclose(fp);
    sockets_send_all(sockfd, headers, headers_len);
    return 0;
}
/*********************/
/* PRIVATE FUNCTIONS */
/*********************/


/*********
* FUNCIÓN: int http_read_request(int sockfd, int sockfd, char *request)
* ARGS_IN:  int sockfd - socket del que leer la request
            char *request - String donde se guarda el resultado
            int request_len - Longitud maxima de request
* DESCRIPCIÓN: Lee de un socket la siguiente request, aunque cabe la posibilidad que no entera
* ARGS_OUT: int - Numero de chars leidos, retorno del read
            -1 si ha habido algun error
*********/
int http_read_request(int sockfd, char *request, int request_len) {
    if(request == NULL || request_len <= 0) return -1;

    int read_ret;   //lee el retorno

    // Guardamos a continuacion en request
    // Lo intentamos de nuevo si ha habido una interrupcion por señal
    do {
        read_ret = read(sockfd, request, request_len);
    } while(read_ret == -1 && errno == EINTR);

    // Error: IO
    if(read_ret < 0) {
        return -1;
    }
    return read_ret;
}

/*********
* FUNCIÓN: int http_get_headers_cgi(char *headers, int headers_max, int code, char *output, long *output_len, http_conf *config, int *error)
* ARGS_IN:  headers - puntero a la lista de headers
            headers_max - maxima longitud de los headers
            code - codigo http de respuesta
            output - puntero a la salida del script
            output_len - longitud de la salida
            config - configuracion del server
            error - en caso de error
* DESCRIPCIÓN: Obtiene los headers para una respuesta cgi
* ARGS_OUT: int - Longitud de los headers
*********/
int http_get_headers_cgi(char *headers, int headers_max, int code, char *output, long *output_len, http_conf *config, int *error) {

    int ret;
    int headers_len = 0;
    *error = 500;   // Server error por defecto

    // Respouesta
    ret = http_get_response_line(headers, headers_max, code);
    if(ret < 1 || ret >= headers_max) {
        // Error: response line
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;
    // Obtencion de headers
    // Vamos actualizando su tamaño para ir guardandolo en orden
    ret = http_get_header_date(&headers[headers_len], headers_max);
    if(ret < 1 || ret >= headers_max) {
        // Error: date
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    ret = http_get_header_content_length_string(&headers[headers_len], headers_max, output, output_len);
    if(ret < 1 || ret >= headers_max) {
        // Error: length
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    ret = http_get_header_server(&headers[headers_len], headers_max, config->signature);
    if(ret < 1 || ret >= headers_max) {
        // Error: server
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    ret = http_get_header_content_type(&headers[headers_len], headers_max, ".html");
    if(ret < 1 || ret >= headers_max) {
        // Error: type
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    // El último header necesita un CRLF extra
    ret = snprintf(&headers[headers_len], headers_max, "\r\n");
    if(ret < 1 || ret >= headers_max) {
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;
    return headers_len;
}

/*********
* FUNCIÓN: int http_get_headers(char *headers, int headers_max, int code, FILE *fp, long *file_len, char *path, http_conf *config, struct stat *stat, int *error)
* ARGS_IN:  headers - puntero a la lista de headers
            headers_max - maxima longitud de los headers
            code - codigo http de respuesta
            fp - puntero al recurso
            file_len - longitud del recurso
            path - path absoluto al recurso
            stat - stat del recurso
            config - configuracion del server
            error - en caso de error
* DESCRIPCIÓN: Obtiene los headers para una respuesta general
* ARGS_OUT: int - Longitud de los headers
*********/
int http_get_headers(char *headers, int headers_max, int code, FILE *fp, long *file_len, char *path, http_conf *config, struct stat *stat, int *error) {

    int ret;
    int headers_len = 0;
    *error = 500;   // Server error por defecto

    // Respuesta
    ret = http_get_response_line(headers, headers_max, code);
    if(ret < 1 || ret >= headers_max) {
        // Error: response line
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;
    // Obtencion de headers
    // Vamos actualizando su tamaño para ir guardandolo en orden
    ret = http_get_header_date(&headers[headers_len], headers_max);
    if(ret < 1 || ret >= headers_max) {
        // Error: date
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    ret = http_get_header_content_length_file(&headers[headers_len], headers_max, fp, file_len);
    if(ret < 1 || ret >= headers_max) {
        // Error: length
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;
    ret = http_get_header_server(&headers[headers_len], headers_max, config->signature);
    if(ret < 1 || ret >= headers_max) {
        // Error: server
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;

    // Si path es null no hay body, luego no se incluyen estas cabeceras
    if(path != NULL) {
        ret = http_get_header_last_modify(&headers[headers_len], headers_max, path);
        if(ret < 1 || ret >= headers_max) {
            // Error: modify
            return -1;
        }
        headers_len += ret;
        headers_max -= ret;
        ret = http_get_header_content_type(&headers[headers_len], headers_max, path);
        if(ret < 1 || ret >= headers_max) {
            // Error: type
            *error = 415;   // Unsopported Media Type
            return -1;
        }
        headers_len += ret;
        headers_max -= ret;
    }

    // Si stat no es null se trata de un OPTIONS y añadimos la cabecera Allow
    if(stat != NULL) {
        ret = http_get_header_allow(&headers[headers_len], headers_max, stat);
        if(ret < 1 || ret >= headers_max) {
            // Error: allow
            return -1;
        }
        headers_len += ret;
        headers_max -= ret;
    }

    // El último header necesita un CRLF extra
    ret = snprintf(&headers[headers_len], headers_max, "\r\n");
    if(ret < 1 || ret >= headers_max) {
        return -1;
    }
    headers_len += ret;
    headers_max -= ret;
    return headers_len;
}

int http_get_header_allow(char *header, int len, struct stat *stat) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Allow";
    char value[MAX_VALUE_SIZE] = "OPTIONS, HEAD, GET, POST";
    int ret;

    ret = snprintf(header, len, "%s: %s\r\n", name, value);
    return ret;
}
int http_get_header_date(char *header, int len) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Date";
    char value[MAX_VALUE_SIZE] = {0};
    int ret;

    // Obtener fecha para formato HTTP
    time_t now = time(0);
    struct tm time = *gmtime(&now);
    ret = strftime(value, sizeof(value), "%a, %d %b %Y %H:%M:%S %Z", &time);
    if(ret < 1) {
        // Error: ocupa demasiado
        return -1;
    }

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %s\r\n", name, value);
    return ret;
}
int http_get_header_last_modify(char *header, int len, char *path) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Last-modify";
    char value[MAX_VALUE_SIZE] = {0};
    int ret;

    // Obtener fecha de ultima modificacion
    struct stat stats;
    ret = stat(path, &stats);
    if(ret != 0) {
        // Error: fstat
        return -1;
    }
    // Convertir fecha a estandar GMT para HTTP
    struct tm time = *gmtime(&(stats.st_ctime));
    ret = strftime(value, sizeof(value), "%a, %d %b %Y %H:%M:%S %Z", &time);
    if(ret < 1) {
        // Error: ocupa demasiado
        return -1;
    }

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %s\r\n", name, value);
    return ret;
}
int http_get_header_server(char *header, int len, char *signature) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Server";
    char *value = signature;
    int ret;

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %s\r\n", name, value);
    return ret;
}
int http_get_header_content_length_string(char *header, int len, char *str, long *str_len) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Content-length";
    long value = 0;
    int ret;

    // Si fp == NULL es que no hay body
    if(str != NULL) {
        value = strlen(str);
    }
    *str_len = value;

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %ld\r\n", name, value);
    return ret;
}
int http_get_header_content_length_file(char *header, int len, FILE *fp, long *file_len) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Content-length";
    long value = 0;
    int ret;

    // Si fp == NULL es que no hay body
    if(fp != NULL) {
        // Obtener longitud del fichero
        fseek(fp, 0, SEEK_END);
        value = ftell(fp);
        fseek(fp, 0, SEEK_SET);
    }
    *file_len = value;

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %ld\r\n", name, value);
    return ret;
}
int http_get_header_content_type(char *header, int len, char *path) {
    if(len < 1 || header==NULL) return -1;

    const char *name = "Content-type";
    char value[128] = {0};
    int ret;
    char *extension = NULL;

    // Obtener extension del fichero pedido (.html, .txt, ...)
    extension = strrchr(path, '.');
    if(extension==NULL) {
        // Error: invalid type
        return -1;
    }
    // Obtener formato http
    if(strcmp(".txt", extension) == 0) {
        snprintf(value, sizeof(value), "text/plain");
    }
    else if(strcmp(".htm", extension) == 0 || strcmp(".html", extension) == 0) {
        snprintf(value, sizeof(value), "text/html");
    }
    else if(strcmp(".gif", extension) == 0) {
        snprintf(value, sizeof(value), "image/gif");
    }
    else if(strcmp(".jpg", extension) == 0 || strcmp(".jpeg", extension) == 0) {
        snprintf(value, sizeof(value), "image/jpeg");
    }
    else if(strcmp(".mpg", extension) == 0 || strcmp(".mpeg", extension) == 0) {
        snprintf(value, sizeof(value), "video/mpeg");
    }
    else if(strcmp(".doc", extension) == 0 || strcmp(".docx", extension) == 0) {
        snprintf(value, sizeof(value), "application/msword");
    }
    else if(strcmp(".pdf", extension) == 0) {
        snprintf(value, sizeof(value), "application/pdf");
    }
    else {
        // Error: invalid type
        return -1;
    }

    // Combinar para obtener el header
    ret = snprintf(header, len, "%s: %s\r\n", name, value);
    return ret;
}

char* http_get_error_doc(char *path, int len, int code, http_conf *config) {
    if(path == NULL || config == NULL) return NULL;

    // Rellenamos en path la localizacion del fichero
    strncat(path, config->root, len-1);
    len -= strlen(path);

    if(code == 400) {
        if(config->doc_code_400 == NULL) return NULL;
        return strncat(path, config->doc_code_400, len-1);
    }
    if(code == 404) {
        if(config->doc_code_404 == NULL) return NULL;
        return strncat(path, config->doc_code_404, len-1);
    }
    return NULL;
}

int http_get_response_line(char *header, int len, int code) {
    int ret;

    if(code == 100) {
        ret = snprintf(header, len, "HTTP/1.1 100 Continue\r\n");
        return ret;
    }
    if(code == 200) {
        ret = snprintf(header, len, "HTTP/1.1 200 OK\r\n");
        return ret;
    }
    if(code == 400) {
        ret = snprintf(header, len, "HTTP/1.1 400 Bad Request\r\n");
        return ret;
    }
    if(code == 404) {
        ret = snprintf(header, len, "HTTP/1.1 404 Not Found\r\n");
        return ret;
    }
    if(code == 413) {
        ret = snprintf(header, len, "HTTP/1.1 413 Payload Too Large\r\n");
        return ret;
    }
    if(code == 415) {
        ret = snprintf(header, len, "HTTP/1.1 415 Unsupported Media Type\r\n");
        return ret;
    }
    if(code == 500) {
        ret = snprintf(header, len, "HTTP/1.1 500 Server Error\r\n");
        return ret;
    }
    if(code == 501) {
        ret = snprintf(header, len, "HTTP/1.1 501 Not Implemented\r\n");
        return ret;
    }
    return -1;
}

/*********
* FUNCIÓN: int http_get_headers(char *headers, int headers_max, int code, FILE *fp, long *file_len, char *path, http_conf *config, struct stat *stat, int *error)
* ARGS_IN:  headers - puntero a la estructura de headers
            num_headers - numero de headers
* DESCRIPCIÓN: Comprueb el header connection para keep-alive
* ARGS_OUT: int - 1 - kee-alive
                  2 - close
                  0 - close (not specified)
*********/
int http_check_close_connection(struct phr_header *headers, int num_headers) {
    if(headers == NULL || num_headers < 1) return -1;

    int i = 0;
    const char *keep = "keep-alive";
    const char *close = "close";

    for (i = 0; i != num_headers; ++i) {
        if(strncmp(headers[i].name, "Connection", (int)headers[i].name_len) == 0) {
            if(strncmp(headers[i].value, keep, (int)headers[i].value_len) == 0) {
                //Keep alive
                return 1;
            }
            if(strncmp(headers[i].value, close, (int)headers[i].value_len) == 0) {
                //close
                return 2;
            }
            return 1;
        }
    }
    return 0;
}

/*********
* FUNCIÓN: int http_send_cgi_response(int sockfd, char *path, char *args, http_conf *config)
* ARGS_IN:  sockfd - socket al que enviar la respuesta
            path - path del script
            args - args para el script
            config - configuracion del server
* DESCRIPCIÓN: Envia una respuesta cgi
* ARGS_OUT: int - control de errores
*********/
int http_send_cgi_response(int sockfd, char *path, char *args, http_conf *config) {
    if(config == NULL || path == NULL) return -1;

    char *output = NULL;
    char headers[MAX_HEADERS_SIZE] = {0};
    long output_len;
    int headers_len = 0;
    int headers_max = MAX_HEADERS_SIZE;
    int error = 0;

    output = exe_script_http(path, args);
    if(output == NULL) {
        return http_send_error(sockfd, 500, config);
    }
    // Tenemos en output la salida del script
    // Formamos respuesta que tenga como cuerpo dicha salida en formato html

    headers_len = http_get_headers_cgi(headers, headers_max, 200, output, &output_len, config, &error);
    if(headers_len < 1 || headers_len >= headers_max) {
        // Error: headers
        free(output);
        if(error != 0) {
            // Custom error from headers
            return http_send_error(sockfd, error, config);
        }
        return -1;
    }

    sockets_send_all(sockfd, headers, headers_len);
    sockets_send_all(sockfd, output, output_len);
    free(output);
    return 0;
}
