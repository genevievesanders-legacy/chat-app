import os
import argparse
import ipaddress
from server import Server
from client import Client

def parse_args():
    parser = argparse.ArgumentParser(description="Process command line options.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--server",
                        metavar="port",
                        nargs=1,
                        help="description for server start up")
    group.add_argument("-c", "--client",
                        metavar=("name", "server-ip",
                                 "server-port", "client-port"),
                        nargs=4,
                        help="description for client start up")
    args = parser.parse_args()
    return parser, args

def valid_port(port):
    try:
        if 1024 <= int(port) <= 65535:
            return True
        else:
            print("Port number should be an integer between 1024 and 65535!")
            return False
    except ValueError:
        print("Port number should be an integer between 1024 and 65535!")
        return False

def valid_ip(ip):
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        print("You should enter a valid IP address!")
        return False
    return True

def main():
    parser, args = parse_args()
    try:
        if args.server:
            port = args.server[0]
            if valid_port(port):
                #print("valid port, initializing server")
                print(">>> [Server initializing...]")
                Server(int(port)).initiate_server()
        elif args.client:
            name, server_ip, server_port, client_port = args.client
            if valid_ip(server_ip) and valid_port(server_port) and valid_port(client_port):
                print("valid input")
                Client(name, server_ip, int(server_port), int(client_port)).start()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("Adios!")
        os._exit(0)


if __name__ == "__main__":
    main()