from variables import *
import time
import binascii
import threading 
import socket
import logging

class ServerCommands:
    """ OAGM:
        Se recibe un servidor para manipular. 
        Luego se crea e inicia un hilo llamado "hiloFindCommands" para verificar constantemente
        los comandos que ingresan al servidor   """

    def __init__(self, servidor):
        self.servidor = servidor
        self.frrInfo = []
        self.tranferirAudio = False
        self.hiloFindCommands = threading.Thread(name = 'FindCommands', target = self.findCommand, args = (()), daemon = True) #OAGM hilo para revisar comandos entrantes 
        self.hiloFindCommands.start()       
        self.hilo_sock = threading.Thread(name='hilo del socket tcp',target=self.socket,daemon=True)#AIPG hilo para socket, aqui se manipula el audio
        self.hilo_sock.start()


    """ OAGM:
        Funcion para devolver un ACK al recivir distintos comandos. Utiliza el valor de "toTopic" para saber a
        quien debe enviar el ACK.   """

    def ack(self, toTopic):
            value = ACK + b'$' + toTopic
            self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{toTopic.decode('UTF-8', 'strict')}", value, qos = 0, retain = False)
    
    def respuestaFTR(self, destinoYtamanio, remitente):
        #OAGM: destinoYtamanio = [01S02, 40004] o [201612429, 40004]; remitente = #carné
        self.frrInfo = [destinoYtamanio[0], destinoYtamanio[1], remitente]
        if len(destinoYtamanio[0]) == 5:
            
            for usuario in self.servidor.salas_dict[destinoYtamanio[0]]:
                if usuario in self.servidor.lista_activos:
                    value = OK + b'$' + destinoYtamanio[0].encode()
                    self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
                    # self.hilo_sock.start()
                    self.tranferirAudio = True
                    break
            else:
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)                
        else:
            self.hilo_sock = threading.Thread(name='hilo del socket tcp',target=self.socket,daemon=False)
            if destinoYtamanio[0] in self.servidor.lista_activos:
                value = OK + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
                # self.hilo_sock.start()
                self.tranferirAudio = True
            else:
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)   
    
    def socket(self):#AIPG metodo del socket controlado en el hilo
        while True:
            if self.tranferirAudio:
                parametros_socket_server =('127.0.0.1',TCP_PORT)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(parametros_socket_server)#AIPG levanta el socket en la direccion especificada
                    BUFFER_SIZE = 16 * 1024 #Bloques de 16 KB
                    sock.listen(1)
                    while True:
                        logging.info('Esperando conexion remota')
                        conexion, dir_cliente = sock.accept()
                        logging.info(f'conexion establecida con: {dir_cliente}')
                        try:
                            data = conexion.recv(BUFFER_SIZE)     
                            with open("ultimoAudio.wav", "wb") as audio:
                                logging.info("añadiendo contenido de audio. . .")
                                while data:                           
                                    audio.write(data) 
                                    data = conexion.recv(BUFFER_SIZE)           
                        
                        finally:
                            conexion.close()
                            break

                logging.info("Archivo guardado!")
                self.frr()
                # self.hilo_frr= threading.Thread(name='hilo del socket tcp',target=self.frr,daemon=False)
                # self.hilo_frr.start()
                   

    def frr(self):
        #OAGM: self.frrInfo = [01S02, 40004, #carnéRemitente] o [#carnéDestinatario, 40004, #carnéRemitente]
        #OAGM: a FRR se le concatena Remintente + Trama FTR(sin el comando), es decir FRR + Remitente + (trama FTR); trama FTR = FTR$01S02$40004 o FTR$201612429$40004
        #OAGM: por lo tanto, la trama FRR se lee: FRR + remitente + destinatario + tamaño del audio
        if len(self.frrInfo[0]) == 9:       #OAGM: desitnatario usuario
            value = FRR + b'$' + self.frrInfo[2].encode() + b'$' + self.frrInfo[0].encode() + b'$' + self.frrInfo[1].encode()
            self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{self.frrInfo[0]}", value, qos = 0, retain = False)
            #AIPG configuraciones del socket
            parametros_socket_server =('127.0.0.1',TCP_PORT)
            # parametros_socket_server =(MQTT_HOST,TCP_PORT)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock: #AIPG socket de la ipv4 y tcp            
                sock.bind(parametros_socket_server)#AIPG levanta el socket en la direccion especificada
                BUFFER_SIZE = 16 * 1024 #Bloques de 16 KB
                sock.listen(1)
                while True:
                    logging.info('Esperando conexion remota')
                    conexion, dir_cliente = sock.accept()
                    logging.info(f'conexion establecida con: {dir_cliente}')
                    try:
                        with open("ultimoAudio.wav", "rb") as audio:
                            conexion.sendfile(audio, 0)
                        logging.info("Audio enviado!")                 
                    
                    finally:
                        conexion.close()
                        logging.info("conexion finalizada")
                    break
            print("salio del with para socket de envio a usuario")

        else: 
            for usuario in self.servidor.salas_dict[self.frrInfo[0]]:
                if usuario in self.servidor.lista_activos:
                    value = FRR + b'$' + self.frrInfo[2].encode() + b'$' + self.frrInfo[0].encode() + b'$' + self.frrInfo[1].encode()
                    self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{usuario}", value, qos = 0, retain = False)
                    #AIPG configuraciones del socket
                    parametros_socket_server =('127.0.0.1',TCP_PORT)
                    # parametros_socket_server =(MQTT_HOST,TCP_PORT)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:     #AIPG socket de la ipv4 y tcp                    
                        sock.bind(parametros_socket_server)#AIPG levanta el socket en la direccion especificada
                        BUFFER_SIZE = 16 * 1024 #Bloques de 16 KB
                        sock.listen(1)
                        while True:
                            logging.info(f'Esperando conexion remota: cliente {usuario}')
                            conexion, dir_cliente = sock.accept()
                            logging.info(f'conexion establecida con: {dir_cliente}')
                            try:
                                with open("ultimoAudio.wav", "rb") as audio:
                                    conexion.sendfile(audio, 0)
                                logging.info("Audio enviado!")                        
                            
                            finally:
                                conexion.close()
                                logging.info("conexion finalizada")
                                break
                    print("salio del with para socket de envio a usuario")
        self.tranferirAudio = False


    """ OAGM:
        Metodo que se ejecuta sobre un hilo (hiloFindCommand). Constantemete revisa si ha recivido un comando de los
        esperados y decide que otro metodo ejecutar. al finalizar establece el valor de self.sevidor.msg = "00", con
        esto no ejecutara un comando mas veces de las debidas.  """

    def findCommand(self):
        while True:

            """ OAGM:
                si el comando es ALIVE, se llamará al metodo ack y se le envia quien lo envia.  """
            if self.servidor.topic[:8] == 'comandos':                
                if self.servidor.msg[:1] == ALIVE:
                    self.ack(self.servidor.msg[2:12]) 
                    self.servidor.msg = "00"
                
                elif self.servidor.msg[:1] == FTR:
                    # print(self.servidor.topic, self.servidor.msg)
                    # print(self.servidor.msg.decode().split("$")[1:])
                    # print(self.servidor.topic.split("/")[2])
                    self.respuestaFTR(self.servidor.msg.decode().split("$")[1:], self.servidor.topic.split("/")[2]) #OAGM: se envia destino y tamaño del audio
                    self.servidor.msg = "00"
