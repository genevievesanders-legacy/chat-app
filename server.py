from socket import *
import json
from datetime import datetime
import time


class Server(object):
    def __init__(self, port):
        self.port = port
        self.users = dict()
        self.pending_ack = dict()

    def initiate_server(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(("", self.port))
        while True:
            msg, address = self.sock.recvfrom(1024)
            # decoded will return in format [CODE (i.e. "REG", "DEREG")| MSG]
            decoded = msg.decode()
            decoded_li = json.loads(decoded)
            decoded_li.append(address)
            print("recieved ", decoded_li, "from", address)
            self.handle_codes(decoded_li)

    # this function sends an updated table of online users to all active users
    def update_users(self):
        data = str.encode(json.dumps(self.users))
        for x in self.users:
            # remember, format for self.users[x] is [IP address, port, online boolean]
            if self.users[x][2]:
                self.sock.sendto(data, (self.users[x][0], self.users[x][1]))
                print("sent to", self.users[x])

    def check_for_msgs(self, recieved_data, file_name: str):
        code, name, address = recieved_data
        try:
            f = open(file_name, 'r+')
            lines = f.readlines()
            message_li = []
            for line in lines:
                if line > "":
                    message_li.append(line.strip())
            if message_li:
                data = str.encode(json.dumps(["OFFLINE_MSG", message_li]))
                self.sock.sendto(data, address)
                print(f"offline messages {message_li} sent to {name}")
            # TODO: clear messages here
            f.truncate(0)
            f.close()
        except OSError:
            print('error check_for_msgs os')

    def check_online(self, target_name):
        target_ip, target_port, target_online = self.users[target_name]

        if target_online:
            print("checking online status for", target_name)

            msg_li = ["ACK_REQ"]
            msg = str.encode(json.dumps(msg_li))
            self.sock.sendto(msg, (target_ip, target_port))
            self.pending_ack[target_name] = True
            time.sleep(.5)
            if self.pending_ack[target_name]:  # aka user is offline
                print(target_name, "appears to be offline")
                self.users[target_name] = [target_ip, target_port, False]

    def save_msgs(self, received_data):
        code, sender_name, target_name, private, text, address = received_data
        self.check_online(target_name)
        if self.users[target_name][2] == True: # target is online
            data = str.encode(json.dumps(["ERR", target_name, self.users]))
            self.sock.sendto(data, address)

        else: # target is offline
            file = "offline_chats/{}.txt".format(target_name)
            # get time info
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            if private:
                saved_message = f">>> PM @{sender_name}: {current_time} {text}\n"
            else:
                saved_message = f">>> Channel Message @{sender_name}: {current_time} {text}\n"
            try:
                f = open(file, 'a')
                f.write(saved_message)
                f.close()
            except OSError:
                print('error save_msg os')

    def register(self, recieved_data):
        print(recieved_data)
        code, name, (ip, port) = recieved_data
        self.pending_ack[name] = False
        file = "offline_chats/{}.txt".format(name)
        if name in self.users:  # aka returning/reregistering
            self.check_for_msgs(recieved_data, file)
        else:  # create new file for them
            try:
                open(file, 'w').close()
            except OSError:
                print('Failed creating the file')
            else:
                print(f'File {file} created')
        online = True
        self.users[name] = [ip, port, online]
        print("self.users at server reg ", self.users)
        self.update_users()

    def deregister(self, recieved_data):
        code, name, (ip, port) = recieved_data
        online = False
        self.users[name] = [ip, port, online]
        self.update_users()  # this only updates for active users (not user calling for dereg)
        msg_li = ["ACK_DEREG"]
        data = str.encode(json.dumps(msg_li))
        self.sock.sendto(data, (ip, port))
        print("sent dereg ack")

    def check_gc_ack(self, recieved_data):
        code, sender, text, address = recieved_data
        for x in self.users:
            if x != sender:
                x_ip, x_port, x_online = self.users[x]
                if x_online:
                    if self.pending_ack[x]:
                        print("did not receive gc ack from", x)
                        self.save_msgs([code, sender, x, False, text, address])

    def distrbute_gc_message(self, received_data):
        code, sender, text, address = received_data

        for x in self.users:
            if x != sender:
                x_ip, x_port, x_online = self.users[x]
                if x_online:
                    data = str.encode(json.dumps(["GC_MSG", sender, x, text]))
                    self.pending_ack[x] = True
                    self.sock.sendto(data, (x_ip, x_port))

                else:
                    # false indicates it is not a private message
                    self.save_msgs([code, sender, x, False, text, address])

    def group_chat(self, received_data):
        code, sender, text, address = received_data

        # send ACK for send_all request
        msg_li = ["ACK_SEND_ALL"]
        data = str.encode(json.dumps(msg_li))
        self.sock.sendto(data, address)

        self.distrbute_gc_message(received_data)
        time.sleep(.5)
        self.check_gc_ack(received_data)

    def handle_codes(self, recieved_data: list):
        if recieved_data[0].upper() == "REG":
            self.register(recieved_data)
        elif recieved_data[0].upper() == "DEREG":
            self.deregister(recieved_data)
        elif recieved_data[0].upper() == "MSG":
            #print("server recieved data ", recieved_data)
            self.save_msgs(recieved_data)
        elif recieved_data[0].upper() == "SEND_ALL":
            self.group_chat(recieved_data)
        elif recieved_data[0].upper() == "ACK_GC_MSG":
            print("recieved ack from 1", recieved_data[1])
            self.pending_ack[recieved_data[1]] = False
        elif recieved_data[0].upper() == "ACK_REQ_RSP":
            print("recieved ack from", recieved_data[1])
            self.pending_ack[recieved_data[1]] = False