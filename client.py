#NAME : SKANDA KRISHNAN BALASUBRAMANIAN
#PROJECT 1 Computer Communication Networks
#FILE_DESCRIPTION: ACTS as the application for the user for get and put functions
#                  All put requests sent to SERVER
#                  All get requests sent to CACHE proxy

#MESSAGE STRUCTURE Between Application
#header_message_construct = ["SOURCE","OPERATION","DEST","SIZEOFDATA","FILENAME","FILE_ORIGIN"]

import sys
import socket
import threading
import tcp_transport
import pickle
import snw_transport
from os.path import exists
from os.path import join


if len(sys.argv) != 6:
    print("Usage: python client.py <server_ip> <server_port> <cache_ip> <cache_port> <Protocol>")
    print("Try Again")
    exit()


PRINT_ENABLE =0

CLIENT_PORT = 8000
SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
CACHE_IP = sys.argv[3]
CACHE_PORT = int(sys.argv[4])
PROTOCOL = sys.argv[5]

CLIENT_IP = "localhost"
#CLIENT_IP = "192.168.1.220"

HEADER = 500
FORMAT = 'utf-8'
DISCONNECT_MESSAGE  = "quit"
SERV_ADDR = (SERVER_IP,SERVER_PORT)
CACHE_ADDR = (CACHE_IP,CACHE_PORT)
CLIENT_ADDR = (CLIENT_IP,CLIENT_PORT)
CLIENT_STORAGE_PATH = "client_files"

def file_search(FILE_NAME):
    found = 1
    if(exists(FILE_NAME) == False):
        print("[NOT FOUND] File not Found")
        found =0
    return found

#ASSERT PRINT_ENABLE =1 for more debug prints
def printf(msg):
    if(PRINT_ENABLE == 1):
        print(msg)

#SEE if client_files exist in the directory
if not exists(CLIENT_STORAGE_PATH):
    print("Make client_files directory")
    exit()



#START and CONNECT CLIENT to SERVER AND CACHE over TCP
client_header = ["SOURCE","OPERATION","DEST","DATASIZE","FILENAME","FILESOURCE"]
client_server_tcp_socket, cl_ser_addr = tcp_transport.start_client_socket("CLIENT to Server",SERV_ADDR)
client_cache_tcp_socket, cl_cach_addr = tcp_transport.start_client_socket("CLIENT to Cache",CACHE_ADDR)

#START SNW/UDP Sockets for DATA Transfer
if(PROTOCOL == "snw"):
    client_server_snw_socket = snw_transport.start_client_socket("Client to Server",cl_ser_addr)
    client_cache_snw_socket = snw_transport.start_client_socket("Client to Cache",cl_cach_addr)

found = 1
oper="none"
while True:
    command = input("Enter a command:  ")
    if command.find("get") >=0:

        #GET Command from the USER
        oper = "get"   
        file_n = command.replace("get ","")
        file_name = join(CLIENT_STORAGE_PATH,file_n)
        found = 1
    elif command.find("put")>=0:

        #GET Command from the USER
        oper ="put"
        file_n = command.replace("put ","")
        file_name = join(CLIENT_STORAGE_PATH,file_n)
        #Search if file exists in client_files
        found = file_search(file_name)
    elif command.find("quit")>=0:
         
        #QUIT Program Disconnect sockets
        oper = "quit"
        found = 1
    else:
        print("invalid command")
        oper = "none"
    if(found ==0):
        oper = "none"

    #HANDLE PUT REQUEST
    if(oper =="put"):
        print(file_name)
        if(PROTOCOL == "snw"):
            text_file = open(file_name,"rb")
        else:
            text_file = open(file_name,"r")
        data = text_file.read()
        data_length = len(data)
        printf(f"Open file {file_name} {data_length}")

        #SEND MESSAGE TO SERVER Over TCP
        client_header = "CLIENT put SERVER "+str(data_length)+" "+file_n +" CLIENT"
        tcp_transport.send_header(client_server_tcp_socket,client_header)
        printf("Sending Client PUT Header")
        print(f"[REQUEST]: {file_n} to SERVER: {SERV_ADDR}")
        
        #SEND FILE OVER SNW UDP
        if(PROTOCOL == "snw"):
            text_file.close()
            text_file = open(file_name,"rb")
           
            send_success = snw_transport.send_file(client_server_snw_socket,SERV_ADDR,data_length,text_file)
            text_file.close()
        #SEND FILE OVER TCP
        elif(PROTOCOL == "tcp"):
            tcp_transport.send_data(client_server_tcp_socket,data)
            server_resp = tcp_transport.receive_header(client_server_tcp_socket)
            printf(f"{server_resp[1]} received")
            send_success = 1
            text_file.close()
        #client_header = "CLIENT "+DISCONNECT_MESSAGE+" SERVER 0 0"
        #tcp_transport.send_header(client_server_socket,client_header)
        if(send_success == 0):
            print("[TERMINATE] No ACK received from SERVER")
            oper = DISCONNECT_MESSAGE
        else:
            print(f"[SUCCESS] {file_n} sent to SERVER: {SERV_ADDR}")
            oper ="none"
    
    #Handle Get command from USER
    elif oper == "get":
        printf(file_name)
        client_header ="CLIENT get CACHE 1 "+file_n
        
        #SEND MESSAGE Over TCP
        tcp_transport.send_header(client_cache_tcp_socket,client_header)
        cache_resp = tcp_transport.receive_header(client_cache_tcp_socket)
        print(f"[REQUEST]: {file_n} from CACHE: {CACHE_ADDR}")
        data_length = int(cache_resp[3])

        #SEND DATA Over TCP
        if(PROTOCOL == "tcp"):
            text_file = open(file_name,"w")
            data = tcp_transport.receive_data(client_cache_tcp_socket,data_length)
            recv_success = 1
        
        #SEND DATA Over SNW/UDP
        elif (PROTOCOL == "snw"):
            text_file = open(file_name,"wb")
            data,recv_success = snw_transport.recv_file(client_cache_snw_socket)

        if(recv_success ==1):
            text_file.write(data)
            #text_file.write("\nClient wrote this file")
            client_header ="CLIENT get_complete CACHE 1 DONE"
            tcp_transport.send_header(client_cache_tcp_socket,client_header)
            print(f"[RECEIVED] : {file_n} from {cache_resp[5]}")
        else:
            print("[CLOSE] Connection")
            oper = DISCONNECT_MESSAGE
        text_file.close()
    #DISCONNECT CLIENT from SERVER and CACHE
    if(oper ==DISCONNECT_MESSAGE):
        client_header = "CLIENT quit SERVER 1 0 0"
        tcp_transport.send_header(client_server_tcp_socket,client_header)
        print(f"[TERMINATED]: Connection to SERVER: {SERV_ADDR}")
        client_header = "CLIENT quit CACHE 1 0 0"
        tcp_transport.send_header(client_cache_tcp_socket,client_header)
        print(f"[TERMINATED] Connection to CACHE: {CACHE_ADDR}") 
        exit()
