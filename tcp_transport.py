#NAME : SKANDA KRISHNAN BALASUBRAMANIAN
#PROJECT 1 Computer Communication Networks
#FILE_DESCRIPTION: ACTS as the function library for tcp protocol
#                  All three client,server and proxy use it for send msg/data and receive msg/data
#                  All Sockets are initiated and connected using functions in this file


import sys
import socket
import threading
import pickle
from os.path import exists
#tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MAX_BUF = 65507
FORMAT = 'utf-8'
DISCONNECT_MESSAGE  = "!DISCONNECT"
PUT_MSG = "put"
GET_MSG = "get"
PRINT_ENABLE = 0
HEADER = 500

#ASSERT PRINT_ENABLE =1 for more debug prints
def printf(msg):
    if(PRINT_ENABLE == 1):
        print(msg)

#START LISTENING SOCKET
def start_server_socket(NAME,IP,PORT):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ADDR = (IP,PORT)
    printf(f"[START] {NAME} at {tcp_socket} using TCP")
    tcp_socket.bind(ADDR)
    tcp_socket.listen()
    print(f"[LISTENING] : {NAME} at {ADDR}")
    return tcp_socket

#STARTT CONNECTING SOCKET
def start_client_socket(NAME,RC_ADDR):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(RC_ADDR)
    CL_ADDR = tcp_socket.getsockname()
    print(f"[CONNECTED] {NAME} at {RC_ADDR} using {CL_ADDR}")
    return tcp_socket,CL_ADDR



#ACCEPT CONNECTION
def accept_socket(tcp_socket):
    cl_conn, cl_addr = tcp_socket.accept()
    return cl_conn,cl_addr

#RECEIVE MESSAGE OVER TCP
def receive_header(conn):
    recvd_data = receive_data(conn,0,0)
    hdr = recvd_data.decode(FORMAT)
#    recvd_data = conn.recv(MAX_BUF).decode(FORMAT)
    printf(f"[TCP_TRANSPORT][Receive Header Length] = {len(recvd_data)}")
    #print(recvd_data)
    data = hdr.split()
    #print(data)
    return data

#RECEIVE DATA OVER TCP
def receive_data(conn,data_length=0,dec=1):
    data = b''

    #IMPLEMENT BUFFER PROTECTION IF Packet GETS lost
    if(data_length ==0):
        buff_size = MAX_BUF
    else:
        buff_size = min(MAX_BUF,data_length)

    while True:
        rc_data = conn.recv(buff_size)
        if rc_data == b'':
            raise Exception("[BROKEN]: Connection while Receive")
        data+=rc_data
        
        if data_length>0:
            data_length -= len(rc_data)
            if(data_length<=0):
                break
        elif len(rc_data)<MAX_BUF:
            break

    printf(f"[TCP_TRANSPORT][Receive Data Length] = {len(data)}")
    if(dec ==1):
        file = data.decode(FORMAT)
    else:
        file = data

    #return data received
    return file





#SEND MESSAGE OVER TcP
def send_header(conn,header_msg):
    hdr = header_msg.encode(FORMAT)
 #   hdr += b' ' *(HEADER - len(hdr))
    send_data(conn,hdr,0) 


#SEND DATA OVER TCP
def send_data(conn,d_data,enc=1):
    if(enc):
        data = d_data.encode(FORMAT)
    else:
        data = d_data
    sent_success = 0
    bytes_sent = 0
    while bytes_sent < (len(data)):
        sent = conn.send(data[bytes_sent:])
        if(sent ==0):
            sent_success = 0
            break
        bytes_sent += sent
        printf(f"{bytes_sent} bytes sent ")
    sent_success = 1
    return sent_success


def connection_close(conn):
    conn.close()
