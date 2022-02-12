#!/usr/bin/env python3
from concurrent.futures import thread
import socket
import select
import sys
import os
import threading
import time

import logging

from flask import request
logging.getLogger().handlers.clear()

#global variables
workers = []
thread_count = 1000
bufferSize = 1025
requestCount = 50

logging.basicConfig(filename="Clientout"+str(thread_count)+".csv",level=logging.DEBUG, format='%(message)s')
#----------------------------------------------------------------------------------------------------------------

def clientThead(server_address, requestCount, message, thread_id):
    print("Starting client thread")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    message = message.encode()
    print("Connected to server")
    # record transfer information
    total_bytes = 0
    total_delay = 0
    total_requests = 0
    total_duration = 0

    # record the start time
    start_time = time.time()

    # start sending requests
    for i in range(requestCount):
        start = time.time()
        total_bytes = sys.getsizeof(message)
        sock.send(message) #sends the message to the server
        data = sock.recv(1024) #receives the message from the server
        end = time.time()
        total_delay = end - start
        total_requests += 1
    sock.send(b'quit\n')
    duration_end = time.time()
    total_duration = duration_end - start_time
    average_delay = total_delay / total_requests

    #recording results to log
    logging.info("%d, %d, %d, %f, %f, %f, %f" % (thread_id, total_requests, total_bytes, total_duration, total_delay, total_bytes/total_duration, average_delay))
    # sock.close()

def main(address, port):
    server_address = (address, port)
    print(server_address)
    #fill message with random characters according to the buffersize
    message = "a" * (bufferSize-2)+"\n"
    print("Starting %d threads" % thread_count)
    for i in range(thread_count):
        t = threading.Thread(target=clientThead, args=(server_address, requestCount, message, i))
        t.start()
        workers.append(t)

    for t in workers:
        t.join()
    

if __name__ == "__main__":
    #take command line arguments for address and port
    if len(sys.argv) != 3:
        print('usage: %s <address> <port>' % sys.argv[0])
        sys.exit(1)
    logging.info("Thread, Requests, Bytes, Duration, Delay, MB/s, Average Delay")
    main(sys.argv[1], int(sys.argv[2]))