# -*- coding: utf-8 -*-
from enlace import *
import time
import numpy as np
import time
from utils import *

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
serialName = "COM8"                    # Windows

def main():
    try:
        com2 = enlace(serialName)
        com2.enable()
        com2.rx.fisica.flush()
        server_log = open('./logs/server.txt','w')
        
        print('Comunicação serial do servidor iniciada!\n')

        handshake = True
        print('Aguardando tentativa de contato...')
        while handshake:
            # Fica em um loop enquanto não recebe handshake
            while (com2.rx.getBufferLen() < 10):
                pass
            
            server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 1 / 10\n")
            
            dtg, n_dtg = com2.getData(10)

            type_message   = dtg[0]
            len_packs      = dtg[3]
            pack_receiving = dtg[4]
            len_payload    = dtg[5]

            # Verifica tipo de mensagem e destinatário
            if (type_message == 1):
                print("Tentativa de contato recebida! Autenticando client...")
                handshake = False
                time.sleep(1)

        # Envia confirmação para o client
        datagram = build_datagram(
            type_message=2,
            len_packs=0,
            pack_sending=0,
            payload=b''
        )

        server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 2 / 10\n")

        com2.sendData(np.asarray(datagram))
        
        while com2.tx.getStatus() != len(datagram):
            pass

        print('EUREKA!!! Contanto com client estabelecido\n')
        print('Iniciando a recepção dos pacotes...\n')

        data_received = b''
        counter = 1

        while counter <= len_packs:
            # Inicia contadores 1 e 2 (de 2 e 20 segundos)
            timer1 = time.time()
            timer2 = time.time()

            # Aguarda recepção do head
            while (com2.rx.getBufferLen() < 10):
                pass

            # extraindo infos importantes
            datagram, n_datagram = com2.getData(10)

            type_message   = datagram[0]
            len_packs      = datagram[3]
            pack_receiving = datagram[4]
            len_payload    = datagram[5]

            server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + f" / receb / {type_message} / {len_payload+14} / {pack_receiving} / {len_packs}\n")
        
            # Verifica mensagem recebida
            if (type_message == 3 and pack_receiving == counter and len_payload > 0):
                print(f'Recebendo pacote {pack_receiving} de {len_packs}...')
                
                while (com2.rx.getBufferLen() < len_payload + 14):
                    now = time.time()
                    # Se passar 20s no contador 2 e o pacote não for recebido,
                    # o servidor encerra comunicação
                    if (now - timer2 > 20):
                        print('Sem resposta do client. Finalizando conexão...\n')
                        handshake = True
                        datagram = build_datagram(
                            type_message=5,
                            len_packs=0,
                            pack_sending=counter,
                            payload=b''
                        )

                        server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 5 / 10\n")

                        com2.sendData(np.asarray(datagram))

                        while com2.tx.getStatus() != len(datagram):
                            pass
                        
                        # server_log.close()
                        com2.disable()
                        return

                    # Se passar 2s no contador 1 e o pacote não for recebido,
                    # o servidor envia solicitação ao client do pacote
                    elif (now - timer1 > 2):
                        datagram = build_datagram(
                            type_message=4,
                            len_packs=0,
                            pack_sending=counter,
                            payload=b''
                        )

                        server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 4 / 10\n")

                        com2.sendData(np.asarray(datagram))

                        while com2.tx.getStatus() != len(datagram):
                            pass

                        timer1 = time.time()

                # Quando receber todo o datagrama, extrai todas as infos
                dtg, n_dtg = com2.getData(len_payload + 14)

                type_message   = dtg[0]
                len_packs      = dtg[3]
                pack_receiving = dtg[4]
                len_payload    = dtg[5]
                payload        = dtg[:-4]
                eop            = dtg[-1:-5:-1]

                # Se os dados conferem com o esperado, solicita próximo pacote
                if (eop == b'\xaa\xff\xaa\xff'):
                    print('Pacote recebido com sucesso!\n')
                    data_received += payload
                    datagram = build_datagram(
                        type_message=4,
                        len_packs=0,
                        pack_sending=counter,
                        payload=b''
                    )

                    server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 4 / 10\n")

                    com2.sendData(np.asarray(datagram))

                    while com2.tx.getStatus() != len(datagram):
                        pass

                    counter += 1
                
                # Se algum não confere, solicita o pacote novamente
                else:
                    print('EOP difere do esperado. Solicitando novamente o pacote...\n')
                    datagram = build_datagram(
                        type_message=6,
                        len_packs=0,
                        pack_sending=counter,
                        payload=b''
                    )

                    server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 6 / 10\n")

                    com2.sendData(np.asarray(datagram))

                    while com2.tx.getStatus() != len(datagram):
                        pass
            
            # Se chegou uma resposta "inesperada", solicita pacote novamente
            else:
                print('Algum erro aconteceu. Solicitando novamente o pacote...\n')
                datagram = build_datagram(
                    type_message=6,
                    len_packs=0,
                    pack_sending=counter,
                    payload=b''
                )

                server_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 6 / 10\n")

                com2.sendData(np.asarray(datagram))

                while com2.tx.getStatus() != len(datagram):
                    pass

        server_log.close()

        # Salva arquivo final
        with open('./data/resp.png', 'wb') as file:
            file.write(data_received)
        
        com2.disable()
    
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        server_log.close()
        com2.disable()

    except KeyboardInterrupt:
        print("Fechamento forçado")
        server_log.close()
        com2.disable()
        
if __name__ == "__main__":
    main()