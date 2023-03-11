#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>

#include <netinet/in.h>
#include <arpa/inet.h>

#ifndef _SOCKETS
#define _SOCKETS


/*********
* FUNCIÓN: int sockets_init_tcp_socket()
* ARGS_IN:
* DESCRIPCIÓN: Inicia y devuelve un stream socket orientado a tcp.
    En particular envuelve una llamada a socket(AF_INET, SOCK_STREAM, 0)
* ARGS_OUT: int - Descriptor del socket iniciado
*********/
int sockets_init_tcp_socket();

/*********
* FUNCIÓN: int sockets_bind_tcp_socket()
* ARGS_IN:  int sockfd - Socket previamente inicializado
            int port - Numero de puerto ha vincular con el socket
* DESCRIPCIÓN: Registra un stream socket para TCP en un puerto
* ARGS_OUT: int - Retorno de la funcion interna bind().
            0 si no ha habido error, -1 en caso de error
*********/
int sockets_bind_tcp_socket(int sockfd, int port);

/*********
* FUNCIÓN:  int sockets_listen(int sockfd, int max_connections)
* ARGS_IN:  int sockfd - Socket previamente inicializado
            int max_connections - Numero maximo de conexiones
* DESCRIPCIÓN: Dispone el socket a atender llamadas
* ARGS_OUT: int - Retorno de la funcion interna listen().
            0 si no ha habido error, -1 en caso de error
*********/
int sockets_listen(int sockfd, int max_connections);

/*********
* FUNCIÓN:  int sockets_accept_connection(int sockfd)
* ARGS_IN:  int sockfd - Socket previamente inicializado y esuchando
* DESCRIPCIÓN: El socket acepta una conexion pendiente o espera a que llegue una.
    Nótese, que el uso de esta función requiere un socket pasivo, por ejemplo,
    el retorno de una llamada a sockets_start_passive_tcp_socket()
* ARGS_OUT: int - Retorno de la funcion interna accept().
    Un descriptor de fichero del socket aceptado, -1 en caso de error
*********/
int sockets_accept_connection(int sockfd);

/*********
* FUNCIÓN:  int sockets_close(int sockfd)
* ARGS_IN:  int sockfd - Socket previamente creado
* DESCRIPCIÓN: El socket pasado se cierra.
* ARGS_OUT: int - Retorno de la funcion interna close().
            0 si no ha habido error, -1 en caso de error
*********/
int sockets_close(int sockfd);

/*********
* FUNCIÓN:  int sockets_start_passive_tcp_socket()
* ARGS_IN:  int port - Numero de puerto ha vincular con el socket
            int max_connections - Numero maximo de conexiones, se espera >0
* DESCRIPCIÓN: Inicia un stream socket para TCP, lo registra en un puerto y lo dispone a
    recibir llamadas. Basicamente envuelve la secuencia socket() - bind() - listen()
* ARGS_OUT: int - Descriptor del socket iniciado, -1 en caso de error
*********/
int sockets_start_passive_tcp_socket(int port, int max_connections);

/*********
* FUNCIÓN:  int sockets_send_all(int sockfd, void *buffer, size_t length)
* ARGS_IN:  int sockfd - Puerto ha enviar el buffer
            void* buffer - Datos a enviar
            size_t length - Longitud del buffer a enviar
* DESCRIPCIÓN: Dado un puerto ya conectado por el que se pueda enviar informacion
    con send, realiza llamadas a send hasta enviar todo el buffer, pues send no
    asegura poder enviar todo lo que se le pide en una sola llamada.
* ARGS_OUT: int - Posible codigo de error en la llamada a send
            0 si no ha habido error, -1 en caso de error
*********/
int sockets_send_all(int sockfd, void *buffer, size_t length);

/*********
* FUNCIÓN:  int sockets_send_file(int sockfd, FILE *fp, int file_len)
* ARGS_IN:  int sockfd - Puerto ha enviar el buffer
            FILE* fp - fichero a enviar
            int file_len - Longitud del fichero
* DESCRIPCIÓN: Dado un puerto ya conectado por el que se pueda enviar informacion
    con send, realiza llamadas a send hasta enviar todo el fichero.
* ARGS_OUT: int - Posible codigo de error en la llamada a send
            0 si no ha habido error, -1 en caso de error
*********/
int sockets_send_file(int sockfd, FILE *fp, int file_len);
#endif /* _SOCKETS */
