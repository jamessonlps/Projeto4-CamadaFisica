#####################################################
# Camada Física da Computação
#Carareto
#11/08/2020
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
import time
import numpy as np

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM6"                  # Windows(variacao de)


def main():
    try:
        #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
        #para declarar esse objeto é o nome da porta.
        com1 = enlace('COM1')
        com2 = enlace('COM2')
        

        # Ativa comunicacao. Inicia os threads e a comunicação seiral 
        com1.enable()
        print('Porta 1 inicializada com sucesso\n')
        
        com2.enable()
        print('Porta 2 inicializada com sucesso\n')
        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.

        # com1.fisica.flush()
        # com2.fisica.flush()
        #aqui você deverá gerar os dados a serem transmitidos. 
        #seus dados a serem transmitidos são uma lista de bytes a serem transmitidos. Gere esta lista com o 
        #nome de txBuffer. Esla sempre irá armazenar os dados a serem enviados.

        with open ("./img/small.png", "rb") as img:
            img = img.read()
            txBuffer = bytearray(img)
        # txBuffer = open('./img/teste.png', 'rb').read()

        #faça aqui uma conferência do tamanho do seu txBuffer, ou seja, quantos bytes serão enviados.
        print(f"Estamos enviando {len(txBuffer)} bytes pela porta COM1\n")

        #finalmente vamos transmitir os tados. Para isso usamos a funçao sendData que é um método da camada enlace.
        #faça um print para avisar que a transmissão vai começar.
        #tente entender como o método send funciona!
        #Cuidado! Apenas trasmitimos arrays de bytes! Nao listas!

        com1.sendData(txBuffer)

        time.sleep(0.5)

        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # Tente entender como esse método funciona e o que ele retorna
        txSize = int(com1.tx.getStatus())
        print(f"Testando o txSize = {txSize}")
        #Agora vamos iniciar a recepção dos dados. Se algo chegou ao RX, deve estar automaticamente guardado
        #Observe o que faz a rotina dentro do thread RX
        #print um aviso de que a recepção vai começar.

        #Será que todos os bytes enviados estão realmente guardadas? Será que conseguimos verificar?
        #Veja o que faz a funcao do enlaceRX  getBufferLen

        #acesso aos bytes recebidos
        txLen = len(txBuffer)
        print(f"txLen = {txLen}")

        rxBuffer, nRx = com2.getData(txSize)

        print(f"Recebidos {nRx} bytes pela porta COM2")

        with open ("./img/imagem_copia.png", 'wb') as file:
            file.write(rxBuffer)
            print("Arquivo cópia salvo")

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        
        com1.disable()
        com2.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        com2.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
