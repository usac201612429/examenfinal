from constantes import *
import time
import threading 
import logging
import sys
import os

class ClientCommands:
    def __init__(self, cliente):
        self.lastCommandSent = b'00'                #OAGM: variable para que en poho.publish() se sepa si se envio un comando o no
        self._periodosAlivePerdidos = 0             #OAGM: variable para contar periodos ALIVE perdidos
        self.ackRecieved = False
        self._alivePeriod = ALIVE_PERIOD
        self.cliente = cliente                      #OAGM: se traen todas los metodos paho.Client
        with (open("usuario", "rb")) as archivo:    #OAGM: obtenemos el userID        
            self.userID = archivo.read()[:-1]       
        archivo.close()
        self.audio = b"00"                          #OAGM: variable para archivos de audio
        self.audioSize = 0                          #OAGM: tamaño del archivo de audio
        self.ftrSent = False
        self.enviandoAudio = False
        self.hiloAlive = threading.Thread(name = 'hiloCommands', target = self.alive, args = (()), daemon = True) #OAGM hilo para enviar ALIVEs
        self.hiloAlive.start()   
        self.hiloMensajes = threading.Thread(name = 'hiloCommands', target = self.verificarMensajes, args = (()), daemon = True) #OAGM hilo para revisar comandos entrantes
        self.hiloMensajes.start()   

    def alive(self):
        while True:
            value = ALIVE + b"$" + self.userID          #OAGM: creacion de la trama ALIVE a enviar
            self.lastCommandSent = ALIVE                #OAGM: se establece que este fue el ultimo cmando enviado
            self.cliente.cliente_paho.publish(f"{MQTT_COMANDOS}{MQTT_GRUPO}{self.userID.decode('UTF-8', 'strict')}", value, qos = 0, retain = False)    #OAGM: se envia la trama
            # print("alive enviado", self._periodosAlivePerdidos) 
            time.sleep(self._alivePeriod)               #OAGM: retardo entre envios ALIVE
            # print(self._periodosAlivePerdidos)
            if not self.ackRecieved:                    #OAGM: se revisa si entro un ack durante el sleep
                self._periodosAlivePerdidos += 1        #OAGM: primer periodo sin recibir ACK del servidor
            else:
                self.ackRecieved = False
            if self._periodosAlivePerdidos == 3:        #OAGM: al alcanzar 3 peridos sin recibir ACK del servidor
                self._alivePeriod = 0.1                 #OAGM: se modifica retardo entre envios ALIVE
            elif self._periodosAlivePerdidos == int(20 // self._alivePeriod) + 3:   #OAGM: luego de 20s sin respuesta del servidor
                logging.critical('Conexión finalizada, el servidor no responde')    #OAGM: se indica que el servidor no respondio
                self.cliente.cliente_paho.loop_stop()                                       #OAGM: se finalizan algunos procesos
                self.cliente.cliente_paho.disconnect()
                os.kill(os.getpid(), 9)                                             #OAGM: y se sale del programa 

 
    def ftr(self):                                              #OAGM: envio de trama FTR y levanta "bandera" de espera
        self.lastCommandSent = FTR
        self.audio = open('audio.wav','rb')                     #OAGM: lectura del audio grabado
        self.audioSize = os.stat('audio.wav').st_size           #OAGM: tamaño del archivo de audio en bytes
        if len(self.cliente.destino.split("/")[2]) == 9:        #OAGM: construyendo la trama FTR
            value = FTR + b'$' + (self.cliente.destino.split("/")[2]).encode() + b'$' + str(self.audioSize).encode()
        else:
            value = FTR + b'$' + (self.cliente.destino.split("/")[1] + self.cliente.destino.split("/")[2]).encode() + b'$' + str(self.audioSize).encode()
        #OAGM: envio de la trama y levantado de "bandera"
        self.cliente.cliente_paho.publish(f"{MQTT_COMANDOS}{MQTT_GRUPO}{self.userID.decode('UTF-8', 'strict')}", value, qos = 0, retain = False)    #OAGM: se envia la trama
        self.ftrSent = True
        self.enviandoAudio = True

    def socketOn(self):
        if not self.ftrSent and self.enviandoAudio:
            print("Se levantó el socket")

    
    def publicar(self):
        if self.lastCommandSent in [FRR, FTR, ALIVE, ACK, OK, NO]:
            self.lastCommandSent = b'00'
        else:
            info='Mensaje enviado'
            logging.info(info)


    def verificarMensajes(self):
        """ OAGM: si el comando es ACK, reinicia el contador de periodos alive sin reslpuesta.  """ 
        while True:
            if self.cliente.topic[:8] == 'comandos':
                
                if self.cliente.message[:1] == ACK:             #OAGM: si el comando recibido del topic comandos/ es ACK
                    self.ackRecieved = True                     #OAGM: hay un ack que no ha reiniciado el contador de alives perdidos
                    self._periodosAlivePerdidos = 0             #OAGM: reinicia el conteo de periodos ALIVE sin respuesta del servidor
                    self._alivePeriod = ALIVE_PERIOD            #OAGM: normaliza el retardo entre envios ALIVE
                    self.cliente.message = "00"
                                                               #OAGM: con esto se evita que detecte un comando mas de una vez si este se recibio de nuevo
                elif self.cliente.message[:1] == OK:
                    self.ftrSent = False
                    self.socketOn()
                    self.cliente.message = "00"
                    print("recibi un OK")

                elif self.cliente.message[:1] == NO:
                    self.ftrSent = False
                    self.cliente.message = "00"
                    print("recibi un NO")

