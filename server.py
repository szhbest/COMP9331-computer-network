from socket import *
import sys
import threading
import time
import re


# correct credentials
credentials = {}
with open('credentials.txt') as f:
    for line in f:
        name, pw = line.replace('\n', '').split(' ')
        credentials[name] = pw

serverPort = 12000
block_duration = 60
timeout = 200
try:
    # serverPort = int(sys.argv[1])
    # block_duration = int(sys.argv[2])
    # timeout = int(sys.argv[3])

    ol_clients = {}
    ol_clients_add = {}

    block_dict = {}
    store_msg = {}
    login_history = {}
    for i in credentials:
        block_dict[i] = []
        store_msg[i] = []
        login_history[i] = {'login': -1, 'logout': -1}

    success_msg = 'Welcome to the greatest messaging application ever!'
    get_block_msg = 'Invalid Password. Your account has been blocked. Please try again later'
    blocked_msg = 'Your account is blocked due to multiple login failures. Please try again later'

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('localhost', serverPort))
    serverSocket.listen(1)
    print('Server is ready for listening:')


    def sleep(s_user, store_ps):
        global block_duration
        global credentials
        time.sleep(block_duration)
        credentials[s_user] = store_ps


    def block_user(b_user):
        global credentials
        if b_user in credentials:
            store_password = credentials[b_user]
            # 0 means block
            credentials[b_user] = 0
            time_block = threading.Thread(target=sleep, args=(b_user, store_password, ))
            time_block.start()


    def invalid_log(user, fail_times):
        if fail_times < 3:
            invalid_msg = 'Invalid Password. Please try again'
            fail_times += 1
        else:
            invalid_msg = get_block_msg
            fail_times = 1
            block_user(user)
        return fail_times, invalid_msg


    def send_handler(rcv_username, send_data):
        global ol_clients
        ol_clients[rcv_username].send(send_data.encode())


    def send_to_client(rcv_command, send_conn, send_name):
        global ol_clients
        global credentials
        global block_dict
        global store_msg
        global ol_clients_add
        pattern = re.compile(r'\S+')
        content = pattern.findall(rcv_command)
        if len(content) == 1:
            if content[0] == 'nothing':
                pass
            elif content[0] == 'whoelse':
                online_list = '\n'.join(c for c in ol_clients if c != send_name)
                if online_list:
                    send_conn.send(online_list.encode())
                else:
                    send_conn.send('No other users online'.encode())
            elif content[0] == 'logout':
                data = send_name + ' logged out'
                del ol_clients[send_name]
                for client in ol_clients:
                    if send_name not in block_dict[client]:
                        send_thread = threading.Thread(target=send_handler, args=(client, data))
                        send_thread.start()
            else:
                send_conn.send('Error. Invalid command'.encode())
        else:
            if content[0] == 'message':
                if len(content) >= 3:
                    rcv_user = content[1]
                    data = send_name + ': ' + ' '.join(w for w in content[2:])
                    if rcv_user in ol_clients:
                        if rcv_user != send_name:
                            if send_name not in block_dict[rcv_user]:
                                send_thread = threading.Thread(target=send_handler, args=(rcv_user, data))
                                send_thread.start()
                                send_conn.send('send successfully'.encode())
                            else:
                                send_conn.send('Your message could not be delivered as the recipient has blocked you'.encode())
                        else:
                            send_conn.send('The receiver can not be yourself.'.encode())
                    else:
                        if rcv_user in credentials:
                            if send_name not in block_dict[rcv_user]:
                                store_msg[rcv_user].append(data)
                                send_conn.send('send to store box'.encode())
                            else:
                                send_conn.send('Your message could not be delivered as the recipient has blocked you'.encode())
                        else:
                            send_conn.send('The receiver is an invalid user.'.encode())
                else:
                    send_conn.send('Error. Invalid command'.encode())
            elif content[0] == 'broadcast':
                data = send_name + ': ' + ' '.join(w for w in content[1:])
                other_users = 0
                is_blocked_by_sb = 0
                for client in ol_clients:
                    if client != send_name:
                        other_users = 1
                        if send_name not in block_dict[client]:
                            send_thread = threading.Thread(target=send_handler, args=(client, data))
                            send_thread.start()
                        else:
                            is_blocked_by_sb = 1
                if other_users == 1 and is_blocked_by_sb == 0:
                    send_conn.send('send successfully'.encode())
                elif other_users == 1 and is_blocked_by_sb == 1:
                    send_conn.send('Your message could not be delivered to some recipients'.encode())
                else:
                    send_conn.send('No other client online'.encode())
            elif content[0] == 'whoelsesince':
                if len(content) == 2:
                    try:
                        since_time = int(content[1])
                        current_time = time.time()
                        past_time_list = []
                        for client in login_history:
                            if client != send_name:
                                if login_history[client]['login'] != -1:
                                    past_time_list.append(client)
                                else:
                                    if login_history[client]['logout'] != -1 and \
                                            current_time - login_history[client]['logout'] <= since_time:
                                        past_time_list.append(client)
                        if past_time_list:
                            past_user = '\n'.join(p for p in past_time_list)
                            send_conn.send(past_user.encode())
                        else:
                            send_conn.send(f'No other users has logged in with the past {since_time} seconds'.encode())
                    except ValueError:
                        send_conn.send('Error. You should input a number'.encode())
                else:
                    send_conn.send('Error. Invalid command'.encode())
            elif content[0] == 'block':
                if len(content) == 2:
                    rcv_user = content[1]
                    if rcv_user not in credentials:
                        send_conn.send('Error. Cannot find the person'.encode())
                    else:
                        if rcv_user == send_name:
                            send_conn.send('Error. Cannot block self'.encode())
                        else:
                            if rcv_user not in block_dict[send_name]:
                                block_dict[send_name].append(rcv_user)
                            send_conn.send(f'{rcv_user} has been blocked'.encode())
                else:
                    send_conn.send('Error. Invalid command'.encode())
            elif content[0] == 'unblock':
                if len(content) == 2:
                    rcv_user = content[1]
                    if rcv_user not in credentials:
                        send_conn.send('Error. Cannot find this user'.encode())
                    else:
                        if rcv_user == send_name:
                            send_conn.send('Error. Cannot unblock self'.encode())
                        elif rcv_user not in block_dict[send_name]:
                            send_conn.send('Error. This user was not already blocked'.encode())
                        else:
                            block_dict[send_name].remove(rcv_user)
                            send_conn.send(f'Has unblocked {rcv_user}'.encode())
                else:
                    send_conn.send('Error. Invalid command'.encode())
            elif content[0] == 'startprivate':
                if len(content) == 2:
                    rcv_user = content[1]
                    if rcv_user not in credentials:
                        send_conn.send('Error. Cannot find this user'.encode())
                    else:
                        if rcv_user == send_name:
                            send_conn.send('Error. Cannot establish TCP with self'.encode())
                        elif rcv_user not in ol_clients:
                            send_conn.send(f'Error. {rcv_user} is offline'.encode())
                        else:
                            if send_name not in block_dict[rcv_user]:
                                send_conn.send(f'{rcv_user} {ol_clients_add[rcv_user]}'.encode())

                                extract_pattern = re.compile(r'[()\,\']')
                                ip_add, port_num = re.sub(extract_pattern, '', str(ol_clients_add[rcv_user])).split()

                                temp_conn = ol_clients[rcv_user]
                                temp_conn.send(f'establish {send_name} {ip_add} {port_num}'.encode())

                                # private_socket = socket(AF_INET, SOCK_STREAM)
                                # private_socket.connect((ip_add, port_num))
                                # send_conn.send('Has established'.encode())
                            else:
                                send_conn.send(f'Error. {rcv_user} has blocked you'.encode())
                else:
                    send_conn.send('Error. Invalid command'.encode())
            else:
                send_conn.send('Error. Invalid command'.encode())


    def rcv_handler(conn, add):
        global serverSocket
        global credentials
        global ol_clients
        # global timeout
        global block_dict
        global login_history
        global private_list
        if_active = 0
        command = ''
        count = 1
        if_online = 0

        # a timeout thread to tell whether the client is active
        def if_timeout(connect):
            nonlocal if_active
            nonlocal command
            try:
                command = connect.recv(2048).decode()
            except ConnectionAbortedError:
                pass
            if_active = 1

        while True:
            username = conn.recv(2048).decode()
            if username in ol_clients:
                conn.send('This user is online. Please try another one.'.encode())
                if_online = 1
                break
            if username in credentials:
                conn.send('Right Username'.encode())
                break
            conn.send('Invalid Username. Please try again'.encode())

        while True:
            password = conn.recv(2048).decode()
            if credentials[username] == password:
                if if_online == 1:
                    wel_msg = 'This user is online. Please try another one.'
                    conn.send(wel_msg.encode())
                    break
                wel_msg = success_msg

                # record user's connection socket
                ol_clients[username] = conn
                # record user's IP address and port number
                ol_clients_add[username] = add

            elif credentials[username] == 0:
                wel_msg = blocked_msg
            else:
                count, wel_msg = invalid_log(username, count)

            conn.send(wel_msg.encode())

            if wel_msg == success_msg:
                # time of login
                login_history[username]['login'] = time.time()

                # to inform other online users
                login_info = username + ' logged in'
                for c in ol_clients:
                    if c != username and username not in block_dict[c]:
                        login_thread = threading.Thread(target=send_handler, args=(c, login_info))
                        login_thread.start()

                # to receive offline messages:
                if store_msg[username]:
                    resend_msg = '\n'.join(s_msg for s_msg in store_msg[username])
                    resend_thread = threading.Thread(target=send_handler, args=(username, resend_msg))
                    resend_thread.start()
                    store_msg[username] = []
                break
            if wel_msg == get_block_msg:
                break
            if wel_msg == blocked_msg:
                break

        while wel_msg == success_msg:
            rcv_command = threading.Thread(target=if_timeout, args=(conn, ))
            rcv_command.daemon = True
            rcv_command.start()
            rcv_command.join(timeout)
            if if_active == 1:
                conn.send('active'.encode())
                if_active = 0
                send_to_client(command, conn, username)
            else:
                conn.send('inactive'.encode())
                del ol_clients[username]
                conn.close()
                break
            if not ol_clients or command == 'logout':
                conn.close()
                login_history[username]['logout'] = time.time()
                login_history[username]['login'] = -1
                break


    while True:
        connection, address = serverSocket.accept()
        new_thread = threading.Thread(target=rcv_handler, args=(connection, address, ))
        new_thread.start()

# input error raise
except Exception:
    print('You should input server_port, block_duration and timeout.')