#NAME : SKANDA KRISHNAN BALASUBRAMANIAN
#PROJECT 1 Computer Communication Networks
#FILE_DESCRIPTION: ACTS as the proxy between SERVER and CLIENT for get functions
#                  Provides the File if found in cache_files
#                  If not, requests file from server and stores it for future USE                   

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
if len(sys.argv) != 5:
    print("Usage: python cache.py <cache_port> <server_ip> <server_port> <Protocol>")
    print("Try Again")
    exit()

#Change IP for running in the internet
#CACHE_IP = "192.168.1.220"  
CACHE_IP = "localhost"


CACHE_PORT = int(sys.argv[1])
PRINT_ENABLE =0
SERVER_IP = sys.argv[2]
SERVER_PORT = int(sys.argv[3])
PROTOCOL = sys.argv[4]
HEADER = 500
FORMAT = 'utf-8'
DISCONNECT_MESSAGE  = "quit"
SERV_ADDR = (SERVER_IP,SERVER_PORT)
CACHE_ADDR = (CACHE_IP,CACHE_PORT)

CACHE_STORAGE_PATH = "cache_files"

#ASSERT PRINT_ENABLE =1 for more debug prints
def printf(msg):
    if(PRINT_ENABLE == 1):
        print(msg)



#FILE search function to search for files in the cache_files directory
def file_search(FILE_NAME):
    found = 1
    if(exists(FILE_NAME) == False):
        print(f"[ERROR] File NOT in {CACHE_STORAGE_PATH}")
        found =0
    return found
#Function to send Requested FILE to Client


def send_file_cache(PROTOCOL,file_name,client_req_msg,cl_conn,cl_addr,file_origin):
    send_ok =0
    if(PROTOCOL == "snw"):
        text_file = open(file_name,"rb")
        data = text_file.read()
        data_length = len(data)

        #SEND RESPONSE REQ to CLIENT over TCP
        cache_header = "CACHE get_response "+client_req_msg[0]+" "+str(data_length)+" "+client_req_msg[4]+" "+file_origin
        printf(cache_header)
        tcp_transport.send_header(cl_conn,cache_header)
        printf(f"Header with FILE found sent from {file_origin}")
        printf(f"Client Address {cl_addr[0]}  {cl_addr[1]}")
        text_file.close()
        text_file = open(file_name,"rb")

        #SEND FILE in 1000 byte CHUNKS over UDP with SNW
        send_ok = snw_transport.send_file(cache_snw_socket,cl_addr,data_length,text_file)
        text_file.close()
        print(f"[SUCCESS]:{client_req_msg[4]} sent from CACHE to CLIENT: {cl_addr} over SNW/UDP")
    elif(PROTOCOL == "tcp"):
        text_file = open(file_name,"r")
        data = text_file.read()
        data_length=len(data)
        printf(f"FILE SIZE = {str(data_length)} bytes")

        #SEND RESPONSE REQ to CLIENT over TCP 
        cache_header = "CACHE get_response "+client_req_msg[0]+" "+str(data_length)+" "+client_req_msg[4]+" "+file_origin
        printf(cache_header)
        tcp_transport.send_header(cl_conn,cache_header)
        printf(f"Header with FILE found sent from {file_origin}")
        
        
        #SEND FILE over TCP  Streamw
        tcp_transport.send_data(cl_conn,data)
        print(f"[SUCCESS]:{client_req_msg[4]} sent from CACHE to CLIENT:{cl_addr} over TCP")
        client_resp = tcp_transport.receive_header(cl_conn)
        printf(f"{client_resp[1]} received")
        send_ok = 1
        text_file.close()
    return send_ok


def req_frm_server(file_n,file_name):

    #CONSTRUCT MESSAGE FOR SERVER FILE REQUEST
    cache_header ="CACHE get SERVER 1 "+file_n+" 0"
    tcp_transport.send_header(cache_server_tcp_socket,cache_header)
    recv_success =0
    
    if(PROTOCOL == "tcp"):
        server_resp = tcp_transport.receive_header(cache_server_tcp_socket)
        printf(f"\nSERVER_RESP = {server_resp}")
        data_length = int(server_resp[3])
        text_file = open(file_name,"w")

        #RECEIVE DATA FROM SERVER OVER TCP
        data = tcp_transport.receive_data(cache_server_tcp_socket,data_length)
        recv_success = 1
    elif (PROTOCOL == "snw"):
        text_file = open(file_name,"wb")
        printf("Req server")
        #RECEIVE DATA FROM SERVER OVER UDP with SNW
        data,recv_success = snw_transport.recv_file(cache_server_snw_socket)
    if(recv_success ==1):

        #STORE FILE FOR FURTHER USE
        text_file.write(data)
        #text_file.write("\nClient wrote this file")
        text_file.close()
        cache_header ="CACHE get_complete SERVER 1 DONE"
        server_resp = tcp_transport.send_header(cache_server_tcp_socket,cache_header)
    return recv_success


def handle_client_request(conn,addr):
    print(f"[NEW CONNECTION]: {addr} connected")
    connected = True
    while connected:

        #REQUEST FROM CLIENT
        client_req_msg = tcp_transport.receive_header(conn)
        data_length = client_req_msg[3]
        oper = client_req_msg[1]
        printf(client_req_msg)
        if data_length and (oper=="get"):
            print(f"[RECEIVED] get REQ from CLIENT")
            file_n = client_req_msg[4]
            file_name = join(CACHE_STORAGE_PATH,client_req_msg[4])
            found = file_search(file_name)
            send_ok =0
            if(found == 1):

                #FILE IN cache_files
                file_origin = "CACHE"
                send_ok = send_file_cache(PROTOCOL,file_name,client_req_msg,conn,addr,file_origin)
            else:

                #REQUEST SERVER for the File
                print(f"[REQUEST]: Server for {file_n}")
                recv_success = req_frm_server(file_n,file_name)
                if(recv_success ==1):
                    print(f"[RECEIVED]: {file_n} from Server")
                    file_origin = "ORIGIN"

                    #FILE RECEIVED SEND FILE To CLIENT
                    send_ok = send_file_cache(PROTOCOL,file_name,client_req_msg,conn,addr,file_origin)
                else:
                    print(f"[TERMINATED]: Connection with {addr}")
                    oper = DISCONNECT_MESSAGE
                    send_ok = 0
                if(send_ok ==1):
                    print(f"[SUCCESS] {file_n} Sent to Client: {addr}")                    
                else:
                    print(f"[TERMINATED]: Connection with {addr}")
                    oper = DISCONNECT_MESSAGE
                    send_ok = 0
        if client_req_msg[1] == DISCONNECT_MESSAGE:
            server_header = "CACHE connection_closed"+client_req_msg[0]+ " 0 SUCCESS"
            connected = False
            tcp_transport.send_header(conn,server_header)
            print(f"[TERMINATED]: Connection with {addr}")
    tcp_transport.connection_close(conn)

def start_cache():
    while True:
        cl_conn, cl_addr = tcp_transport.accept_socket(cache_tcp_socket)
        print(f"Accepted Connection to {cl_addr}")

        #IMPLEMENT Threading for Multiple Client connections
        thread = threading.Thread(target=handle_client_request,args=(cl_conn,cl_addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count()-1}")





if not exists(CACHE_STORAGE_PATH):
    print(f"[ERROR]: Make cache_files directory")
    exit()

#START TCP SOCKETS For MESSAGE and DATA
cache_server_tcp_socket, ca_ser_addr = tcp_transport.start_client_socket("CACHE to Server",SERV_ADDR)
cache_tcp_socket = tcp_transport.start_server_socket("CACHE",CACHE_IP,CACHE_PORT)
if(PROTOCOL == "snw"):

    #START UDP with SNW SOCKETS For DATA
    cache_snw_socket = snw_transport.start_snw_socket("CACHE",CACHE_ADDR)
    cache_server_snw_socket = snw_transport.start_client_socket("CACHE",ca_ser_addr)
start_cache()
