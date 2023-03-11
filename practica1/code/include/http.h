#ifndef _HTTP
#define _HTTP

// Por defecto los errores no devuelven contenido, pero se pueden
// especificar ficheros para usarlo como respuesta
typedef struct http_conf {
    char *signature;    // Server signature
    char *root;         // Root path

    char *doc_code_400; // Path relativo a root para html respuesta ante error 400
    char *doc_code_404; // Path relativo a root para html respuesta ante error 404
} http_conf;

/*********
* FUNCIÓN:  int http_process_request(int sock, http_conf *config);
* ARGS_IN:  int sock - socket donde leer la peticion
            http_conf *config - puntero a la variable de la configuracion del server
* DESCRIPCIÓN: Dado un puerto y una configuracion lee la siguiente peticion http y
        la procesa.
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
            1 para continuar abierta la conexion
            2 si se cierra la conexion
*********/
int http_process_request(int sock, http_conf *config);

/*********
* FUNCIÓN:  int http_send_get_response(int sockfd, const char *rpath, http_conf *config);
* ARGS_IN:  int sock - socket donde enviar la respuesta
            rpath - path relativo del recurso a devolver
            config - configuracion del server
* DESCRIPCIÓN: Envia una respuesta GET
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
*********/
int http_send_get_response(int sockfd, const char *rpath, http_conf *config);

/*********
* FUNCIÓN:  int http_send_head_response(int sockfd, const char *rpath, http_conf *config);
* ARGS_IN:  int sock - socket donde enviar la respuesta
            rpath - path relativo del recurso a devolver
            config - configuracion del server
* DESCRIPCIÓN: Envia una respuesta HEAD
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
*********/
int http_send_head_response(int sockfd, const char *rpath, http_conf *config);

/*********
* FUNCIÓN:  int http_send_options_response(int sockfd, const char *rpath, http_conf *config);
* ARGS_IN:  int sock - socket donde enviar la respuesta
            rpath - path relativo del recurso a devolver
            config - configuracion del server
* DESCRIPCIÓN: Envia una respuesta OPTIONS
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
*********/
int http_send_options_response(int sockfd, const char *rpath, http_conf *config);

/*********
* FUNCIÓN:  int http_send_post_response(int sockfd, const char *rpath, char *body, int body_len, http_conf *config);
* ARGS_IN:  int sock - socket donde enviar la respuesta
            rpath - path relativo del recurso a devolver
            config - configuracion del server
            body - datos a enviar
            body_len - longitud de dichos datos
* DESCRIPCIÓN: Envia una respuesta POST
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
*********/
int http_send_post_response(int sockfd, const char *rpath, char *body, int body_len, http_conf *config);

/*********
* FUNCIÓN:  int http_send_error(int sockfd, int code, http_conf *config);
* ARGS_IN:  int sock - socket donde enviar la respuesta
            code - codigo a devolver
            config - configuracion del server
* DESCRIPCIÓN: Envia un condigo de error HTTP
* ARGS_OUT: int - Control de errores
            0 si no ha habido error
            -1 si ha habido algun error
*********/
int http_send_error(int sockfd, int code, http_conf *config);

#endif
