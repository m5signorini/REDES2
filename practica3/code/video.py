"""


"""
from PIL import Image, ImageTk
import cv2
import time
import socket
import sys
import numpy as np


class VideoData(object):
    def __init__(self, myaddress):
        # Direccion UDP para el envio y recepcion de video
        self.order = 0
        self.myaddress = myaddress
        self.dest = None
        self.init_udp_sockets()
        return

    def init_udp_sockets(self):
        """ Crear socket UDP.
        Inicializa un socket conectado a la direccion especificada,
        el cual se puede usar tanto para enviar como para recibir los
        paquetes udp.
        """
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(self.myaddress)
        return

    def send_udp_message(self, message, address=None):
        """ Enviar mensaje UDP.
        message : bytes a enviar
        address : (dest_host, dest_port)
        Devuelve la cantidad de bytes enviados.
        """
        if address is None:
            address = self.dest
        try:
            address = (address[0], int(address[1]))
            sent = self.send_sock.sendto(message, address)
        except:
            return None
        return sent

    def receive_udp(self):
        """ Recibir un mensajes UDP.
        """
        try:
            data, address = self.recv_sock.recvfrom(160000)
            return data, address
        except:
            return None
        return None

    def set_dest_address(self, address):
        """ Especificar direccion destino por defecto
        """
        self.dest = (address[0], int(address[1]))
        self.order = 0
        return

    def send_video(self, img, res, fps=20, order=None, dest=None):
        """ Enviar un paquete de video UDP
        Si dest no se especifica, se utiliza la variable de clase ya asignada
        Antes de enviar habria que llamar a set_dest_address
        """
        # Procesar frame
        timestamp = time.time()
        headers = '{0}#{1}#{2}#{3}#'.format(self.order, timestamp, res, fps)
        message = bytearray(headers.encode('utf-8'))
        # Comprimir frame
        encode_param = [cv2.IMWRITE_JPEG_QUALITY,50]
        result,encimg = cv2.imencode('.jpg',img,encode_param)
        if result == False:
            print('Error al codificar imagen')
            return None
        encimg = encimg.tobytes()
        # Enviar
        message.extend(encimg)
        return self.send_udp_message(message, dest)

    def receive_video(self):
        """ Recibir un paquete de video UDP
        """
        result = self.receive_udp()
        if result is None:
            return None, None
        message, address = result
        decoded = message.split(b'#',4)
        headers = [decoded[i].decode('utf-8') for i in range(4)]
        headers = {'order':headers[0], 'timestamp':headers[1], 'res':headers[2], 'fps':headers[3]}
        # Decodificar frame
        encimg = decoded[4]
        decimg = cv2.imdecode(np.frombuffer(encimg,np.uint8), 1)
        return headers, decimg
