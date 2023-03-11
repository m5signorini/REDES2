#include "sockets.h"
#include "child.h"
#include "confuse.h"
#include <pthread.h>

int main(int argc, char **argv) {
    int i = 0;
    int listenfd;
    pid_t pid_aux;
    struct sigaction actint;
    int nchildren;
    pid_t *pids;
    char *server_root = NULL;
    char *server_signature = NULL;
    char *doc_error_400 = NULL;
    char *doc_error_404 = NULL;
    int max_clients;
    int listen_port;
    http_conf *httpcfg;

    if (argc < 2) {
        perror("usage: fork_pool_server <nchildren>");
        exit(EXIT_FAILURE);
    }

    nchildren = atoi(argv[1]);
    if (nchildren < 1) {
        perror("insufficient number of children");
        exit(EXIT_FAILURE);
    }

    pids = calloc(nchildren, sizeof(pid_t));

    /* Lee el archivo de configuracion */
    cfg_opt_t opts[] = {
        CFG_SIMPLE_STR("server_root", &server_root),
        CFG_INT("max_clients", 0, CFGF_NONE),
        CFG_INT("listen_port", 0, CFGF_NONE),
        CFG_SIMPLE_STR("server_signature", &server_signature),
        CFG_SIMPLE_STR("doc_code_400", &doc_error_400),
        CFG_SIMPLE_STR("doc_code_404", &doc_error_404),
        CFG_END()
    };
    cfg_t *cfg;

    cfg = cfg_init(opts, 0);
    if (cfg_parse(cfg, "server.conf") == CFG_PARSE_ERROR) {
        perror("cfg_parsing failed");
        exit(EXIT_FAILURE);
    }

    max_clients = cfg_getint(cfg, "max_clients");
    listen_port = cfg_getint(cfg, "listen_port");

    httpcfg = malloc(sizeof(http_conf));
    if (httpcfg == NULL) {
        perror("http_conf failed");
        exit(EXIT_FAILURE);
    }

    httpcfg->root = server_root;
    httpcfg->signature = server_signature;
    httpcfg->doc_code_400 = doc_error_400;
    httpcfg->doc_code_404 = doc_error_404;

    //Abrimos el socket
    listenfd = sockets_init_tcp_socket();

    if (sockets_bind_tcp_socket(listenfd, listen_port) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    printf("%s ready to receive\n", server_signature);    //Avisa al cliente

    if (sockets_listen(listenfd, max_clients) < 0) {
        perror("listening failed");
        exit(EXIT_FAILURE);
    }

    for (i = 0; i < nchildren; i++)
    {
        pid_aux = fork();

        if (pid_aux != 0)
            pids[i] = pid_aux;

        else if (pid_aux == 0) /* child */
            child_main(i, listenfd, httpcfg);
    }

    /*manejador señal SIGINT*/
    sigfillset(&(actint.sa_mask));
    actint.sa_flags = 0;

    /* Se arma la señal SIGINT. */
    actint.sa_handler = sig_int;
    if (sigaction(SIGINT, &actint, NULL) < 0)
    {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }

    for( ; ; )
        pause();

    free(server_signature);
    free(server_root);
    cfg_free(cfg);
    free(httpcfg);
}
