import time
import numpy         as np
from   enlace    import *
from   random        import randint
from   utils  import build_head, build_payloads, extract_datagram_info, load_file, number_of_packs
from constants import *

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
    handshake = True
    receiving_data = False
    data = b''
    
    try:
        com2 = enlace(serialName)
        com2.enable()
        # com2.tx.fisica.flush()
        com2.rx.fisica.flush()
        print("Servidor inicializado!")
        print("\nAguardando tentativa de contato...")

        while handshake:
            # Fica em um loop enquanto não recebe handshake
            while com2.rx.getBufferLen() < 14:
                time.sleep(0.2)
                pass

            if com2.rx.getBufferLen() >= 14:
                rx, n_rx = com2.getData(14)
                rx_info = extract_datagram_info(rx)
                
                id_server = rx_info["id_server"]
                len_packs = rx_info["len_packs"]
                
                # Verifica tipo de mensagem e destinatário
                if ((rx_info["type_message"] == 1) and (id_server == ID_SERVER)):
                    print("Tentativa de contato recebida!")
                    handshake = False
                    receiving_data = True
                    time.sleep(1)
                    
                    # Envia confirmação ao client
                    head = build_head(type_message=2)
                    datagram = b''.join([head, EOP])
                    com2.sendData(datagram)

                    # Fica no loop enquanto aguarda conclusão do envio
                    while com2.tx.getStatus() < 14:
                        time.sleep(0.2)
                        pass

                    print(f"Comunicação com client ok! Preparando recepção de {len_packs} pacotes...")
                    break


                elif id_server != ID_SERVER:
                    print(f"Erro: ID esperado: {ID_SERVER}. ID recebido: {id_server}")

        counter = 1
        while receiving_data:
            # Inicia contadores 1 e 2 (de 2 e 20 segundos)
            timer_1 = time.time()
            timer_2 = time.time()

            # Aguarda recepção do head
            while com2.rx.getBufferLen() < 10:
                pass

            # Head recebido
            head, n_head = com2.getData(10)
            head_info = extract_datagram_info(head)

            # extraindo infos importantes
            type_message   = head_info["type_message"]
            len_packs      = head_info["len_packs"]
            pack_receiving = head_info["pack_sending"]
            len_payload    = head_info["type_ref"]


            # Verifica mensagem recebida
            if ((type_message == 3) and (counter == pack_receiving)):
                print(f"Recebendo pacote {counter} de {len_packs}")
                len_datagram = 14 + len_payload
                
                while com2.rx.getBufferLen() < len_datagram:
                    # Se passar 20s no contador 2 e o pacote não for recebido,
                    # o servidor encerra comunicação
                    now = time.time()
                    if (time - timer_2 > 20):
                        print("Sem resposta do cliente. Encerrando comunicação...")
                        head = build_head(type_message=5)
                        time_response = b''.join([head, EOP])
                        com2.sendData(time_response)
                        
                        time.sleep(0.2)
                        receiving_data = False
                        break

                    # Se passar 2s no contador 1 e o pacote não for recebido,
                    # o servidor envia solicitação ao client do pacote
                    elif (time - timer_1 > 2):
                        head = build_head(type_message=4, pack_sending=counter)
                        time_response = b''.join([head, EOP])
                        com2.sendData(time_response)

                        time.sleep(0.2)

                        timer_1 = time.time()

                # Quando receber todo o datagrama
                rx, n_rx = com2.getData(len_datagram)

                # Extrai demais infos
                rx_info = extract_datagram_info(rx)
                payload = rx_info["payload"]
                eop     = rx_info["eop"]

                # Se os dados conferem com o esperado
                if ((eop == EOP) and (len(payload) == len_payload)):
                    print(f"Parcote {counter} recebido com sucesso!")
                    # Atualiza contador, informação completa e devolve ok ao client
                    counter += 1
                    data = b''.join([data, payload])
                    head = build_head(type_message=4, pack_sending=counter)
                    ok_response = b''.join([head, EOP])
                    com2.sendData(ok_response)

                    time.sleep(0.2)

                # Se algum não confere, solicita o pacote novamente
                else:
                    print("Algum erro aconteceu. Solicitando novamente o pacote...")
                    head = build_head(type_message=6, pack_sending=counter, resend_pack=counter)
                    error = b''.join([head, EOP])
                    com2.sendData(error)

                    time.sleep(0.2)

        print("Todos os pacotes foram recebidos com sucesso!")
        
        # Salva arquivo
        with open("./data/received.png", 'wb') as file:
            file.write(data)

        com2.disable()
        print("Comunicação encerrada.")

    except KeyboardInterrupt:
        print("\nPrograma fechado a força")
        com2.disable()
        
    except Exception as erro:
        print("Ocorreu um erro na execução:\n")
        print(erro)
        com2.disable()

        
if __name__ == "__main__":
    main()
