import numpy as np
from .globals import *


def load_file(path):
    with open(path, 'rb') as file:
        content = file.read()
        return bytearray(content)



def number_of_packs(len_bytes:int, max_size:int=MAX_SIZE_PAYLOAD):
    """
        Recebe o total de bytes que o arquivo contém e retorna
        quantos pacotes serão montados com o limite de até {max_size}
    """
    prop = len_bytes // max_size
    n    = int(len_bytes / max_size)
    if prop == 0:
        return n
    else:
        return n + 1



def build_payloads(file:bytes, max_size:int=MAX_SIZE_PAYLOAD):
    """
        Recebe o arquivo em bytes e retorna uma lista com todos os 
        payloads já divididos em tamanhos de até {max_size} bytes.
    """
    payloads = []
    # Número de pacotes a serem enviados
    len_packs = number_of_packs(len(file))

    # Constrói cada payload e preenche a lista
    for i in range(0, len_packs):
        if i == len_packs - 1:
            payload = file[ i*max_size : -1 ]
        else:
            payload = file[ i*max_size : (i+1)*max_size ]
        # os payloads menores que 114 são preenchidos com b'\x00'
        if len(payload) < max_size:
            payload = b''.join([payload, b'\x00'*(max_size - len(payload))])
        
        payloads.append(payload)
    
    return payloads



def build_packs(head:bytes, payloads:list):
    """
        Retorna uma lista com os datagramas do arquivo a serem enviados.
    """
    return [b''.join([head, payload, EOP] for payload in payloads)]



def build_head(
    type_message,
    id_client=ID_CLIENT,
    id_server=ID_SERVER,
    len_packs:int=0,
    pack_sending:int=0,
    type_ref:int=0,
    resend_pack:int=0,
    last_pack_received:int=0,
    crc1:int=0,
    crc2:int=0,
):
    """
        Recebe os parâmetros que constrói o head e o retorna
        formatado em bytes. A maioria dos parâmetros, por padrão,
        foram definidos como zero por dependerem do tipo de mensagem.
    """
    params = [type_message, id_client, id_server, len_packs, pack_sending, type_ref, resend_pack, last_pack_received, crc1, crc2]
    head = [int_to_bytes(number=n) for n in params]
    return b''.join(head)



def extract_datagram_info(datagram:bytes):
    """
        Retorna um dicionário com todas as informações do
        dataframe, em que cada informação é retornada em bytes.
    """
    info = {
        "type_message":       datagram[0], # h0
        "id_client":          datagram[1], # h1
        "id_server":          datagram[2], # h2
        "len_packs":          datagram[3], # h3
        "pack_sending":       datagram[4], # h4
        "type_ref":           datagram[5], # h5
        "resend_pack":        datagram[6], # h6
        "last_pack_received": datagram[7], # h7
        "crc1":               datagram[8], # h8
        "crc2":               datagram[9], # h9
        "payload":            datagram[10:-4],
        "eop":                datagram[-4:]
    }
    return info



def int_to_bytes(number:int):
    """
        Converte inteiro para bytes
        (evitar repetição do 'byteorder' no código)
    """
    return int.to_bytes(number, byteorder='little')



def bytes_to_int(number:bytes):
    """
        Converte bytes para inteiro
        (evitar repetição do 'byteorder' no código)
    """
    return int.from_bytes(number, byteorder='little')