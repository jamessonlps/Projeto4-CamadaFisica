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

serialName = "COM7"

def main():
    try:
        com1 = enlace(serialName)
        com1.enable()
        com1.rx.fisica.flush()
        print('Comunicação serial do client iniciada!\n')

        # Carrega imagem
        with open('./data/small.png','rb') as file:
            txBuffer = file.read()
        
        client_log = open('./logs/client.txt','w')

        # Monta payloads para envio
        payloads = []
        for i in range(0, len(txBuffer), 114):
            payloads.append(txBuffer[i : i+114])
            
        len_packs = len(payloads)

        print("Dados para envio carregados.\n")

        handshake = True
        while handshake:
            print('Tentando se conectar ao servidor...')

            # Envia o datagrama e inicia contagem do tempo
            datagram = build_datagram(
                type_message=1,
                len_packs=len_packs,
                pack_sending=0,
                payload=b''
            )

            client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 1 / 10\n")

            com1.sendData(np.asarray(datagram))
            while com1.tx.getStatus() != len(datagram):
                pass

            t0_handshake = time.time()
            while (com1.rx.getBufferLen() < len(datagram)):
                if (time.time() - t0_handshake >= 5):
                    break
            
            if (com1.rx.getBufferLen() == len(datagram)):
                client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 2 / 10\n")

                response, n_response = com1.getData(len(datagram))
                if (response[0] == 2):
                    handshake = False
                    print('EUREKA!!! Servidor contatado disponível!\n')
            else:
                print('Ocorreu um erro. Conectando novamente...')

        print('Iniciando a transmissão de dados...\n')

        counter = 1
        index_sent = 0

        while (counter <= len_packs):
            
            # Prepara pacote e executa tentativa de envio
            datagram = build_datagram(
                type_message=3,
                len_packs=len_packs,
                pack_sending=counter,
                payload=b'',
                len_payload=len(payloads[counter-1])
            )
            print(f'Enviando pacote {counter} de {len_packs} pacotes')

            client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + f" / envio / 3 / {len(payloads[counter-1])+14} / {counter} / {len_packs}\n")
            
            com1.sendData(np.asarray(datagram))

            while com1.tx.getStatus() != len(datagram):
                pass

            dtg = build_datagram(
                type_message=3,
                len_packs=len_packs,
                pack_sending=counter,
                payload=payloads[counter-1]
            )
            com1.sendData(np.asarray(dtg))

            while com1.tx.getStatus() != len(dtg):
                pass
            
            # Inicia os dois contadores (um de 5 e outro de 20 segundos)
            timer_1 = time.time()
            timer_2 = time.time()

            while (com1.rx.getBufferLen() < 10):
                now = time.time()
                
                # Se o contador 1 passar de 5s e o client não receber confirmação,
                # ele reenvia o mesmo pacote
                if (now - timer_1 >= 5):
                    print('\nSem resposta do servidor. Tentando um novo envio...')

                    client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + f" / envio / 3 / {len(payloads[counter-1])+14} / {counter} / {len_packs}\n")
                    
                    com1.sendData(np.asarray(dtg))

                    while com1.tx.getStatus() != len(dtg):
                        pass
                    timer_1 = time.time()

                # Se o contador 2 passar de 20 segundos, envia uma mensagem do 
                # tipo 5 (time out) e finaliza a conexão
                elif (now - timer_2 >= 20):
                    datagram = build_datagram(
                        type_message=5,
                        len_packs=len_packs,
                        pack_sending=counter,
                        payload=b''
                    )

                    client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / envio / 5 / 10\n")

                    com1.sendData(np.asarray(datagram))

                    while com1.tx.getStatus() != len(datagram):
                        pass
                    print('\nTempo de conexão excedeu o limite! Encerrando conexão...\n')
                    
                    client_log.close()
                    
                    com1.disable()
                    return

            # Verifica resposta recebida do servidor
            if (com1.rx.getBufferLen() == 10):
                response, n_response = com1.getData(10)
                # Se o envio foi ok, passa para o próximo pack
                if (response[0] == 4):
                    client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 4 / 10\n")

                    index_sent = counter
                    counter += 1
                    
                    if counter > len_packs:
                        print("Último pacote enviado com sucesso!")
                    
                    else:
                        print(f"Pacote {counter-1} enviado com sucesso. Preparando pacote {counter}...")
                
                # Se deu erro, não atualiza o contador
                elif (response[0] == 6):

                    client_log.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + " / receb / 6 / 10\n")

                    print('Ocorreu algum erro. Tentando enviar novamente...')
                    counter = index_sent
            else:
                print('Ocorreu algum erro. Tentando enviar novamente...')

        print('\nEnvio de dados finalizado com sucesso!')
        client_log.close()
        com1.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        client_log.close()
        com1.disable()

    except KeyboardInterrupt:
        print("Fechamento forçado")
        client_log.close()
        com1.disable()
        

if __name__ == "__main__":
    main()