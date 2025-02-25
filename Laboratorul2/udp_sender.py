import socket
import time
import random
# Completati cu adresa IP a platformei ESP32
PEER_IP = "192.168.89.41"
PEER_PORT = 10001

#MESSAGE = b"Salut!"
i = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while 1:
    try:
        TO_SEND = bytes(str(i),"ascii")
        sock.sendto(TO_SEND, (PEER_IP, PEER_PORT))
        print("Am trimis mesajul: ", TO_SEND)
        i=random.randint(0,1)
        time.sleep(1)
    except KeyboardInterrupt:
        break