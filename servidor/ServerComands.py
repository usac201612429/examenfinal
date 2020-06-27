from variables import *
import time
import binascii
import threading 

class ServerCommands:
    """ OAGM:
        Se recibe un servidor para manipular. 
        Luego se crea e inicia un hilo llamado "hiloFindCommands" para verificar constantemente
        los comandos que ingresan al servidor   """

    def __init__(self, servidor):
        self.servidor = servidor
        self.hiloFindCommands = threading.Thread(name = 'FindCommands', target = self.findCommand(), args = (()), daemon = True) #OAGM hilo para revisar comandos entrantes
        self.hiloFindCommands.start()

    """ OAGM:
        Funcion para devolver un ACK al recivir distintos comandos. Utiliza el valor de "toTopic" para saber a
        quien debe enviar el ACK.   """

    def ack(self, toTopic):
            value = ACK + b'$' + toTopic
            self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{toTopic.decode('UTF-8', 'strict')}", value, qos = 0, retain = False)
    
    def respuestaFTR(self, destinoYtamanio, remitente):
        if len(destinoYtamanio[0]) == 5:
            print("FTR Sala")
            for usuario in self.servidor.salas_dict[destinoYtamanio[0]]:
                if usuario in self.servidor.lista_activos:
                    value = OK + b'$' + destinoYtamanio[0].encode()
                    self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
                    break
            else:
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)                
        else:
            print("FTR Usuario")
            if destinoYtamanio[0] in self.servidor.lista_activos:
                value = OK + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)
            else:
                print(f"Usuario {destinoYtamanio[0]} inactivo")
                value = NO + b'$' + destinoYtamanio[0].encode()
                self.servidor.mqttcliente.publish(f"{ROOTTOPIC}/{remitente}", value, qos = 0, retain = False)   
    
    
    # def frr(self, toTopic):
    #     client.publish(toTopic, (5).to_bytes(1, "little"), qos, retain = False)

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
                    self.respuestaFTR(self.servidor.msg.decode().split("$")[1:], self.servidor.topic.split("/")[2])
                    self.servidor.msg = "00"
