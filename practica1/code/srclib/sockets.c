#include "sockets.h"

#define MAX_SEND 8096

int sockets_init_tcp_socket() {
    int sockfd;
    // Usamos AF_INET para IPv4
    // Usamos SOCK_STREAM para facilitar conexion
    // Podemos usar protocol=0 en general
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if(sockfd < 0) {
        //perror("socket initialization failed");
        return -1;
    }
    // Usamos SO_REUSEADDR para no esperar que linux lo cierre
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &(int){1}, sizeof(int)) < 0) {
        perror("setsockopt(SO_REUSEADDR) failed");
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_KEEPALIVE, &(int){1}, sizeof(int)) < 0) {
        perror("setsockopt(SO_KEEPALIVE) failed");
    }
    return sockfd;
}

int sockets_bind_tcp_socket(int sockfd, int port) {
    struct sockaddr_in address;

    address.sin_family = AF_INET;           /* TCP/IP protocol */
    address.sin_addr.s_addr = INADDR_ANY;   /* Aceptar cualquiera */
    address.sin_port = htons(port);  /* Asignar puerto (poner bytes en orden de red) */

    /* Bind socket to actual address */
    if (bind(sockfd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        //perror("bind failed");
        return -1;
    }
    return 0;
}

int sockets_listen(int sockfd, int max_connections) {
    if(max_connections < 0) return -1;
    return listen(sockfd, max_connections);
}

int sockets_accept_connection(int sockfd) {
    int fd, len;
    struct sockaddr address;    /* Rellenado tras aceptar conexion con cliente */
    len = sizeof(address);      /* Poner al tamaño de la estructura 'siempre' */

    // Llamada bloqueante hasta haber conexion en la cola
    if((fd = accept(sockfd, &address, (socklen_t *)&len)) < 0) {
        //perror("accept failed");
        return -1;
    }
    // La request no se procesa aqui, usar este descriptor para ello en otra funcion
    return fd;
}

int sockets_close(int sockfd) {
    return close(sockfd);
}

int sockets_start_passive_tcp_socket(int port, int max_connections) {
    int sockfd;
    // INIT
    if((sockfd = sockets_init_tcp_socket()) < 0) {
        perror("socket initialization failed");
        return -1;
    }

    // BIND
    if(sockets_bind_tcp_socket(sockfd, port) < 0) {
        perror("bind failed");
        return -1;
    }

    // LISTEN
    if (sockets_listen(sockfd, max_connections) < 0) {
        perror("listening failed");
        return -1;
    }

    return sockfd;
}

int sockets_send_all(int sockfd, void *buffer, size_t length) {
    if(buffer == NULL) return -1;

    char *ptr = (char*) buffer;
    int sent = 0;

    while(length > 0) {
        sent = send(sockfd, ptr, length, 0);
        if(sent < 1) {
            return -1;
        }
        ptr += sent;
        length -= sent;
    }
    return 0;
}

int sockets_send_file(int sockfd, FILE *fp, int file_len) {
    int sent;
    char buf[MAX_SEND];

    while(file_len > 0) {
        sent = fread(buf, 1, MAX_SEND, fp);
        if(sent < 1) {
            // Error: fread
            return -1;
        }
        if(sockets_send_all(sockfd, buf, MAX_SEND) != 0) {
            // Error: send
            return -1;
        }
        file_len -= sent;
    }

    return 0;
}
