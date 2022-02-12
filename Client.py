#!/usr/bin/env python3
from concurrent.futures import thread
import socket
import select
import sys
import os
import threading
import time

import logging
logging.getLogger().handlers.clear()
logging.basicConfig(filename="Clientout.csv",level=logging.DEBUG, format='%(message)s')

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
        sock.sendall(message) #sends the message to the server
        data = sock.recv(1024) #receives the message from the server
        end = time.time()
        total_delay = end - start
        total_requests += 1
    duration_end = time.time()
    total_duration = duration_end - start_time

    #recording results to log
    logging.info("%d, %d, %d, %f, %f, %f" % (thread_id, total_requests, total_bytes, total_duration, total_delay, total_bytes/total_duration))
    sock.close()

def main(address, port):
    server_address = (address, port)
    print(server_address)
    workers = []
    thread_count = 100
    message = "Hello World"
    requestCount = 10
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
    logging.info("Thread, Requests, Bytes, Duration, Delay, MB/s")
    main(sys.argv[1], int(sys.argv[2]))