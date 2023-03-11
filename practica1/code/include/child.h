#include "sockets.h"
#include "http.h"
#ifndef _CHILD
#define _CHILD

/*********
* FUNCIÓN: void child_main(int i, int listenfd)
* ARGS_IN: int i - Numero de hijo
    int listenfd - Socket previamente inicializado y esuchando
* DESCRIPCIÓN: Bucle infinito ejecutado por cada hijo del pool
    hasta ser detenido por el padre. Acepta conexiones y las procesa.
* ARGS_OUT:
*********/
void child_main(int i, int listenfd, http_conf *httpcfg);

/*********
* FUNCIÓN: void sig_int(int nchildren, pid_t *pids)
* ARGS_IN: int nchildren - Numero de hijos creados
    pid_t *pids - array con los pid de los hijos
* DESCRIPCIÓN: Manejador de la señal SIGINT. Termina con
    todos los hijos y los espera
* ARGS_OUT:
*********/
void sig_int(int nchildren, pid_t *pids);
#endif
