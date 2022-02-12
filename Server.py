#!/usr/bin/env python3
#Simple epoll echo server 

from __future__ import print_function
from contextlib import contextmanager
import socket
import select

ServerPort = 8000   # Listening port
MAXCONN = 3000         # Maximum connections
BUFLEN = 80         # Max buffer size

#----------------------------------------------------------------------------------------------------------------
# Main server function 
def EpollServer (socket_options, address):
    
    with socketcontext (*socket_options) as server, epollcontext (server.fileno(), select.EPOLLIN) as epoll:
        server.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Allow multiple bindings to port
        server.bind(address)
        server.listen (MAXCONN)
        server.setblocking (0)
        server.setsockopt (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # Set socket to non-blocking
        print ("Listening on Port:",ServerPort)

        Client_SD = {}
        Client_Reqs = {}
        Server_Response = {}
        server_SD = server.fileno()

        while True:
            events = epoll.poll(1)

            for sockdes, event in events:
                if sockdes == server_SD:
                    init_connection (server, Client_SD, Client_Reqs, Server_Response, epoll)
                elif event & select.EPOLLIN:
                    Receive_Message (sockdes, Client_Reqs, Client_SD, Server_Response, epoll)
                elif event & select.EPOLLOUT:
                    Echo_Response (sockdes, Client_SD, Server_Response, epoll)

#----------------------------------------------------------------------------------------------------------------
# Process Client Connections
def init_connection (server, Client_SD, Client_Reqs, Server_Response, epoll):
    connection, address = server.accept()
    connection.setblocking(0)

    print ('Client Connected:', address)    #print client IP

    fd = connection.fileno()
    epoll.register(fd, select.EPOLLIN)
    Client_SD[fd] = connection
    Server_Response[fd] = ''
    Client_Reqs[fd] = ''

#----------------------------------------------------------------------------------------------------------------
# Receive a request and send an ACK with echo
def Receive_Message (sockdes, Client_Reqs, Client_SD, Server_Response, epoll):
      
    Client_Reqs[sockdes] += Client_SD[sockdes].recv (BUFLEN)

    # Make sure client connection is still open    
    if Client_Reqs[sockdes] == 'quit\n' or Client_Reqs[sockdes] == '':
        print('[{:02d}] Client Connection Closed!'.format(sockdes))
        
        epoll.unregister(sockdes)
        Client_SD[sockdes].close()

        del Client_SD[sockdes], Client_Reqs[sockdes], Server_Response[sockdes]
        return

    elif '\n' in Client_Reqs[sockdes]:
        epoll.modify(sockdes, select.EPOLLOUT)
        msg = Client_Reqs[sockdes][:-1]
        print("[{:02d}] Received Client Message: {}".format (sockdes, msg))
        
        # ACK + received string
        Server_Response[sockdes] = 'ACK => ' + Client_Reqs[sockdes]
        Client_Reqs[sockdes] = ''
#----------------------------------------------------------------------------------------------------------------
# Send a response to the client
def Echo_Response (sockdes, Client_SD, Server_Response, epoll):
    byteswritten = Client_SD[sockdes].send(Server_Response[sockdes])
    Server_Response[sockdes] = Server_Response[sockdes][byteswritten:]
    epoll.modify(sockdes, select.EPOLLIN)
    print ("Response Sent")

#----------------------------------------------------------------------------------------------------------------
# Use context manager to free socket resources upon termination
@contextmanager   # Socket Context (resource) manager
def socketcontext(*args, **kwargs):
    sd = socket.socket(*args, **kwargs)
    try:
        yield sd
    finally:
        print ("Listening Socket Closed")
        sd.close()

#----------------------------------------------------------------------------------------------------------------
# Use context manager to free epoll resources upon termination
@contextmanager # epoll loop Context manager
def epollcontext (*args, **kwargs):
    eps = select.epoll()
    eps.register(*args, **kwargs)
    try:
        yield eps
    finally:
        print("\nExiting epoll loop")
        eps.unregister(args[0])
        eps.close()
#----------------------------------------------------------------------------------------------------------------
# Start the epoll server & Process keyboard interrupt CTRL-C
if __name__ == '__main__':
    try:
        EpollServer ([socket.AF_INET, socket.SOCK_STREAM], ("0.0.0.0", ServerPort))
    except KeyboardInterrupt as e:
        print("Server Shutdown")
        exit()      # Don't really need this because of context managers