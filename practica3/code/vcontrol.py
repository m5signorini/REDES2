"""


"""
import select
import socket
import sys
import numpy as np
from practica3_client import VideoClient

TIMEOUT_SECS = 20

class VideoControl(object):
    def __init__(self, myaddress, client):

        self.myaddress = myaddress
        self.client = client
        self.listen_sock = None
        self.sender_sock = None
        self._running = False
        self.connection = None
        self.init_control_listener()
        return

    def end_thread(self):
        """ Detiene el thread
        """
        self._running = False
        try:
            closer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            closer.connect(self.myaddress)
            closer.close()
            self.listen_sock.close()
        finally:
            self.listen_sock = None
        return

    def start_thread(self):
        """ Comienza el thread
        """
        self._running = True
        self.receive_control()
        return

    def init_control_listener(self):
        """ Inicializa el socket de escucha de comandos de control.
        Devuelve el socket inicializado, preparado para escuchar.
        """
        # Creamos socket para recibir comandos
        if self.listen_sock:
            self.listen_sock.close()
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind(self.myaddress)
        self.listen_sock.listen(1)
        return self.listen_sock

    def init_control_sender(self, address):
        """ Inicializa un socket conectado al de escucha de control del otro usuario.
        Dada la direccion del otro usuario, se conecta al dicho para el
        envio de comandos de control.
        Devuelve socket ya conectado, preparado para enviar.
        """
        # Creamos socket conectado
        if self.sender_sock:
            self.sender_sock.close()
        self.sender_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sender_sock.settimeout(10)
        try:
            self.sender_sock.connect(address)
            self.sender_sock.settimeout(None)
        except:
            self.sender_sock = None
            return None
        self.sender_sock.setblocking(False)
        return self.sender_sock

    def receive_control(self):
        """ Recibe y procesa los comandos de control.
        Dado un socket inicilizado para la escuha, acepta las
        conexiones a dicho socket, esperando recibir comandos de control.
        Los procesa y vuelve a esperar otra conexion indefinidamente.
        """
        while self._running:
            # Esperar por una conexion
            self.connection, address = self.listen_sock.accept()
            try:
                # Una vez conectado intenta leer y procesar constantemente
                while True:
                    data = self.connection.recv(1024)
                    # Procesar datos
                    if data:
                        print('received {!r}'.format(data))
                        self.process_control(data)
                    else:
                        print('connection closed by peer')
                        break
            except:
                print('exception')
            finally:
                self.connection.close()
                self.connection = None
        return

    # ENVIAR PETICIONES DE COMANDOS
    def send_control(self, command, expect_response=False):
        """ Envia un comando de control.
        Dado un socket ya conectado al usuario destino, envia el
        comando especificado, y en caso de esperar respuesta la
        devuelve una vez recibida.
        """
        response = None
        # Enviar comando
        try:
            self.sender_sock.sendall(command.encode())
        except:
            print('Error al enviar comando {0} al servidor'.format(command))
            return None
        # Recibir respuesta
        if expect_response:
            response = bytearray()
            try:
                while True:
                    ready = select.select([self.sender_sock],[],[], TIMEOUT_SECS)
                    if ready[0]:
                        data = self.sender_sock.recv(1024)
                        if data:
                            # Solo leemos una vez la respuesta
                            response.extend(data)
                            return response
                        else:
                            break
                    else:
                        break
                    # Finalizar bucle si no hay más datos que leer
            except:
                return None
                pass
        return response

    def calling(self, nick):
        """ Envia el comando CALLING.
        """
        command = 'CALLING {0} {1}'.format(nick, self.client.videodat.myaddress[1])
        response = self.send_control(command, True)
        if response is None or len(response) < 1:
            return None
        response = response.decode('utf-8').split(' ')
        return response

    def call_hold(self, nick):
        """  Envia el comando CALL_HOLD.
        """
        command = 'CALL_HOLD {0}'.format(nick)
        self.send_control(command)
        return

    def call_resume(self, nick):
        """  Envia el comando CALL_RESUME.
        """
        command = 'CALL_RESUME {0}'.format(nick)
        self.send_control(command)
        return

    def call_end(self, nick):
        """  Envia el comando CALL_END.
        """
        command = 'CALL_END {0}'.format(nick)
        self.send_control(command)
        return

    def call_accepted(self, nick, udp_port):
        """ Envia respuesta CALL_ACCEPTED
        """
        command = 'CALL_ACCEPTED {0} {1}'.format(nick, udp_port)
        if self.connection:
            self.connection.sendall(command.encode())
        return

    def call_denied(self, nick):
        """ Envia respuesta CALL_DENIED
        """
        command = 'CALL_DENIED {0}'.format(nick)
        if self.connection:
            self.connection.sendall(command.encode())
        return

    def call_busy(self):
        """ Envia respuesta CALL_BUSY
        """
        command = 'CALL_BUSY'
        if self.connection:
            self.connection.sendall(command.encode())
        return

    # PROCESAR PETICIONES DE COMANDOS
    def process_control(self, command_data):
        """ Procesa un comando de control.
        """
        command = command_data.decode('utf-8')
        params = command.split(' ')
        if len(params) < 2:
            return None
        if params[0] == 'CALLING':
            if len(params) < 3:
                return None
            return self.client.process_calling(params[1], params[2])
        if params[0] == 'CALL_HOLD':
            return self.client.process_call_hold(params[1])
        if params[0] == 'CALL_RESUME':
            return self.client.process_call_resume(params[1])
        if params[0] == 'CALL_END':
            return self.client.process_call_end(params[1])
        return None
