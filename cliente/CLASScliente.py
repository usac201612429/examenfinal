'''Modulo del control de la clase del cliente'''


from constantes import * #FPRTH Importando las constantes del proyecto

#FPRTH Importando las librerias necesarias
import os
import paho.mqtt.client as paho
import logging
import time
import threading

#FPRTH Definiendo la estrucutra de mensajes de logging
FORMATO = '[%(levelname)s] %(message)s'
logging.basicConfig(level = logging.INFO, format=FORMATO)


''' def on_publish(client,userdata,mid):
    comandos.publicar() '''



'''FPRTH Se crea la clase que manejara al cliente/clientes'''

class clients (object):
    def __init__(self):
        #FPRTH Inicializando atritubutos de la clase clients
        self.usuario = self.DetID() #FPRTH se obtiene el id del usuario a partir de una funcion 
        
        #FPRTH Se crea una lista con tuplas que contiene los topics a los que se debe subscribir el usuario
        self.subscripciones = [(MQTT_COMANDOS+MQTT_GRUPO+self.usuario,MQTT_QOS),(MQTT_USUARIOS+MQTT_GRUPO+self.usuario,MQTT_QOS),(MQTT_AUDIO+MQTT_GRUPO+self.usuario,MQTT_QOS)]
        self.SubSalas() #FPRTH Se agregan mas topics en funcion de las salas. Se usa una funcion para esto

        #self.MenuActal=0 #FPRTH Varibale para controlar el menu actual

        #FPRTH Se hace configura y se inicia el cliente MQTT (Basado en el ejemplo)
        self.cliente_paho = paho.Client(clean_session=True)
        self.cliente_paho.on_publish = self.on_publish
        self.cliente_paho.on_message = self.on_message
        self.cliente_paho.username_pw_set(MQTT_USER,MQTT_PASS)
        self.cliente_paho.connect(host=MQTT_HOST,port=MQTT_PORT)
        self.cliente_paho.subscribe(self.subscripciones)
        self.cliente_paho.loop_start()

        self.message = "00"
        self.topic = "00"

        self.hilos =[] #FPRTH Lista que controla los hilos a usar para reproducir el audio
        
    #FPRTH Funcion que asigna el topic destino del mensaje
    def SetDestino(self,dest):
        self.destino=dest

    #FPRTH Funcion que setea y graba en el archivo 'usuario' el id del cliente
    def SetId(self,id):
        self.id = id
        os.system('echo "'+id+'" > usuario')
    
    #FPRTH Funcion que devuelve el topic destino del mensaje
    def GetDestino(self):
        return self.destino

    #FPRTH Funcion que envia un mensaje 'msg' a travez de MQTT
    def EnviarTexto(self,msg):
        self.cliente_paho.publish(self.destino,msg,qos=0,retain=False)
        
    #FPRTH Funcion que devuelve el id del cliente
    def GetUsuario(self):
        return self.usuario

    #FPRTH Funcion que obtiene del archivo 'usuario' el id del cliente y lo devuelve
    def DetID(self):
        arch_usuario=open('usuario','r')
        texto_usuario =arch_usuario.read()
        arch_usuario.close()    
        return texto_usuario[:-1]

    #FPRTH Funcion que setea el menu actual de la interfaz
    def SetMenuActual(self,menu):
        self.MenuActal = menu

    #FPRTH Funcion que determina una lisat con las salas a las que esta subscrito el usuario a partir del archivo 'salas'
    def DetSalas(self):
        self.lista_salas=[]
        arch_salas = open('salas','r')
        texto_salas=arch_salas.read()
        lista = texto_salas[:-1].split('\n')
        for i in lista:
            self.lista_salas.append(i[2:])
        
    #FRTH Funcion que devuelve la lista determinada en la funcion DetSalas
    def GetSalas(self):
        self.DetSalas()
        return self.lista_salas

    #FPRTH Funcion que a partir de la lista de salas agrega mas topics a la lista con los topics a suscribirse
    def SubSalas(self):
        self.DetSalas()
        for i in self.lista_salas:
            self.subscripciones.append((MQTT_SALAS+MQTT_GRUPO+i,MQTT_QOS))
            self.subscripciones.append((MQTT_AUDIO+MQTT_GRUPO+i,MQTT_QOS))


    #FPRTH Funcion que maneja cuando se publica en MQTT
    def on_publish(self,client,userdata,mid):
        info='Mensaje enviado'
        logging.debug(info)

    #FPRTH Funcion que maneja cuando se recibe un mensaje por MQTT
    def on_message(self,client,userdata,msg):
        self.message = msg.payload
        self.topic = msg.topic
        
        topic=str(msg.topic)#FPRTH Se obtiene el topic donde se recibio el mensaje
        ltopic=topic.split('/') #FPRTH El topic se divide en lista para ver su estructura y poder tomar decisioens

        #FPRTH Se comprueba de que topic proviene el mensaje
        if ltopic[0]==MQTT_USUARIOS[:-1]: #Si es de usuarios solo se muestra el mensaje
            print('\n\n')
            logging.info("[MENSAJE NUEVO DE USUARIO]\n\t"+msg.payload.decode()+'\n')
        elif ltopic[0]==MQTT_SALAS[:-1]: #FPRTH Si es de una sala se muestra el mensaje indicando de que sala proviene el mensaje
            print('\n\n')
            logging.info("[MENSAJE NUEVO EN LA SALA " +ltopic[2]+"]\n\t"+msg.payload.decode()+'\n')
        elif ltopic[0]==MQTT_AUDIO[:-1]: #FPRTH Si viene del topic audio se indica que es audio y se crea un hilo que guarda y reproduce el audio
            print('\n\n')
            logging.info("[MENSAJE DE AUDIO NUEVO]")
            archivo_nombre=str(time.time())+'.wav' #FPRTH Se asigna un nombre al archivo dependiendo del momento en que se recibio
            brcibidos = msg.payload
            #FPRTH Se configura e inicia el hilo que guarda y reproduce el audio
            self.hilo = threading.Thread(name='Reproductor de audio recibido',target=self.Reproducir_Audio, args=((archivo_nombre,brcibidos)),daemon=False)
            self.hilo.start()
        # elif ltopic[0] == 'comandos': #FPRTH Si viene del topic comandos se ejecuta un metodo diferente
        #     comandos.verificarMensajes(msg.payload, msg.topic)


    #FPRTH Funcion que guarda y reproduce el audio
    def Reproducir_Audio(self,nombre,bytes_recibidos):
        #FPRTH Se crea un archivo con la informacion que recibe de MQTT
        audio = open(nombre,'wb')
        audio.write(bytes_recibidos)
        audio.close()
        os.system('aplay '+nombre) #FPRTH Se reproduce el archivo




''' #OAGM: objeto comandos. Recibe la cliente mqtt como parametro (paho.Client)
comandos = ClientCommands(cliente_paho) '''