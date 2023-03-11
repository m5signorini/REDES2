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

#define SERVER_PORT 8080
#define NCHILDREN 1
#define NLOOPS 1

int main(int argc, char **argv) {

    int sockfd[NCHILDREN], i, j;
    struct sockaddr_in server_addr;
    char buffer[1024] = {0};
    pid_t pid;
    char* hello = "GET /index.html HTTP/1.1\r\nHost: example.com\r\nCookie: \r\n\r\n";

    server_addr.sin_family = AF_INET;           /* Protocolo TCP/IP */
    server_addr.sin_port = htons(SERVER_PORT);  /* Asignar puerto (poner bytes en orden de red) */

    // Convierte direcciones IPv4 e IPv6 de texto en una estructura de dirección de red
    if(inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr) <= 0) {
        perror("invalid address");
        exit(EXIT_FAILURE);
    }

    for (i = 0; i < NCHILDREN; i++) {
        if ( (pid = fork()) == 0) { /* child */
            for (j = 0; j < NLOOPS; j++) {

                //abre el socket
                if((sockfd[i] = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
                    perror("socket initialization failed");
                    exit(EXIT_FAILURE);
                }

                //conexión con el servidor
                if(connect(sockfd[i], (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
                    perror("connection failed");
                    exit(EXIT_FAILURE);
                }

                /* envía mensaje al servidor y lee su respuesta */
                send(sockfd[i], hello, strlen(hello), 0);
                printf("Enviado\n");
                read(sockfd[i], buffer, 1024);
                fprintf(stdout, "%s\n", buffer);
                close(sockfd[i]);
            }

        printf("child %d done\n", i);
        exit(0);
        }
    /* el padre vuelve al bucle para hacer fork() otra vez */
    }

    while (wait(NULL) > 0)     /* espera a todos los hijos */
        ;

    if (errno != ECHILD)
        perror("wait error");


    return 0;
}
