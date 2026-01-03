from socket import *
import select
import time

serverIP = "127.0.0.1" # Localhost for testing on the same machine
serverPort = 8090

def start_server():
    serverSocketTCP = socket(AF_INET, SOCK_STREAM)
    serverSocketTCP.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Allow reuse of the address
    serverSocketTCP.bind((serverIP, serverPort))
    serverSocketTCP.listen(1)
    print(f"Server listening on {serverIP}:{serverPort}")

    while True:
        connectionSocket, addr = serverSocketTCP.accept()
        first_msg = connectionSocket.recv(1024).decode().strip()
        if first_msg == "START":
            connectionSocket.send(b"READY\n")
            break
        else:
            connectionSocket.close()

    serverSocketUDP = socket(AF_INET, SOCK_DGRAM)
    serverSocketUDP.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
    serverSocketUDP.bind((serverIP, serverPort))
    print("UDP server ready.")

    last_received = -1
    received_count = 0
    wrong_order_count = 0
    running = True

    while running:
        readable, _, _ = select.select([serverSocketUDP, connectionSocket], [], [])

        for sock in readable:
            if sock is serverSocketUDP:
                msg, clientAddr = serverSocketUDP.recvfrom(1024)
                msg_decoded = msg.decode().strip()

                try:
                    number = int(msg_decoded)
                except:
                    continue

                received_count += 1

                if last_received != -1 and number != last_received + 1:
                    wrong_order_count += 1

                last_received = number
                # Uncomment the line below to simulate processing delay
                # time.sleep(0.0001)

            elif sock is connectionSocket:
                msg = connectionSocket.recv(1024)
                if not msg:
                    running = False
                    break
                text = msg.decode().strip()
                if text == "END":
                    running = False
                    break

    print(f"Total messages received: {received_count}")
    print(f"Messages received out of order: {wrong_order_count}")

    connectionSocket.close()
    serverSocketUDP.close()
    serverSocketTCP.close()


if __name__ == "__main__":
    start_server()
