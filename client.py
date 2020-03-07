from socket import *
import sys
import threading
import re
import queue


serverName = 'localhost'
serverPort = 12000
try:
    # serverName = sys.argv[1]
    # serverPort = int(sys.argv[2])
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    success_msg = 'Welcome to the greatest messaging application ever!'
    get_block_msg = 'Invalid Password. Your account has been blocked. Please try again later'
    blocked_msg = 'Your account is blocked due to multiple login failures. Please try again later'

    command = ''
    q = queue.Queue()

    def set_private_conn(private_ip, private_port, connect_user):
        private_socket = socket(AF_INET, SOCK_STREAM)
        private_socket.bind((private_ip, private_port))
        private_socket.listen(1)
        connection, address = private_socket.accept()
        q.put((connect_user, connection))
        while True:
            private_msg = connection.recv(2048).decode()
            if private_msg != 'close the p2p connection':
                print(private_msg)
            else:
                break
        connection.close()


    def input_command():
        global command
        global clientSocket
        command = input('print the command:\n')
        if command:
            clientSocket.send(command.encode())
        else:
            clientSocket.send('nothing'.encode())


    def send_to_server(send_cmd, c_socket):
        global if_logout
        global private_list
        pattern = re.compile(r'\S+')
        content = pattern.findall(send_cmd)
        if len(content) == 0:
            pass
        elif len(content) == 1:
            if content[0] == 'whoelse':
                data = c_socket.recv(2048).decode()
                print(data)
            elif content[0] == 'logout':
                if_logout = 1
            elif content[0] == 'nothing':
                print('Error. Invalid command')
            else:
                data = c_socket.recv(2048).decode()
                print(data)
        else:
            if content[0] == 'message':
                if len(content) >= 3:
                    data = c_socket.recv(2048).decode()
                    if data != 'send successfully':
                        if data != 'send to store box':
                            print(data)
                else:
                    data = c_socket.recv(2048).decode()
                    print(data)
            elif content[0] == 'broadcast':
                data = c_socket.recv(2048).decode()
                if data != 'send successfully':
                    print(data)
            elif content[0] == 'whoelsesince':
                data = c_socket.recv(2048).decode()
                print(data)
            elif content[0] == 'block':
                data = c_socket.recv(2048).decode()
                print(data)
            elif content[0] == 'unblock':
                data = c_socket.recv(2048).decode()
                print(data)
            elif content[0] == 'startprivate':
                data = c_socket.recv(2048).decode()
                if data.startswith('Error'):
                    print(data)
                else:
                    extract_pattern = re.compile(r'[()\,\']')
                    conn_user, ip_add, port_num = re.sub(extract_pattern, '', data).split()
                    port_num = int(port_num)

                    new_private_thread = threading.Thread(target=set_private_conn, args=(ip_add, port_num, conn_user, ))
                    new_private_thread.daemon = True
                    new_private_thread.start()
                    print(f'Start private messaging with {conn_user}')
                    private_list.append(conn_user)
            else:
                data = c_socket.recv(2048).decode()
                print(data)


    def rcv_handler(rcv_socket):
        while True:
            rcv_data = rcv_socket.recv(2048).decode()
            print(rcv_data)


    while True:
        Username = input('Username: ')
        if Username == '':
            print('The username cannot be null')
        else:
            clientSocket.send(Username.encode())
            user_msg = clientSocket.recv(2048).decode()
            if user_msg == 'Right Username' or \
                    user_msg == 'This user is online. Please try another one.':
                break
            print(user_msg)

    while True:
        Password = input('Password: ')
        if Password == '':
            print('The password cannot be null')
        else:
            clientSocket.send(Password.encode())
            msg = clientSocket.recv(2048).decode()
            print(msg)
            if msg == success_msg:
                break
            if msg == get_block_msg:
                break
            if msg == blocked_msg:
                break
            if msg == 'This user is online. Please try another one.':
                break


    def set_private_rcv(i_add, p_num, p_obj):
        private_socket = socket(AF_INET, SOCK_STREAM)
        private_socket.connect((i_add, p_num))
        q.put((p_obj, private_socket))
        while True:
            try:
                rcv_private_msg = private_socket.recv(2048).decode()
                if not rcv_private_msg.startswith('close the p2p connection'):
                    print(rcv_private_msg)
                else:
                    private_socket.send('close the p2p connection'.encode())
                    print(rcv_private_msg)
                    private_list.remove(p_obj)
                    break
            except ConnectionResetError:
                pass
        private_socket.close()


    if_active = 1
    if_logout = 0
    private_list = []
    while msg == success_msg:
        send_command = threading.Thread(target=input_command)
        send_command.daemon = True
        send_command.start()
        while True:
            rcv_message = clientSocket.recv(2048).decode()
            if command.startswith('private'):
                clientSocket.recv(2048).decode()
                cmd_pattern = re.compile(r'\S+')
                cmd_content = cmd_pattern.findall(command)
                if len(cmd_content) >= 3:
                    r_user = cmd_content[1]
                    private_data = Username + ' (private): ' + ' '.join(w for w in cmd_content[2:])
                    if r_user == Username:
                        print('Error. Cannot send to self')
                        break
                    elif r_user in private_list:
                        temp_list = []
                        while not q.empty():
                            temp_list.append(q.get())
                        for m in temp_list:
                            temp_user, temp_socket = m
                            if temp_user == r_user:
                                try:
                                    temp_socket.send(private_data.encode())
                                except ConnectionResetError:
                                    print(f'{r_user} is offline')
                        for n in temp_list:
                            q.put(n)
                        break
                    else:
                        print(f'Error. {Username} has not executed startprivate with {r_user} before')
                        break
                else:
                    print('Error. Invalid command.')
                    break
            elif command.startswith('stopprivate'):
                clientSocket.recv(2048).decode()
                cmd_pattern = re.compile(r'\S+')
                cmd_content = cmd_pattern.findall(command)
                if len(cmd_content) == 2:
                    stop_user = cmd_content[1]
                    if stop_user == Username:
                        print('Error. Cannot stopprivate with self')
                        break
                    elif stop_user in private_list:
                        temp_list = []
                        while not q.empty():
                            temp_list.append(q.get())
                        for m in temp_list:
                            temp_user, temp_socket = m
                            if temp_user == stop_user:
                                try:
                                    temp_socket.send(f'close the p2p connection with {Username}'.encode())
                                    private_list.remove(stop_user)
                                except ConnectionResetError:
                                    print(f'{r_user} is offline')
                        for n in temp_list:
                            q.put(n)
                        break
                    else:
                        print(f'Error. There is no p2p session between {stop_user} and {Username}')
                        break
                else:
                    print('Error. Invalid command')
                    break
            else:
                if rcv_message == 'active':
                    send_to_server(command, clientSocket)
                    break
                elif rcv_message == 'inactive':
                    # clientSocket.close()
                    if_active = 0
                    break
                elif rcv_message.startswith('establish'):
                    _, private_obj, ip_address, port_number = rcv_message.split(' ')
                    port_number = int(port_number)

                    rcv_private_thread = threading.Thread(target=set_private_rcv, args=(ip_address, port_number, private_obj))
                    rcv_private_thread.daemon = True
                    rcv_private_thread.start()

                    private_list.append(private_obj)
                else:
                    print(rcv_message)
        if if_active == 0 or if_logout == 1:
            clientSocket.close()
            break

except Exception:
    print('You should input server_IP and server_port')

