#NAME : SKANDA KRISHNAN BALASUBRAMANIAN
#PROJECT 1 Computer Communication Networks
#FILE_DESCRIPTION: ACTS as the function library for snw/udp protocol
#                  All three client,server and proxy use it for send msg/data and receive msg/data
#                  All Sockets are initiated and connected using functions in this file
#                  STOP and WAIT implemented in this FILE
import sys
import socket
import threading
import pickle
from os.path import exists

#tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HEADER = 500
FORMAT = 'utf-8'
DISCONNECT_MESSAGE  = "!DISCONNECT"
PUT_MSG = "put"
GET_MSG = "get"
RESP_SIZE = 4
CHUNK_SIZE = 1000
LEN_SIZE  = 10

PRINT_ENABLE = 0
 
#ASSERT PRINT_ENABLE =1 for more debug prints
def printf(msg):
    if(PRINT_ENABLE == 1):
        print(msg)


#START SERVER SOCKET
def start_snw_socket(NAME,UDP_ADDR):
    snw_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    snw_socket.settimeout(1)
    #ADDR = (IP,PORT)
 #   print(f"[Starting SNW Socket] {NAME} at {snw_socket}")
    snw_socket.bind(UDP_ADDR)
    print(f"[LISTENING]: SNW Socket at {NAME}: {snw_socket.getsockname()}")
    return snw_socket

#START CLIENT SOCKET
def start_client_socket(NAME,UDP_ADDR):
    snw_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    snw_socket.settimeout(1)
    snw_socket.bind(UDP_ADDR)
    #tcp_socket.bind(ADDR)
    print(f"[STARTED] SNW Socket at {NAME}: {snw_socket.getsockname()}")
    return snw_socket

#SEND LEN OF DATA
def send_len(snw_socket,data_length,RCV_ADDR):
    length = (str(data_length)).encode(FORMAT)
    length += b' ' *(LEN_SIZE - len(length))
    snw_socket.sendto(length,RCV_ADDR)
    print(f"[SENT] Length of file: {data_length} to {RCV_ADDR}")

#RECV LEN OF DATA
def recv_len(snw_socket):
    len_data = 0
    first_rec = 0
    try:
        len, snd_address_info = snw_socket.recvfrom(LEN_SIZE)
        printf(f"Length of Data received from {snd_address_info}")
    except:
        print("[TERMINATED] Did not receive LEN")
        return b"0",len_data,first_rec
    len_data = int(len.decode(FORMAT))

    print(f"[RECEIVED] LENGTH of File = {len_data} bytes")
    try:
        data,snd_address_info = snw_socket.recvfrom(CHUNK_SIZE)
        msg = "ACK".encode(FORMAT)
        #print(f"First data is {str(data)}")
        snw_socket.sendto(msg,snd_address_info)
        first_rec = 1
        print(f"[RECEIVED] : No.1 Packet")
        print(f"[SENT]: Packet No.1 ACK")
        return data,len_data,first_rec
    except socket.timeout():
        first_rec = 0
        printf("First CHUNK NOT Received")
        print("[TERMINATE] DID NOT RECEIVE FIRST 1000 bytes....")
        return b"0",len_data,first_rec

#SEND 1000BYTE CHUNK
def send_chunk(snw_socket,data,RCV_ADDR):
    snw_socket.sendto(data,RCV_ADDR)
    printf(f"Packet sent to {RCV_ADDR}")
    ack_recvd =0
    try:
        b_resp, rcv_address_info = snw_socket.recvfrom(RESP_SIZE)
        resp = b_resp.decode(FORMAT)
        if(resp == "ACK"):
            ack_recvd = 1            
            return ack_recvd
    except socket.timeout:
        print("Did not receive ACK. [Terminating]")
        return ack_recvd

#RECV 1000BYTE CHUNK
def recv_chunk(snw_socket):
    chnk_recvd = 0
    try:
        data, snd_address_info = snw_socket.recvfrom(CHUNK_SIZE)
        msg = ("ACK".encode(FORMAT))
        snw_socket.sendto(msg,snd_address_info)
        chnk_recvd = 1
        return (data,chnk_recvd)
    except socket.timeout:
        print("[ERROR]: DATA not received")
        print("[TERMINATED] : Data transmission prematurely")
        return (b"0",chnk_recvd)

#SEND FILE USING send_len and send_chunk
def send_file(snw_socket,RCV_ADDR,data_len,file_obj):
    send_file_success = 0
    send_len(snw_socket,data_len,RCV_ADDR)
    chunk = b' ' *(CHUNK_SIZE)
    num_packet = 0
    while len(chunk) == CHUNK_SIZE:
        chunk = file_obj.read(CHUNK_SIZE)
        printf(f"Length of Chunk {len(chunk)}")
        if(len(chunk) !=0):
            pad_chunk =chunk+  b' ' *(CHUNK_SIZE - len(chunk))
            ack_rcvd = send_chunk(snw_socket,pad_chunk,RCV_ADDR)
            num_packet +=1
            print(f"[SENT]: Packet No.{num_packet}")
            if(ack_rcvd == 0):
                send_file_success = 0
                return send_file_success
            else:
                print(f"[RECEIVED]: ACK for Packet No.{num_packet}")
    send_file_success = 1
    msg = ("FIN".encode(FORMAT))
    snw_socket.sendto(msg,RCV_ADDR)
    print(f"[SENT] FIN to {RCV_ADDR}")
    return send_file_success

#RECEIVE File using recv_len recv_chunk    
def recv_file(snw_socket):
    recv_file_success = 0
    data,data_length,first_chunk = recv_len(snw_socket)
    if(first_chunk == 0):
        recv_file_success = 2
        return b"0",recv_file_success
    data_length -= CHUNK_SIZE
    pckt_cnt = 1 
    while data_length > 0:
        chnk,chnk_recvd = recv_chunk(snw_socket)
        data += chnk
        data_length-= CHUNK_SIZE
        pckt_cnt +=1
        printf(f"[SENT] Packet No.{pckt_cnt} ACK")
        if(chnk_recvd == 0):
            pckt_cnt -=1
            return b"0",recv_file_success
        print(f"[RECEIVED] :Packet No.{pckt_cnt}")
        print(f"[SENT]: ACK for Packet No.{pckt_cnt}")

    recv_file_success = 1
    b_fin_data,rcv_address_info =  snw_socket.recvfrom(RESP_SIZE)
    fin_data = b_fin_data.decode(FORMAT)
    if(fin_data =="FIN"):
        print("[FINISH] FIN received from Sender")
    return data,recv_file_success

    


