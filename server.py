#NAME : SKANDA KRISHNAN BALASUBRAMANIAN
#PROJECT 1 Computer Communication Networks
#FILE_DESCRIPTION: ACTS as the SERVER for CLIENT:put and CACHE:get functions

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





#Check if python script started correctly
if len(sys.argv) != 3:
    print("Usage: python server.py <server_port> <Protocol>")
    print("Try Again")
    exit()

#USE other IP for running on the NET
SERVER_IP =  "localhost"
#SERVER_IP = "169.226.22.10"
#SERVER_IP = "192.168.1.220"


SERVER_PORT = int(sys.argv[1])
PROTOCOL = sys.argv[2]

SERV_ADDR = (SERVER_IP,SERVER_PORT)
PRINT_ENABLE = 0
HEADER = 500
FORMAT = 'utf-8'
DISCONNECT_MESSAGE  = "quit"
SERVER_STORAGE_PATH = "server_files"

if not exists(SERVER_STORAGE_PATH):
    print("Make server_files directory")
    exit()

sizeofdata = ""

#ASSERT PRINT_ENABLE =1 for more debug prints
def printf(msg):
    if(PRINT_ENABLE == 1):
        print(msg)


#DISCONNECT SOCKET
def disconnect_soc(conn,addr):
    server_header = "SERVER connection_closed ORIGIN 0 SUCCESS"
    tcp_transport.send_header(conn,server_header)
    print(f"[TERMINATED]: Connection with {addr}")
    tcp_transport.connection_close(conn)
    return False



#Function to execute put request from client
def handle_put_command(conn,addr,source,data_length,file_name):
    if(PROTOCOL == "tcp"):
        d_length = int(data_length)
        printf(f"Expected Data length = {d_length} bytes")
        data = tcp_transport.receive_data(conn,d_length)
         
        #FILE Received over TCP
        print(f"[RECEIVED]: {len(data)} bytes")
        recv_ok = 1
        text_file = open(file_name,"w")
    else: 

        #FILE Received over snw/udp   
        data,recv_ok = snw_transport.recv_file(server_snw_socket)
        text_file = open(file_name,"wb")
    if(recv_ok == 0):
        print("[ERROR] : Data Not received")
        print("[TERMINATE] Connection")
        return 0
    text_file.write(data)
    #text_file.write("Server wrote this file")
    text_file.close()
    server_header ="SERVER put_response CLIENT 0 HEAD"
    tcp_transport.send_header(conn,server_header)
    return 1


#Function to handle get command from CACHE
def handle_get_command(conn,addr,source,data_length,file_name,file_n):
    if(PROTOCOL == "snw"):
        text_file = open(file_name,"rb")
        data = text_file.read()
        data_len = len(data)
        text_file.close()
        text_file = open(file_name,"rb")
        printf(f"[Receiver address] : {addr}")

        #SENDING FILE To Cache over SNW/UDP
        send_ok = snw_transport.send_file(server_snw_socket,addr,data_len,text_file)
        text_file.close()
    else:
        text_file = open(file_name,"r")
        data = text_file.read()
        data_length=len(data)
        printf(str(data_length))
        server_header = "SERVER get_response "+source+" "+str(data_length)+" "+file_n+" SERVER"
        printf(server_header)           
        tcp_transport.send_header(conn,server_header)
        printf("Header from Server to Cache Sent")

        #SENDING File to CACHE over TCP 
        tcp_transport.send_data(conn,data)
        client_resp = tcp_transport.receive_header(conn)
        printf(f"{client_resp[1]} received")
        text_file.close()
        send_ok = 1
    return send_ok

#hadnle req from both client and cache
def handle_client_command(conn,addr):
    print(f"[NEW CONNECTION]{addr} connected")
    connected = True
    while connected:
        print("[SERVER WAITING].....")
        header_msg = tcp_transport.receive_header(conn)
        printf(f"[REQ]= {header_msg}")
        destn =      str(header_msg[2])
        if(destn == "SERVER"):
            printf(f"REQ = {header_msg}")
            source =      header_msg[0]
            oper =        header_msg[1]
            data_length = header_msg[3]
            file_n =      header_msg[4]
            printf(header_msg)
            print(f"[RECVD REQ] :{oper} {file_n} from {destn} to {source}")

            #RECEIVED Put command from CLIENT
            if data_length and (oper=="put"):

                print(f"[EXECUTING] PUT for {source} at {addr}")
                file_name = join(SERVER_STORAGE_PATH,file_n)
                recv_success = handle_put_command(conn,addr,source,data_length,file_name)
                if(recv_success == 0):
                    disconnect_soc(conn,addr)
                else:
                    print(f"[SUCCESS]: {file_n} received to Server from {addr} using {PROTOCOL}")

            #RECEIVED Put command from CACHE
            if data_length and (oper=="get"):
                file_name = join(SERVER_STORAGE_PATH,file_n)
                print(f"[EXECUTING] GET for {source} at {addr}")
                send_ok = handle_get_command(conn,addr,source,data_length,file_name,file_n)

                if(send_ok == 0):
                    print("[ERROR]: Could Not send File")
                    print("[ERROR]: Terminating Conneciton")
                    disconnect_soc(conn,addr)
                else:
                    print(f"[SUCCESS]: {file_n} send from Server to {addr} using {PROTOCOL}")
            
            #DISCONNCT AND TERMINATE SOCKET
            if oper == DISCONNECT_MESSAGE:
                connected = disconnect_soc(conn,addr)
                

def start_tcp():
    while True:
        printf(f"TCP {server_tcp_socket}")
        cl_conn, cl_addr = tcp_transport.accept_socket(server_tcp_socket)
        print(f"[ACCEPT] Connection from {cl_addr}")

        #IMPLEMENT Threading for Multiple Clients and CACHEs connections
        thread = threading.Thread(target=handle_client_command,args=(cl_conn,cl_addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count()-1}")






print(f"Starting Skanda's server.py")
server_tcp_socket = tcp_transport.start_server_socket("SERVER",SERVER_IP,SERVER_PORT)
if(PROTOCOL == "snw"):
    server_snw_socket = snw_transport.start_snw_socket("SERVER",(SERVER_IP,SERVER_PORT))
    #server_snw_snd_socket = snw_transport.start_snw_socket("SERVER",(SERVER,PORT_SND))
start_tcp()

