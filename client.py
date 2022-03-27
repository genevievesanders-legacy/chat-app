from socket import *
import threading
import json
import time
import os

class Client():
    def __init__(self, name, server_ip, server_port, client_port):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port
        self.done = False
        self.peers = dict()
        self.waiting_msg_ack = False
        self.offline = False
        self.printing = True
        self.dereg = False
        self.registered = False
        self.mutex = threading.Lock()  # mutext lock for self.pending


    def handle_ack_req(self):
        msg_li = ["ACK_REQ_RSP", self.name]
        msg = str.encode(json.dumps(msg_li))
        self.sock.sendto(msg, (self.server_ip, self.server_port))

    def send_all(self,code):
        text = " ".join(code[1:])
        msg_li = ["SEND_ALL", self.name, text]
        msg = str.encode(json.dumps(msg_li))
        self.waiting_msg_ack = True
        x = 5
        while self.waiting_msg_ack and x > 0:
            self.sock.sendto(msg, (self.server_ip, self.server_port))
            time.sleep(.5)
            x -= 1
        if self.waiting_msg_ack:
            print(">>> [Server not responding.]")
        else:
            print(">>> [Message received by Server.]")

    def handle_offline_err(self, code):
        acronym, target_name, updated_peers = code
        print(f">>> [Client {target_name} exists!!]")
        self.update_peers(updated_peers)

    def collect_offline_messages(self, code):
        acronym, msg_li = code
        print(">>> You have unread messages.")
        for x in msg_li:
            print(x)

    def receive_message(self, code, sender_address):
        acronym, sent_user, recieving_user, private, text = code
        ip, port = sender_address
        if private:
            print(f">>> PM @{sent_user}: {text}")
        else:
            (f">>> Channel Message @{sent_user}: {text}")

        # send ack
        msg_li = ["ACK_MSG"]
        data = str.encode(json.dumps(msg_li))
        self.sock.sendto(data, (ip, port))

    def receive_gc_message(self, code, address):
        acronym, sent_user, receiving_user, text = code
        ip, port = address
        print(f">>> Channel Message @{sent_user}: {text}")
        # print(code, type(code))
        # send ack
        msg_li = ["ACK_GC_MSG", receiving_user]
        data = str.encode(json.dumps(msg_li))
        self.sock.sendto(data, (ip, port))

    def send_message(self, code):
        peer_name = code[1]
        try:
            ip, port, online_status = self.peers[peer_name]
            text = " ".join(code[2:])
            msg_li = ["MSG", self.name, peer_name, True, text]
            msg = str.encode(json.dumps(msg_li))
            self.sock.sendto(msg, (ip, port))
            self.waiting_msg_ack = True
            time.sleep(.5)
            if self.waiting_msg_ack:  # aka user is offline
                print(f">>> [No ACK from @{peer_name}, message sent to server.]")
                self.sock.sendto(msg, (self.server_ip, self.server_port))
            elif peer_name == self.name:  # successful self message
                print(f">>> [Self-message received.]")
            else:
                print(f">>> [Message received by @{peer_name}.]")
            self.waiting_msg_ack = False
        except KeyError:
            print(f"No such user @{peer_name} is registered.")

    def deregistration(self):
        msg_li = ["DEREG", self.name]
        msg = str.encode(json.dumps(msg_li))
        x = 5
        while not self.dereg and x > 0:
            self.sock.sendto(msg, (self.server_ip, self.server_port))
            time.sleep(.5)
            x -= 1
        # print("self.dereg ", self.dereg)
        if not self.dereg:
            print(">>> [Server not responding]")
            print(">>> [Exiting]")
        else:
            print(">>> [You are Offline. Bye.]")
        self.offline = True

    def handle_codes(self, code: list, address: tuple):
        # print("handle code receieved: ", code)
        self.printing = True
        if len(code) == 2 and code[0].upper() == "DEREG" and code[1] == self.name:
            self.deregistration()

        elif code[0].upper() == "ACK_DEREG":
            self.dereg = True

        elif code[0].upper() == "SEND":
            self.send_message(code)

        elif code[0].upper() == "MSG":  # recieving messages
            self.receive_message(code, address)

        elif code[0].upper() == "GC_MSG":  # recieving gc messages
            self.receive_gc_message(code, address)

        elif code[0].upper() == "ACK_MSG" or code[0].upper() == "ACK_SEND_ALL":
            self.waiting_msg_ack = False

        elif code[0].upper() == "OFFLINE_MSG":
            self.collect_offline_messages(code)

        elif code[0].upper() == "SEND_ALL":
            self.send_all(code)

        elif code[0].upper() == "ERR":
            self.handle_offline_err(code)

        elif code[0].upper() == "ACK_REQ_RSP":
            print("get to ackreqrsp")
            self.handle_ack_req()
            print("handled")

        self.printing = False

    def update_peers(self, data):
        self.printing = True
        update = False
        if self.peers != data:
            update = True
            self.peers = data

        if not self.registered:  # for first time update/registration
            self.registered = True
            print(f">>> [Welcome @{self.name}, You are registered.]")
        if update:
            print(">>> [Client table updated.]")
        if not self.peers[self.name][2]:  # online boolean set to false
            print(">>> [You are Offline. Bye.]")
        self.printing = False

    def input(self):
        while not self.done:
            while not self.printing:
                cmd = input(">>> ")
                cmd_li = cmd.split()
                # print("input self offline", self.offline)
                if not self.offline:
                    if cmd_li[0].upper() in ["DEREG", "SEND", "SEND_ALL"]:
                        self.handle_codes(cmd_li, address=())
                    elif cmd_li[0].upper() == "PEERS":
                        print(self.peers)
                elif cmd_li[0].upper() == "REG":
                    self.register()

    def listen(self):
        while not self.done:
            msg, address = self.sock.recvfrom(1024)
            decoded = msg.decode()
            decoded_tab = json.loads(decoded)
            if not self.offline:
                if decoded[0] == "{":  # dictionary structure -> signals server user db overwrite
                    self.update_peers(decoded_tab)
                else:  # code/msg structure
                    self.handle_codes(decoded_tab, address)

    def register(self):
        self.offline = False
        self.dereg = False
        msg_li = ["REG", self.name]
        msg = str.encode(json.dumps(msg_li))
        self.sock.sendto(msg, (self.server_ip, self.server_port))

    def stop(self):
        self.done = True
        print(f"Client @{self.name} has exited.")
        try:
            os._exit(1)
        except:
            print("Exception")

    def start(self):
        self.register()

        listening = threading.Thread(target=self.listen, name=f"{self.name}-listening", daemon=True)
        sending = threading.Thread(target=self.input, name=f"{self.name}-sending", daemon=True)
        listening.start()
        sending.start()

        try:
            sending.join()
            listening.join()
        except KeyboardInterrupt:
            print(" >>> [Keyboard Interrupt detected; silent leave initiated]")
        finally:
            self.stop()