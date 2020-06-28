from variables import *
import time
import binascii
import threading 
import socket

class ServerCommands:
    """ OAGM:
        Se recibe un servidor para manipular. 
        Luego se crea e inicia un hilo llamado "hiloFindCommands" para verificar constantemente
        los comandos que ingresan al servidor   """

    def __init__(self, servidor):
        self.servidor = servidor
        self.frrInfo = []
        self.hiloFindCommands = threading.Thread(name = 'FindCommands', target = self.findCommand, args = (()), daemon = True) #OAGM hilo para revisar comandos entrantes 
        self.hiloFindCommands.start()       
        self.hilo_sock = threading.Thread(name='hilo del socket tcp',target=self.socket,daemon=False)

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
            print("FTR Sala")
            for usuario in self.servidor.salas_dict[destinoYtamanio[0]]:
                if usuario in self.servidor.lista_activos:
                    value = OK + b'$' + destinoYtamanio[0].encode()
                    self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
                    self.hilo_sock.start()
                    break
            else:
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)                
        else:
            print("FTR Usuario")
            if destinoYtamanio[0] in self.servidor.lista_activos:
                value = OK + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
                self.hilo_sock.start()
            else:
                print(f"Usuario {destinoYtamanio[0]} inactivo")
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)   
    
    def socket(self):#AIPG metodo del socket controlado en el hilo
        #AIPG configuraciones del socket
        parametros_socket_server =('127.0.0.1',TCP_PORT)
        # parametros_socket_server =(MQTT_HOST,TCP_PORT)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#AIPG socket de la ipv4 y tcp
        sock.bind(parametros_socket_server)#AIPG levanta el socket en la direccion especificada
        BUFFER_SIZE = 16 * 1024 #Bloques de 16 KB
        sock.listen(3)
        while True:
            print('Esperando conexion remota')
            coneccion, dir_cliente = sock.accept()
            print('conexion establecida con: ', dir_cliente)
            try:
                data = coneccion.recv(BUFFER_SIZE)
                while True:      
                    print("Creando/abriendo archivo de auido")
                    with open("ultimoAudio.wav", "wb") as audio:
                        print("añadiendo contenido de audio. . .")
                        while data:          
                            print(len(data))
                            if len(data) == self.frrInfo[1]: #< BUFFER_SIZE:   
                                break
                            else:                            
                                audio.write(data) 
                                data = coneccion.recv(BUFFER_SIZE) 
                                print("Archivo guardado!") 
                    audio.close()     
                    # print("Reproduciendo . . .")
                    # os.system('aplay ultimoAudio.wav') 
                    break
                self.frr()
                break
                

            except KeyboardInterrupt:
                sock.close()


    def frr(self):
        #OAGM: self.frrInfo = [01S02, 40004, #carnéRemitente] o [#carnéDestinatario, 40004, #carnéRemitente]
        #OAGM: a FRR se le concatena Remintente + Trama FTR(sin el comando), es decir FRR + Remitente + (trama FTR); trama FTR = FTR$01S02$40004 o FTR$201612429$40004
        #OAGM: por lo tanto, la trama FRR se lee: FRR + remitente + destinatario + tamaño del audio
        if len(self.frrInfo[0]) == 9:
            value = FRR + b'$' + self.frrInfo[2].encode() + b'$' + self.frrInfo[0].encode() + b'$' + self.frrInfo[1].encode()
            self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{self.frrInfo[0]}", value, qos = 0, retain = False)
        else: 
            pass


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
