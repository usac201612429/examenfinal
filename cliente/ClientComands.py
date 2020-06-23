from constantes import *
import time
import threading 
import logging
import sys

class ClientCommands:
    def __init__(self, cliente_paho):
        self.lastCommandSent = b'00'                #OAGM: variable para que en poho.publish() se sepa si se envio un comando o no
        self._periodosAlivePerdidos = 0             #OAGM: variable para contar periodos ALIVE perdidos
        self._alivePeriod = ALIVE_PERIOD
        self.cliente_paho = cliente_paho            #OAGM: se traen todas los metodos paho.Client
        with (open("usuario", "rb")) as archivo:    #OAGM: obtenemos el userID        
            self.userID = archivo.read()[:-1]       
        archivo.close()
        self.hiloCommands = threading.Thread(name = 'hiloCommands', target = self.alive, args = (()), daemon = True) #OAGM hilo para revisar comandos entrantes
        self.hiloCommands.start()   

    def alive(self):
        while True:
            value = ALIVE + b"$" + self.userID          #OAGM: creacion de la trama ALIVE a enviar
            self.lastCommandSent = ALIVE                #OAGM: se establece que este fue el ultimo cmando enviado
            self.cliente_paho.publish(f"{MQTT_COMANDOS}{MQTT_GRUPO}{self.userID.decode('UTF-8', 'strict')}", value, qos = 0, retain = False)    #OAGM: se envia la trama
            # print("alive enviado", self._periodosAlivePerdidos) 
            time.sleep(self._alivePeriod)               #OAGM: retardo entre envios ALIVE
            self._periodosAlivePerdidos += 1            #OAGM: primer periodo sin recibir ACK del servidor
            if self._periodosAlivePerdidos == 3:        #OAGM: al alcanzar 3 peridos sin recibir ACK del servidor
                self._alivePeriod = 0.1                 #OAGM: se modifica retardo entre envios ALIVE
            elif self._periodosAlivePerdidos == int(20 // self._alivePeriod) + 3:   #OAGM: luego de 20s sin respuesta del servidor
                logging.critical('Conexión finalizada, el servidor no responde')    #OAGM: se indica que el servidor no respondio
                self.cliente_paho.loop_stop()                                       #OAGM: se finalizan algunos procesos
                self.cliente_paho.disconnect()
                sys.exit()                                                          #OAGM: y se sale del programa               
                
                

    def ackRespuesta(self):
        pass

    
    def publicar(self):
        if self.lastCommandSent in [FRR, FTR, ALIVE, ACK, OK, NO]:
            self.lastCommandSent = b'00'
        else:
            info='Mensaje enviado'
            logging.info(info)


    def verificarMensajes(self, payload, topic):
        """ OAGM: si el comando es ACK, reinicia el contador de periodos alive sin reslpuesta.  """ 
  
        if payload[:1] == ACK:                          #OAGM: si el comando recibido del topic comandos/ es ACK
            self._periodosAlivePerdidos = 0             #OAGM: reinicia el conteo de periodos ALIVE sin respuesta del servidor
            self._alivePeriod = ALIVE_PERIOD            #OAGM: normaliza el retardo entre envios ALIVE
            payload = "00"                              #OAGM: con esto se evita que detecte un comando mas de una vez si este se recibio de nuevo

