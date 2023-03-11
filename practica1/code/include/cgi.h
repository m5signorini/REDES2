#include "sockets.h"
#include <stdbool.h>
#ifndef _CGI
#define _CGI

/*********
* FUNCIÓN: bool is_script_python(const char *path)
* ARGS_IN: const char *path - path hasta el archivo a comprobar
* DESCRIPCIÓN: Comprueba si un path corresponde a un script en python o no
* ARGS_OUT: bool
*********/
bool is_script_python(const char *path);

/*********
* FUNCIÓN: bool is_script_php(const char *path)
* ARGS_IN: const char *path - path hasta el archivo a comprobar
* DESCRIPCIÓN: Comprueba si un path corresponde a un script en php o no
* ARGS_OUT: bool
*********/
bool is_script_php(const char *path);

/*********
* FUNCIÓN: char** get_args(const char *path);
* ARGS_IN: const char *path - path recibido incluyendo argumentos cgi
* DESCRIPCIÓN: Obtiene los argumentos a partir del path
* ARGS_OUT: lista de argumentos
*********/
char** get_args(const char *path);

/*********
* FUNCIÓN: char** get_args(const char *path);
* ARGS_IN: const char *path - path del script
           char * args - argumentos
* DESCRIPCIÓN: Ejecuta el script
* ARGS_OUT: Salida del script
*********/
char* exe_script_http(char *path, char *args);

#endif
