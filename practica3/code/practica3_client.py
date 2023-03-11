# import the library
import threading

import queue
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2

from video import VideoData
from vcontrol import *
from dserver import *
from config import *

class VideoClient(object):

    def __init__(self, window_size):

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10, 10)
        self.app.setSticky("news")
        self.app.setExpand("both")

        # Preparación del interfaz
        self.app.setLabelFont(16)
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ", row=0)
        self.app.addLabel("subtitle", "Debe registrarse para poder usar la aplicación", row=1)
        self.app.setLabelFg("subtitle", "red")
        self.app.addImage("video", "imgs/webcam.gif", row=2, column=0, rowspan=4, colspan=3)
        self.app.addImage("VideoCall", "imgs/waiting.gif", row=2, column=2, rowspan=4, colspan=3)

        # Registramos la función de captura de video
        # Esta misma función también sirve para enviar un vídeo
        self.myImage = 0
        self.cap = cv2.VideoCapture(self.myImage)  # webcam o video
        self.app.setPollTime(20)
        self.app.registerEvent(self.capturaVideo)

        # Añadir los botones
        self.app.addButtons(["Conectar", "Colgar", "Salir"], self.buttonsCallback, row=6)
        self.app.addButton("Log In", self.logInCallback, row=7)
        # Deshabilitamos los botones hasta que el usuario esté registrado o en una llamada
        self.app.disableButton("Conectar")
        self.app.disableButton("Colgar")

        # Barra de estado
        # Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
        self.app.addStatusbar(fields=2)
        self.inACall = 0

    def setControls(self, dserver, vcontrol, videodata):
        self.dserver = dserver
        self.vcontrol = vcontrol
        self.videodat = videodata
        self.userList = dserver.list_users()
        self.nicks = list(map(lambda d: d['nick'], self.userList))

    def start(self):
        self.app.go()

    # Función que captura el frame a mostrar en cada momento
    def capturaVideo(self):

        # Capturamos un frame de la cámara o del vídeo
        ret, frame = self.cap.read()
        frame = cv2.resize(frame, (640, 480))
        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        # Lo mostramos en el GUI
        self.app.setImageData("video", img_tk, fmt='PhotoImage')

    # Aquí tendría que el código que envia el frame a la red
    # ...

    # Establece la resolución de la imagen capturada
    def setImageResolution(self, resolution):
        # Se establece la resolución de captura de la webcam
        # Puede añadirse algún valor superior si la cámara lo permite
        # pero no modificar estos
        if resolution == "LOW":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        elif resolution == "MEDIUM":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        elif resolution == "HIGH":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Función que gestiona los callbacks de los botones

    def buttonsCallback(self, button):
        if button == "Salir":
            # Paramos los threads
            self.flag_end = 1
            self.inACall = 0
            self.t_send.join()
            self.t_receive.join()

            # Salimos de la aplicación
            self.dserver.quit()
            self.app.stop()

        elif button == "Conectar":
            # Entrada del nick del usuario a conectar
            self.app.startLabelFrame("CONEXION")
            self.app.addAutoEntry("Nick", self.nicks, 0, 1)
            self.app.addButtons(["Llamar", "Cancelar"], self.CallManagement)

        elif button == "Colgar":
            self.app.removeButton("PLAY")
            self.app.removeButton("PAUSE")
            self.app.removeButton("STOP")
            self.app.setImageData("VideoCall", "imgs/waiting.gif")
            self.cap = cv2.VideoCapture(self.myImage)

            self.flag_end = 1
            self.inACall = 0

            # Paramos los threads
            self.t_send.join()
            self.t_receive.join()

            # Lo mostramos en el GUI
            self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))

    # Funciones que gestionan el registro de usuarios

    def logInCallback(self):
        self.app.startLabelFrame("REGISTRO", rowspan=3, colspan=3)
        self.app.addLabelEntry("Name", 0, 1)
        self.app.addSecretLabelEntry("Password", 1, 1)
        self.app.addButtons(["Submit", "Cancel"], self.registerCallback, 2, 1)

    def registerCallback(self, button):
        if button == "Submit":
            self.nick = self.app.getEntry("Name")
            pwd = self.app.getEntry("Password")

            reg_res = self.dserver.register(self.nick, self.vcontrol.myaddress[0], self.vcontrol.myaddress[1], pwd)

            self.app.stopLabelFrame()
            self.app.removeLabelFrame("REGISTRO")

            if "OK WELCOME" in str(reg_res):
                self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))
                self.app.setLabelFg("subtitle", "black")
                self.app.enableButton("Conectar")
                self.app.setButton("Log In", "change nick")
            elif "NOK WRONG_PASS" in str(reg_res):
                self.app.setLabel("subtitle", "Contraseña errónea. Pruebe otra vez")
            else:
                self.app.setLabel("subtitle", "Error: comando REGISTER ha sido rechazado por el servidor")

        elif button == "Cancel":
            self.app.stopLabelFrame()
            self.app.removeLabelFrame("REGISTRO")

    # Función que gestiona una llamada

    def CallManagement(self, button):
        if button == "Llamar":
            self.app.enableButton("Colgar")
            self.nickToCall = self.app.getEntry("Nick")
            self.app.stopLabelFrame()
            self.app.removeLabelFrame("CONEXION")

            # Pedimos al servidor la ip correspondiente al nick a llamar
            query_res = self.dserver.query(self.nickToCall)
            if query_res is None:
                self.app.warningBox("errorNick", "Error: El nick al que quiere llamar no existe")
                self.app.disableButton("Colgar")
            else:
                tcp = (query_res['ip_address'], int(query_res['port']))
                self.app.setLabel("subtitle", "Llamando a {} ...".format(self.nickToCall))
                init_res = self.vcontrol.init_control_sender(tcp)

                if init_res is None:
                    self.app.infoBox("not connected", "El usuario al que quiere llamar no está conectado")
                    self.app.disableButton("Colgar")
                    self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))
                else:
                    # Enviamos un CALLING y comprobamos la respuesta
                    calling_res = self.vcontrol.calling(self.nick)

                    if calling_res is None:
                        self.app.warningBox("errorCalling", "Error: comando CALLING ha sido rechazado por el servidor")
                        self.app.disableButton("Colgar")
                        self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))
                    elif "CALL_BUSY" in calling_res[0]:
                        self.app.infoBox("busy", "La persona a la que quiere llamar está ocupada. Pruebe más tarde")
                        self.app.disableButton("Colgar")
                        self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))
                    elif "CALL_DENIED" in calling_res[0]:
                        self.app.infoBox("denied", "Su llamada ha sido denegada")
                        self.app.disableButton("Colgar")
                        self.app.setLabel("subtitle", "Bienvenido {}".format(self.nick))
                    else:
                        # si la llamada se acepta, se recibe el puerto udp al que enviar el video
                        self.dest_udp = (tcp[0], calling_res[2])

                        showCamera = self.app.questionBox('vidOrCamera',
                                                          "¿Quiere compartir su cámara(Y) o enviar un vídeo(N)?",
                                                          parent=None)
                        if showCamera == False:
                            self.vid = self.app.openBox(title='selVideo', dirName='/imgs', mode='r')
                        else:
                            self.vid = None

                        self.flag_hold = 0
                        self.flag_end = 0
                        self.inACall = 1

                        # Creamos los threads que se encargaran de enviar nuestro video y recibir el que entra
                        self.t_send = threading.Thread(target=self.send_video)
                        self.t_send.start()
                        self.t_receive = threading.Thread(target=self.receive_video)
                        self.t_receive.start()

        elif button == "Cancelar":
            self.app.stopLabelFrame()
            self.app.removeLabelFrame("CONEXION")

    # Funcion que envia un video a la red

    def send_video(self):
        self.videodat.set_dest_address(self.dest_udp)
        if self.vid is None:
            vidToSend = cv2.VideoCapture(0)  # camara
            ret, frame = vidToSend.read()
            while ret and self.inACall:
                self.videodat.send_video(frame, "640x320")
                ret, frame = vidToSend.read()
        else:
            vidToSend = cv2.VideoCapture(self.vid)  # video
            ret, frame = vidToSend.read()
            while ret and self.inACall:
                self.videodat.send_video(frame, "640x320")
                ret, frame = vidToSend.read()
        return

    # Funcion que recibe el video entrante

    def receive_video(self):
        # Cargar nuestro video
        if self.vid is None:
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(self.vid)

        # Añadimos el video recibido
        self.app.addButtons(['PLAY', 'PAUSE', 'STOP'], self.videoCallback, row=8)

        # Creamos cola para buffer
        self.videoq = queue.Queue(40)
        # Leer un frame del video
        ret, frame = self.videodat.receive_video()
        self.videoq.put_nowait(frame)

        while ret and self.inACall:
            if self.flag_hold == 1:  # si estamos en espera, no cargamos nuevos frames
                pass
            elif self.flag_end == 1:  # fin de la llamada
                break
            else:
                if self.videoq.qsize() > 5:
                    frame = self.videoq.get_nowait()
                    frame = cv2.resize(frame, (320, 240))
                    cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

                    # Lo mostramos en el GUI
                    self.app.setImageData("VideoCall", img_tk, fmt='PhotoImage')

                # Leer un nuevo frame de cada video
                ret, frame = self.videodat.receive_video()
                self.videoq.put_nowait(frame)

        return

    def videoCallback(self, button):
        if button == 'PLAY':
            self.flag_hold = 0
            self.vcontrol.call_resume(self.nick)

        elif button == 'PAUSE':
            self.flag_hold = 1
            self.vcontrol.call_hold(self.nick)

        elif button == 'STOP':
            self.app.removeButton("PLAY")
            self.app.removeButton("PAUSE")
            self.app.removeButton("STOP")
            self.app.setImageData("VideoCall", "imgs/waiting.gif")
            self.cap = cv2.VideoCapture(self.myImage)

            self.flag_end = 1
            self.inACall = 0

            # Paramos los threads
            self.t_send.join()
            self.t_receive.join()

            # Enviamos fin de llamada
            self.vcontrol.call_end(self.nick)

    def process_calling(self, nick, udp_port):
        """ Procesa el comando CALLING.
        """
        accept_call = self.app.questionBox('acceptCall', "Recibiendo una llamada de {}, ¿quiere aceptar?".format(nick),
                                            parent=None)
        if accept_call is False:
            self.vcontrol.call_denied(self.nick)  # rechazamos la llamada
            return

        # Pedimos al servidor la ip correspondiente al nick a llamar
        query_res = self.dserver.query(nick)
        if query_res is None:
            self.app.warningBox("errorQuery", "Error: comando QUERY ha sido rechazado por el servidor")
            return

        # aceptamos la llamada
        self.vcontrol.init_control_sender((query_res['ip_address'], int(query_res['port'])))
        self.vcontrol.call_accepted(self.nick, self.videodat.myaddress[1])

        # establecer conexion udp
        self.dest_udp = (query_res['ip_address'], udp_port)
        showCamera = self.app.questionBox('vidOrCamera',
                                          "¿Quiere compartir su cámara(Y) o enviar un vídeo(N)?",
                                          parent=None)
        if showCamera == False:
            self.vid = self.app.openBox(title='selVideo', dirName='/imgs', mode='r')
        else:
            self.vid = None

        self.flag_end = 0
        self.flag_hold = 0
        self.inACall = 1

        self.t_send = threading.Thread(target=self.send_video)
        self.t_send.start()
        self.t_receive = threading.Thread(target=self.receive_video)
        self.t_receive.start()
        return

    def process_call_hold(self, nick):
        """  Procesa el comando CALL_HOLD.
        """
        self.flag_hold = 1
        self.app.setLabel("subtitle", "Estás en espera")
        return

    def process_call_resume(self, nick):
        """  Procesa el comando CALL_RESUME.
        """
        self.flag_hold = 0
        return

    def process_call_end(self, nick):
        """  Procesa el comando CALL_END.
        """
        self.app.removeButton("PLAY")
        self.app.removeButton("PAUSE")
        self.app.removeButton("STOP")
        self.app.removeImage("VideoCall")

        self.flag_end = 1
        self.inACall = 0

        # Paramos los threads
        self.t_send.join()
        self.t_receive.join()
        return


if __name__ == '__main__':
    vc = VideoClient("640x520")

    # Crear aquí los threads de lectura, de recepción y,
    # en general, todo el código de inicialización que sea necesario
    # ...

    if CONFIG_IP == 'default':
        hostname = socket.gethostname()
        localip = socket.gethostbyname(hostname)
    else:
        localip = CONFIG_IP
    myaddress = (localip, CONFIG_PORT_TCP)
    myudp = (localip, CONFIG_PORT_UDP)

    dserver = DiscoveryServer()
    vcontrol = VideoControl(myaddress, vc)
    videodata = VideoData(myudp)
    vc.setControls(dserver, vcontrol, videodata)

    t_vcontrol = threading.Thread(target=vcontrol.start_thread)
    t_vcontrol.start()

    # Lanza el bucle principal del GUI
    # El control ya NO vuelve de esta función, por lo que todas las
    # acciones deberán ser gestionadas desde callbacks y threads
    vc.start()
    vcontrol.end_thread()
    t_vcontrol.join()
