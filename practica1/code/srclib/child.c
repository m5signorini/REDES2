#include "child.h"

void child_main(int i, int listenfd, http_conf *httpcfg) {
    int accfd;
    int ret;

    printf("Child %d starting\n", i);
    for( ; ; ) {
        accfd = sockets_accept_connection(listenfd);

        ret = http_process_request(accfd, httpcfg);
        while(ret == 1) {
            ret = http_process_request(accfd, httpcfg);
        }
        /* Fin del procesado de la petición */
        sockets_close(accfd);
    }
}

void sig_int(int nchildren, pid_t *pids) {
    int i;

    /* Acaba con todos los hijos */
    for (i = 0; i < nchildren; i++)
        kill(pids[i], SIGTERM);

    /* Espera a todos los hijos */
    while (wait(NULL) > 0)
        ;

    if (errno != ECHILD)
        perror("wait error");

    exit(0);
}
