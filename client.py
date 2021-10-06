import time
import numpy         as np
from   enlace    import *
from   random        import randint
from   utils  import build_datagram, load_file, number_of_packs
from   config import *

"""
Para verificar as portas no seu dispositivo:
    python -m serial.tools.list_ports


head template:
    h0 – tipo de mensagem
    h1 – id do sensor
    h2 – id do servidor
    h3 – número total de pacotes do arquivo
    h4 – número do pacote sendo enviado
    h5 – se tipo for handshake:id do arquivo
    h5 – se tipo for dados: tamanho do payload
    h6 – pacote solicitado para recomeço quando a erro no envio.
    h7 – último pacote recebido com sucesso.
    h8 – CRC
    h9 – CRC
"""

#serialName = "/dev/ttyACM0"           # Ubuntu
#serialName = "/dev/tty.usbmodem1411"  # Mac
serialName = "COM7"                    # Windows


def main():
    try:
        # Cria objeto enlace
        com1 = enlace(serialName)
        com1.enable()
        print("Comunicação client aberta! \n")

        # Carrega dados a serem enviados
        file = load_file('arquivo.png')
        num_of_packs = number_of_packs(len(file))
        

    except KeyboardInterrupt:
        print("Fechamento forçado")
        com1.disable()
        
    except Exception as erro:
        print("Ocorreu um erro na execução:\n")
        print(erro)
        com1.disable()
        

if __name__ == "__main__":
    main()