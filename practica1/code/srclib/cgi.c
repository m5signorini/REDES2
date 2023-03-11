#include "cgi.h"
#define NARGS 2
#define MAX_STR 128
#define MAX_LINE 1024
#define MAX_HEADERS_SIZE 8192
#define MAX_OUTPUT 10000

bool is_script_python(const char *path) {
    char *extension, *check;
    const char pt = '.';
    char parse[64];

    //Comprobamos si la extension es .py
    extension = strrchr(path, pt);
    strcpy(parse, extension);
    check = strtok(parse, "?");
    if (strcmp(check, ".py") == 0)
        return true;

    return false;
}


bool is_script_php(const char *path) {
    char *extension, *check;
    const char pt = '.';
    char parse[64];

    //Comprobamos si la extension es .php
    extension = strrchr(path, pt);
    strcpy(parse, extension);
    check = strtok(parse, "?");
    if (strcmp(check, ".php") == 0)
        return true;

    return false;
}


char** get_args(const char *path) {
    char *parse;
    char **args;

    //Reservamos memoria para los argumentos
    parse = malloc(sizeof(char)*128);
    args = (char**) malloc(NARGS * sizeof(char*));

    //Guardamos el nombre en args[0]
    strncpy(parse, path, 128);
    args[0] = strtok(parse, "?");

    //Los argumentos estan despues de ?
    if ((args[1] = strtok(NULL, "?")) == NULL) {
        printf("No arguments\n");
    }

    return args;
}


char* exe_script(const char *path, char *args, char *interpreter) {
    char *res = "";
    char call[MAX_STR] = "";
    size_t size = strlen(path) + strlen(args);
    int in_pipe[2], out_pipe[2];
    pid_t pid;
    char *buf = NULL;
    int ret;

    buf = malloc(sizeof(char)*MAX_OUTPUT);
    if(buf == NULL) {
        return NULL;
    }

    snprintf(call, size, "%s %s %s", interpreter, path, args);
    fflush(stdout);

    pipe(in_pipe);
    pipe(out_pipe);

    if ( (pid = fork() ) == 0) { // Child
        //Redirige stdin a in_pipe[0] y stdout a out_pipe[1]
        dup2(in_pipe[0], STDIN_FILENO);
        dup2(out_pipe[1], STDOUT_FILENO);

        //Cierra los extremos no usados de las tuberías
        close(out_pipe[0]);
        close(in_pipe[1]);

        //Ejecuta el script
        execlp("/bin/sh","/bin/sh", "-c", call, NULL);
        exit(0);
    }
    else { // Padre
        //Cierra los extremos no usados de las tuberías
        close(out_pipe[1]);
        close(in_pipe[0]);

        //escribe los argumentos y lee los resultados
        if (args != NULL)
            write(in_pipe[1], args, strlen(args));
        ret = read(out_pipe[0], buf, MAX_OUTPUT);
        memset(&buf[ret], 0, MAX_OUTPUT-ret);
        wait(NULL);
    }

    res = buf;
    return res;
}


char* exe_script_http(char *path, char *args) {
    if(is_script_python(path) == true) {
        return exe_script(path, args, "python3");
    }
    if(is_script_php(path) == true) {
        return exe_script(path, args, "php");
    }
    return NULL;
}
