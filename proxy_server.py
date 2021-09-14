import datetime
import socket
import os.path
import threading
#Murat ŞENOL 150117039
#Emre Yiğit 150116056

PORT = 8888
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)
BUFFER = 32768
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


def main():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.bind(ADDR) # bind to connection on ADDR = {server_ip , port}
        client.listen()
        print("[*] Initializing socket. Done.")
        print("[*] Socket bound successfully...")
        print(f"[*] Server started successfully [{PORT}]")
    except Exception as e_socket:
        print(e_socket)
    while True:
        conn, addr = client.accept() # accept new client connection
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


def handle_client(conn, addr):
    connected = True

    # while connected:

    data = conn.recv(BUFFER).decode(FORMAT) # Recieve Data

    # if len(data) == 0:
        # continue

    if data == DISCONNECT_MESSAGE: # If received Data is disconnect message
        connected = False
        conn.sendall("\nDisconnected !".encode(FORMAT)) # return message to client
        # continue

    response_line = connection_string(conn, addr, data) # get the response line from method
    if type(response_line) is bytes:
        response_first_line = response_line.decode(FORMAT).split("\r\n")[0]
        print(f"Send Message: {response_first_line} to {addr}")
        conn.sendall(response_line)
    else:
        try:
            response_first_line = response_line.split("\r\n")[0]
        except Exception as split_error:
            response_first_line = ""
            print(split_error)
            # continue

        print(f"Send Message: {response_first_line} to {addr}")
        conn.sendall(response_line.encode(FORMAT))

    conn.close()


def connection_string(conn, addr, data):
    print("\n[REQUEST]")
    # print(addr)
    first_line = data.split("\r\n")[0]
    print(f"Received Message: {first_line} from {addr}")

    first_line_split = first_line.split(' ')
    http_method = first_line_split[0]

    if http_method == "GET" and first_line.find("localhost") != -1:
        webserver = first_line_split[1].split(':')[1][2:] # to  find the webserver sting on recieved data
        port = first_line_split[1].split(':')[2].split('/')[0] # to find the port string on the received data

        print(f"webserver:{webserver}")
        print(f"port:{port}")
        if webserver == "localhost": # changing 'localhost' to ipv4 of this machine for connecting to server
            webserver = socket.gethostbyname(socket.gethostname())
        proxy_addr = (webserver, int(port))
        response_line = proxy_server(proxy_addr, conn, data, addr) # get the response line from method
    else:
        response_line = create_response_line(501, 0 , "")

    return response_line


def proxy_server(proxy_addr, conn, data, addr):
    # print(f"{proxy_addr} {conn} {addr}")
    try:

        first_line = data.split("\r\n")[0]
        first_line_split = first_line.split(' ')
        http_method = first_line_split[0]
        uri = first_line_split[1].split("/")[3]
        http_ver = first_line_split[2]
        cache_dir = os.getcwd() + "\\cache\\" + uri

        if not os.path.exists(os.getcwd() + "\\cache\\"): # crate cach dir if it does not exsist. Not creating this will give an error
            os.makedirs(os.getcwd() + "\\cache\\")        # when proxy tries to save the cache

        if uri.isdigit():
            if int(uri) > 9999: # URI Check for bounds
                response_line = create_response_line(414, 0 , http_ver)
            elif os.path.isfile(cache_dir):  # Cache hit

                # If cache hit  read from cache ,do not go to the server
                f = open(cache_dir, "rb")
                html_data = f.read()
                f.close()

                if int(len(html_data)) % 2 == 1:  # Cache hit , file not modified
                    print("---Cache hit - file was not modified\n")
                    response_line = create_response_line(200, len(html_data) , http_ver) + html_data.decode(FORMAT)
                else:  # Cache hit , but file was modified , request new file from server
                    print("\n---Cache hit - file was modified")
                    print("---Requesting new file from Server...\n")

                    try: # Cache hit , but file was modified , request new file from server
                        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        server.connect(proxy_addr) # connect to the server
                        msg = http_method + " /" + uri + " " + http_ver + "\r\n"
                        server.sendall(msg.encode(FORMAT)) # send requested uri to the server
                        print(f"Send Message: {msg} to {proxy_addr}")
                        reply = server.recv(BUFFER) # receive message from server
                        response_line = reply
                        reply = reply.decode(FORMAT)
                        reply_first_line = reply.split("\r\n")[0]
                        print(f"Received Message: {reply_first_line} from {proxy_addr}")

                        # write to cache
                        html_data = response_line.decode(FORMAT).split("\r\n\r\n")[1]

                        f = open(cache_dir, "wb")
                        f.write(html_data.encode())
                        f.close()
                    except Exception as e_connect:
                        print(f"[CONNECTION ERROR]:{e_connect}")
                        response_line = create_response_line(404, 0 , http_ver) # 404 error not found , Server is not running

            else:  # Cache miss
                try:
                    print("---Cache miss\n")
                    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server.connect(proxy_addr) # connect to the server
                    msg = http_method + " /" + uri + " " + http_ver + "\r\n"
                    server.sendall(msg.encode(FORMAT)) # send requested uri to the server
                    print(f"Send Message: {msg} to {proxy_addr}")
                    reply = server.recv(BUFFER) # receive message from server
                    response_line = reply
                    reply = reply.decode(FORMAT)
                    reply_first_line = reply.split("\r\n")[0]
                    print(f"Received Message: {reply_first_line} from {proxy_addr}")

                    # If cache missed write to cache
                    html_data = response_line.decode(FORMAT).split("\r\n\r\n")[1]

                    f = open(cache_dir, "wb")
                    f.write(html_data.encode())
                    f.close()

                except Exception as e_connect:
                    print(f"[CONNECTION ERROR]:{e_connect}")
                    response_line = create_response_line(404, 0 , http_ver) # 404 error not found , Server is not running
        else:
            response_line = create_response_line(400, 0 , http_ver)

        return response_line
    except Exception as e:
        print(e)


def create_response_line(status_code, size, http_ver):
    file_type = "text/html"

    if http_ver[:4] != "HTTP":
        http_ver = "HTTP/1.0" #Default

    if status_code == 404:
        header = http_ver + " " + "404 Not Found\r\n"
        content = "404 Not Found"
        size = len(content)
    elif status_code == 414:
        header = http_ver + " " + "414 Request-URI Too Long\r\n"
        content = "414 Request-URI Too Long"
        size = len(content)
    elif status_code == 501:  # Not Implemented
        header = http_ver + " " + "501 Not Implemented\r\n"
        content = http_ver + " " + "Implemented"
        size = len(content)
    elif status_code == 200:  # OK
        header = http_ver + " " + "200 OK\r\n"
    elif status_code == 400:  # Bad Request
        header = http_ver + " " + "400 Bad Request\r\n"
        content = "400 Bad Request"
        size = len(content)

    if status_code != 200:
        html_string = "<HTML>\n<HEAD>\n<TITLE>" + content + "</TITLE>\n</HEAD>\n<BODY>"
        content = html_string + content + "</BODY>\n</HTML>"

    header += "Date: " + str(datetime.datetime.now()) + "\r\n"
    header += "Server: HTTPServer/1.0\r\n"
    header += "Content-Length: " + str(size) + "\r\n"
    header += "Content-Type: " + file_type + "\r\n"

    if status_code == 200:  #  If status code is 200 return without content , because content is already recieved from
        return header + "\r\n"   #  server or cache

    return header + "\r\n" + content


if __name__ == "__main__":
    main()
