import socket
import threading
import datetime
import sys
#Murat ŞENOL 150117039
#Emre Yiğit 150116056

if sys.argv[1:]:  # take command line argument to specify port
    PORT = int(sys.argv[1])
else:
    PORT = 8080

SERVER = socket.gethostbyname(socket.gethostname())
# SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def create_response_line(msg):
    msg_split = msg.split(" ")
    file_type = "text/html"

    html_size = msg_split[1]
    html_ver = msg_split[2]
    try:
        html_size = int(html_size[1:])  # URL is not an integer
    except Exception as url_not_int:
        header = html_ver + " " + "400 Bad Request\r\n"
        content = "400 Bad Request"
        size = len(content)

        content = "<HTML>\n<HEAD>\n<TITLE>" + content + "</TITLE>\n</HEAD>\n<BODY>" + content + "</BODY>\n</HTML>"

        header += "Date: " + str(datetime.datetime.now()) + "\r\n"
        header += "Server: HTTPServer/1.0\r\n"
        header += "Content-Length: " + str(size) + "\r\n"
        header += "Content-Type: " + file_type + "\r\n"

        return header + "\r\n" + content

    if msg_split[0] == "HEAD" or msg_split[0] == "PUT" or msg_split[0] == "POST" or msg_split[0] == "PATCH" or \
            msg_split[0] == "DELETE" or msg_split[0] == "CONNECT":# Status Code 501,method is not GET but a valid HTTP method
        header = html_ver + " " + "501 Not Implemented\r\n"
        content = "501 Not Implemented"
        size = len(content)
    elif msg_split[0] != "GET":  # Status Code 400
        header = html_ver + " " + "400 Bad Request\r\n"
        content = "400 Bad Request"
        size = len(content)
    elif msg_split[0] == "GET" and 100 <= html_size <= 20000:  # Status code 200 OK
        header = html_ver + " " + "200 OK\r\n"
        content = str(html_size) + "\n" + "a" * (html_size - 60 - 2 * len(str(html_size)))
        size = len(content)
    elif msg_split[
        0] == "GET" and html_size < 100 or html_size > 20000:  # Status Code 400 ,method is GET but size not in bounds
        header = html_ver + " " + "400 Bad Request\r\n"
        content = "400 Bad Request"
        size = len(content)
    else:  # Status Code 400 ,invalid methods
        header = html_ver + " " + "400 Bad Request\r\n"
        content = "400 Bad Request"
        size = len(content)

    #Fill the html with appropriate data
    html_string = "<HTML>\n<HEAD>\n<TITLE>" + str(html_size) + "</TITLE>\n</HEAD>\n<BODY>"
    content = html_string + content + "</BODY>\n</HTML>"

    header += "Date: " + str(datetime.datetime.now()) + "\r\n"
    header += "Server: HTTPServer/1.0\r\n"
    header += "Content-Length: " + str(size) + "\r\n"
    header += "Content-Type: " + file_type + "\r\n"

    return header + "\r\n" + content


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    # while connected:
    msg = conn.recv(2048).decode(FORMAT) # Receive message from client
    if msg:
        msg = msg.split('\r\n')[0]  # first row
        print(f"Received Message: '{msg}' from {addr[1]}")

        if msg == DISCONNECT_MESSAGE: # if message is disconnect message disconnect client and return the message
            conn.sendall(DISCONNECT_MESSAGE.encode(FORMAT))
            connected = False
            # continue

        response_line = create_response_line(msg)
        response_first_line = response_line.split("\r\n")[0] # first line of response for printing
        print(f"Send Message: '{response_first_line}' to {addr[1]}")
        conn.sendall(response_line.encode(FORMAT)) # sendall to client

    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {ADDR}")
    while True:
        conn, addr = server.accept() #Server Starts to listen on this connection and adress
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}") # # of active connections (Active threads - 1 [This thread])


print("[STARTING] server is starting...")
start()

