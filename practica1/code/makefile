##################

CC = gcc -g -Wall -pedantic -Iinclude -lconfuse#-L./lib/
INC = ./include/
LIB = ./lib/
OBJ = ./obj/
SRC = ./src/
SRCLIB = ./srclib/
EXE = concurrent_server test_client fork_pool_server
##################
.PHONY: clean

all: $(EXE)

concurrent_server: $(OBJ)concurrent_server.o $(LIB)libhttpserver.a#$(OBJ)sockets.o $(OBJ)picohttpparser.o $(OBJ)http.o $(OBJ)cgi.o
	$(CC) -o $@ $^ -lconfuse -L$(LIB) -lhttpserver

fork_pool_server: $(OBJ)fork_pool_server.o $(OBJ)child.o  $(LIB)libhttpserver.a#$(OBJ)sockets.o $(OBJ)picohttpparser.o $(OBJ)http.o $(OBJ)cgi.o
	$(CC) -o $@ $^ -lconfuse -L$(LIB) -lhttpserver

test_client: $(OBJ)test_client.o
	$(CC) -o $@ $^

# OBJECTS
$(OBJ)server.o: $(SRC)server.c
	$(CC) -c $< -o $@

$(OBJ)concurrent_server.o: $(SRC)concurrent_server.c $(INC)sockets.h
	$(CC) -c $< -o $@

$(OBJ)fork_pool_server.o: $(SRC)fork_pool_server.c $(INC)sockets.h $(INC)child.h
	$(CC) -c $< -o $@

$(OBJ)test_client.o: $(SRC)test_client.c
	$(CC) -c $< -o $@

$(OBJ)sockets.o: $(SRCLIB)sockets.c $(INC)sockets.h
	$(CC) -c $< -o $@

$(OBJ)child.o: $(SRCLIB)child.c $(INC)child.h
	$(CC) -c $< -o $@

$(OBJ)cgi.o: $(SRCLIB)cgi.c $(INC)cgi.h
	$(CC) -c $< -o $@

$(OBJ)http.o: $(SRCLIB)http.c $(INC)http.h $(SRCLIB)sockets.c $(INC)sockets.h $(SRCLIB)cgi.c $(INC)cgi.h $(SRCLIB)picohttpparser.c $(INC)picohttpparser.h
	$(CC) -c $< -o $@

$(OBJ)picohttpparser.o: $(SRCLIB)picohttpparser.c $(INC)picohttpparser.h
	$(CC) -c $< -o $@

# LIBRARY
$(LIB)libhttpserver.a: $(OBJ)picohttpparser.o $(OBJ)http.o $(OBJ)sockets.o $(OBJ)cgi.o
	mkdir -p ./lib/
	ar rcs $@ $^

clean:
	rm -f $(EXE)
	rm -f obj/*.o

clear: clean
	rm -f lib/*.a
