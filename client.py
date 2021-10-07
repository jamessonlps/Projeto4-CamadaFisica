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
serialName = "COM7"                    # Windows



def main():
    handshake = True
    transfer_data = False
    try_again = False
    try:
        # Cria objeto enlace
        com1 = enlace(serialName)
        com1.enable()
        # com1.tx.fisica.flush()
        com1.rx.fisica.flush()
        print("Comunicação client aberta! \n")

        # Carrega dados a serem enviados
        file = load_file('./data/small.png')
        num_of_packs = number_of_packs(len(file))
        payloads = build_payloads(file=file)
        print("Dados carregados. Iniciando tentativa de comunicação com servidor...")

        while handshake:
            # Prepara pack do handshake
            head = build_head(type_message=1, len_packs=num_of_packs)
            init_pack = b''.join([head, EOP])
            
            # Envia o handshake e inicia contagem do tempo
            com1.sendData(init_pack)
            t0_handshake = time.time()

            # Aguarda resposta do server
            while (com1.rx.getBufferLen() < 14):
                now = time.time()
                if now - t0_handshake >= 5:
                    print("Tentativa de contato sem resposta. Deseja tentar novamente? (S/N)")
                    choice = input()
                    if ((choice == 'S') or (choice == 's')):
                        print("Tentando contatar server novamente...")
                        t0_handshake = time.time()
                        break
                    
                    elif ((choice == 'N') or (choice == 'n')):
                        print("\nTudo bem. Vamos encerrar a comunicação...")
                        handshake = False
                        break

                    else:
                        print("Comando inválido. Encerrando comunicação...")
                        handshake = False
                        break

            # Analisa resposta ao receber o pacote inteiro
            if com1.rx.getBufferLen() == 14:
                rx, n_rx = com1.getData(14)
                rx_info = extract_datagram_info(rx)
                if ((rx_info["type_message"] == 2) and (rx_info["eop"] == EOP)):
                    handshake = False
                    transfer_data = True
                    print("Servidor contatado! Iniciando envio de dados...\n")
                elif rx_info["eop"] != EOP:
                    print(EOP)
                    print(rx_info["eop"])
                    print("EOP difere do esperado, algum erro ocorreu. Tentando novamente...")

        counter = 1
        last_pack_sent = counter - 1

        while transfer_data:
            if (counter <= num_of_packs):
                # Prepara pacote e executa tentativa de envio
                print('oi')
                head = build_head(
                    type_message=3, 
                    len_packs=num_of_packs, 
                    pack_sending=counter, 
                    type_ref=len(payloads[last_pack_sent])
                )
                payload = payloads[last_pack_sent]
                datagram = b''.join([head, payload, EOP])
                print(f"Enviando pacote {counter} de {num_of_packs}...")

                com1.sendData(datagram)
                time.sleep(0.1)

                # Inicia os dois contadores (um de 5 e outro de 20 segundos)
                timer_1 = time.time()
                timer_2 = time.time()

                # Contagem de tempo enquanto aguarda resposta do server
                while com1.rx.getBufferLen() < 14:
                    now = time.time()
                    # Se o contador 1 passar de 5s e o client não receber confirmação,
                    # ele reenvia o mesmo pacote
                    if now - timer_1 > 5:
                        print("\nA resposta do servidor está demorando...")
                        print(f"Reenviando pacote {counter}...")
                        com1.sendData(datagram)
                        # atualiza contador 1
                        time.sleep(0.2)
                        timer_1 = time.time()
                    
                    # Se o contador 2 passar de 20 segundos, envia uma mensagem do 
                    # tipo 5 (time out) e finaliza a conexão
                    elif now - timer_2 > 20:
                        print("Limite de tempo excedido. Encerrando comunicação...")
                        head = build_head(type_message=5)
                        datagram = b''.join([head, EOP])
                        com1.sendData(datagram)
                        # com1.disable()
                        transfer_data = False
                        break

                # Verifica resposta recebida do server
                if com1.rx.getBufferLen() == 14:
                    rx, n_rx = com1.getData(14)
                    rx_info = extract_datagram_info(datagram=rx)
                    # Se o envio foi ok, passa para o próximo pack
                    if ((rx_info["type_message"] == 4) and (rx_info["eop"] == EOP)):
                        print(f"Pacote {counter} enviado com sucesso. Preparando pacote {counter+1}...")
                        counter += 1
                        last_pack_sent += 1
                    
                    # Se deu erro, não atualiza o contador
                    elif (rx_info["type_message"] == 6):
                        print(f"Erro ao enviar o pacote {counter}. Reenviando...\n")
                        counter = rx_info["resend_pack"]
                        last_pack_sent = counter - 1

                    elif (rx_info["eop"] != EOP):
                        print("EOP difere do esperado. Comunicação comprometida...")
                        break


            else:
                print("O envio dos dados foi concluído!")
                print("Encerrando comunicação...")
        
        com1.disable()

    except KeyboardInterrupt:
        print("Fechamento forçado")
        com1.disable()
        
    except Exception as erro:
        print("Ocorreu um erro na execução:\n")
        print(erro)
        com1.disable()
        

if __name__ == "__main__":
    main()