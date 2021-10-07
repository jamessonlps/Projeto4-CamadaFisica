def build_datagram(
    type_message,
    len_packs,
    pack_sending, 
    payload,
    len_payload=0,
    id_client=b'\xff',
    id_server=b'\x00',
    crc1=b'\x00',
    crc2=b'\x01'
    ):

    """
        Recebe os parâmetros do head e retorna o datagrama
        adequadamente estruturado
    """

    head = type_message.to_bytes(1, 'big') + id_client + id_server + len_packs.to_bytes(1, 'big')

    head += pack_sending.to_bytes(1,'big') + len_payload.to_bytes(1, 'big') + pack_sending.to_bytes(1, 'big') + pack_sending.to_bytes(1, 'big') + crc1 + crc2

    if (len(payload) > 0):
        return head + payload + b'\xff\xaa\xff\xaa'

    return head
