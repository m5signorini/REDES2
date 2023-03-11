"""


"""

import select
import socket
import sys
import numpy as np

TIMEOUT_SECS = 2.5

class DiscoveryServer(object):
    def __init__(self):
        self.server_sock = None
        self.init_server_connection()
        return

    def init_server_connection(self):
        """ Inicia la conexion TCP con el servidor vega.
        Devuelve el socket ya conectado.
        """
        if self.server_sock:
            self.server_sock.close()
        # Crear y conectar socket
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('vega.ii.uam.es', 8000)
        self.server_sock.connect(server_address)
        self.server_sock.setblocking(False)
        return self.server_sock

    def send_command_to_server(self, command):
        """ Enviar comando al servidor vega.
        Dado un comando en formato string, lo envia al servidor y
        devuelve la respuesta en formato bytes.
        Devuelve None en caso de error (comando no valido,...)
        """
        response = bytearray()
        # Enviar comando
        try:
            self.server_sock.sendall(command.encode())
        except:
            print('Error al enviar comando {0} al servidor'.format(command))
            return None
        # Recibir respuesta
        try:
            while True:
                ready = select.select([self.server_sock],[],[], TIMEOUT_SECS)
                if ready[0]:
                    data = self.server_sock.recv(1024)
                    if data:
                        response.extend(data)
                    else:
                        break
                else:
                    break
                # Finalizar bucle si no hay más datos que leer
        except:
            print('error')
            pass
        return response

    def register(self, nick, ip_address, port, password, protocol='V0'):
        """ Registra al usuario en el servidor.
        """
        response = self.send_command_to_server('REGISTER {0} {1} {2} {3} {4}'.format(nick, ip_address, port, password, protocol))
        if response is None:
            print('Error: comando REGISTER ha sido rechazado por el servidor')
        return response

    def query(self, name):
        """ Obtiene del servidor la direccion IP dado un nombre.
        Objeto None o mapa con:
            'nick'
            'ip_address'
            'port'
            'protocols'
        """
        response = self.send_command_to_server('QUERY {0}'.format(name))
        if response is None:
            print('Error: comando QUERY ha sido rechazado por el servidor')
            return None
        response = response.decode('utf-8')
        if response == 'NOK USER_UNKNOWN':
            return None
        response = response.split('OK USER_FOUND ', 1)[1]
        response = response.split(' ')
        result = {'nick': response[0], 'ip_address': response[1], 'port':response[2], 'protocols':response[3].split('#')}
        return result

    def list_users(self):
        """ Obtiene del servidor el listado de usuarios
        Devuelve una lista con objetos que conforman los datos de cada usuario,
        por ejemplo, list_users()[0]['nick'] contiene el nick del primer usuario
        Objetos de la lista con propiedades:
            'nick'
            'ip_address'
            'port'
            'protocols'
        """
        response = self.send_command_to_server('LIST_USERS')
        if response is None:
            print('Error: comando LIST_USERS ha sido rechazado por el servidor')
            return []
        response = response.decode('utf-8')
        if response == 'NOK USER_UNKNOWN':
            return []
        response = response.split('OK USERS_LIST ',1)[1]
        response = response.split('#')
        # Eliminamos ultimo elemento que esta vacio
        response.pop()
        # Mapeamos creando un array de diccionarios
        result = []
        for unparsed_data in response:
            unparsed_data = unparsed_data.split(' ')
            if len(unparsed_data) < 4:
                continue
            parsed_data = dict.fromkeys(['nick','ip_address','port','protocols'])
            parsed_data['nick'] = unparsed_data[0]
            parsed_data['ip_address'] = unparsed_data[1]
            parsed_data['port'] = unparsed_data[2]
            parsed_data['protocols'] = unparsed_data[3]
            result.append(parsed_data)
        return result

    def quit(self):
        """ Cierra la conexion con el servidor.
        Recibe el socket ya conectado, envia un QUIT y cierra el socket.
        """
        self.send_command_to_server('QUIT')
        self.server_sock.close()
        return
