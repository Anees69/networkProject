from socket import *
import time

serverIP = "127.0.0.1"
serverPort = 8090

def start_client():
    clientSocketTCP = socket(AF_INET, SOCK_STREAM)
    clientSocketTCP.connect((serverIP, serverPort))
    print("Connected to server")
    clientSocketTCP.send(b"START\n")
    print("Sent START")

    ready_msg = clientSocketTCP.recv(1024).decode().strip()
    print("Got from server:", ready_msg)
    if ready_msg != "READY":
        clientSocketTCP.close()
        return

    clientSocketUDP = socket(AF_INET, SOCK_DGRAM)

    for i in range(0, 1000001):
        msg = (str(i) + "\n").encode()
        clientSocketUDP.sendto(msg, (serverIP, serverPort))
        if i % 100000 == 0:
            print("Sent", i)
        # the commented code below can be used to slow down the sending rate
    #     if i % 20000 == 0:
    #         time.sleep(0.02)
    # #the commented code below can be used to simulate out-of-order packets
    # for i in range(0, 1000001):
    #     msg = (str(i) + "\n").encode()
    #     clientSocketUDP.sendto(msg, (serverIP, serverPort))
  
        # if i % 100000 == 0 and i != 0:
        #     bad_msg = (str(i - 50) + "\n").encode()
        #     clientSocketUDP.sendto(bad_msg, (serverIP, serverPort))


    clientSocketTCP.send(b"END\n")
    print("Sent END")

    time.sleep(1)
    clientSocketTCP.close()
    clientSocketUDP.close()
    print("Client done.")


if __name__ == "__main__":
    start_client()
