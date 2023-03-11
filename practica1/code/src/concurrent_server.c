#include "sockets.h"
#include "confuse.h"
#include "picohttpparser.h"
#include "http.h"

int main(int argc, char **argv) {
    int i = 0;
    int listenfd, accfd;
    pid_t pid;
    char *server_root = NULL;
    char *server_signature = NULL;
    char *doc_error_400 = NULL;
    char *doc_error_404 = NULL;
    int max_clients;
    int listen_port;
    http_conf *httpcfg;

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

    /* Inicia el servidor */
    listenfd = sockets_init_tcp_socket();

    if (sockets_bind_tcp_socket(listenfd, listen_port) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    printf("%s ready to receive\n", server_signature);    //Avisa al cliente

    /* Queda a la escucha */
    if (sockets_listen(listenfd, max_clients) < 0) {
        perror("listening failed");
        exit(EXIT_FAILURE);
    }


    /* Acepta conexiones */
    while(i < max_clients) {
        accfd = sockets_accept_connection(listenfd);
        /* Procesa la petición */

        if ( (pid = fork()) == 0) { /* child */
            http_process_request(accfd, httpcfg);
            printf("Recibido\n");
            /* Fin del procesado */
            exit(0);
        }

        close(accfd);
        i++;
    }


    /* Espera a todos los hijos */
    while (wait(NULL) > 0) 
        ;
        
    if (errno != ECHILD)
        perror("wait error");


    /* Libera recursos */
    sockets_close(listenfd);
    free(server_signature);
    free(server_root);
    cfg_free(cfg);
    free(httpcfg);

    return 0;
}
