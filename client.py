from activity import NetworkActivity
from utils.str_functions import get_list_from_json, hash_file, \
    get_real_path, get_generic_path
import json
import socket
import threading
import os
import time
import string
import random
import traceback
from xml.dom.minidom import parse
import xml.dom.minidom
from loghandler import LogHandler, ClientAlreadyExists
import constants
from utils.str_functions import str_diff
from pathlib import Path
import constants

def get_file_info_helper(file_name, client):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(client)
    client_socket.send("{0}".format(NetworkActivity.FILE_INFO).encode())
    client_socket.recv(1024)
    client_socket.send(json.dumps({"file" : file_name}).encode())
    data = client_socket.recv(1024000)
    client_socket.close()
    return get_list_from_json(data)

class FailedToConnect(Exception):
    pass

# TODO: Maybe check if paths are symlinks. If they are, make a hold to ask the
# user what to do (skip/copy) (but only if the link points to a destination that is not in the list of files)

# Maybe preserve permissions and file meta data?
class ClientManager:
    clients = []
    busy_clients = []
    transfer_threads = {}
    inactive_threads = []
    current_client = None
    client_logger = None
    progress_logger = None
    list_logger = None

    def busy_client_check(func):
        def func_wrapper(context, *args, **kwargs):
            try:
                if context.current_client not in context.busy_clients:
                    return func(context, *args, **kwargs)
                else:
                    print("Client is busy")

            except:
                print(traceback.print_exc())
                exit(-1)

        return func_wrapper

    def __init__(self):
        self.client_logger = LogHandler               \
        (                                             \
            log_type=LogHandler.LOG_CLIENTCONNECTION  \
        )
        self.progress_logger = LogHandler(log_type=LogHandler.LOG_FILEPROGRESS)
        self.list_logger = LogHandler(log_type=LogHandler.LOG_FILELIST)

    def reestablish_connection(self, hash):
        connections = self.client_logger.log_instance.get_clients()
        failed_connections = []
        for conn in connections:
            try:
                self.connect_to_server(conn[0], conn[1], conn[2], False)

            except FailedToConnect as e:
                failed_connections.append(conn)

        if len(failed_connections):
            return constants.CONNECT_FAILED, failed_connections
        else:
            return constants.CONNECT_SUCCESS, []

    def resume_transfers(self):
        for conns in self.clients:
            file_info = self.progress_logger.get_outstanding_files(conns[1])

            if len(file_info):
                self.fetch_file_data                                 \
                (                                                    \
                    conns, file_info[4], file_info[5], file_info[4], \
                    file_info[3]                                     \
                )

            remaining_list, dest_path = self.list_logger.get_file_list()
            if len(remaining_list):
                for l in remaining_list:
                    self.fetch_file_data                          \
                    (                                             \
                        conns, get_real_path(l), dest_path, l[2:] \
                    )

        return

    def connect_to_server(self, address, port=10031, hash=None, new_conn=True):
        try:
            client_hash = None
            if hash:
                client_hash = hash

            if (address, port) in [i[0] for i in self.clients]:
                raise FailedToConnect("connection already established")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((address, port))
            sock.settimeout(None)
            if not hash:
                sock.send(F"{NetworkActivity.SERVER_NAME}".encode())
                sock.recv(1024)
                sock.send(b"{\"blank\": \"0\"}")
                client_hash = sock.recv(1024000).decode()
            sock.close()

            temp_addr = ((address, port), client_hash)

            self.current_client = temp_addr
            self.clients.append(self.current_client)

            self.client_logger.write_to_log(client_addr=temp_addr[0][0], \
                    client_port=temp_addr[0][1], \
                    client_hash=temp_addr[1])

        except socket.timeout:
            raise FailedToConnect("timed out")

        except ConnectionRefusedError:
            raise FailedToConnect("connection refused")

    def fetch_file_data(self, client, orig_path, dest_path, root, pos=0):
        #get information of file
        info = get_file_info_helper(orig_path, client[0])
        name = info['name']
        size = info['size']
        hash = info['hash']

        #create the destination path for the new file
        root = root.replace(constants.GENERIC_PATH, os.path.sep)
        basename = str(Path(root).parent)
        new_path = ''.join([dest_path, str_diff(orig_path, basename)])

        if not os.path.exists(str(Path(new_path).parent)):
            os.makedirs(str(Path(new_path).parent))
        new_file = open(new_path, 'wb')

        #request file data
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(client[0])
        client_socket.send(F"{NetworkActivity.FILE_DATA}".encode())
        client_socket.recv(1024)
        client_socket.send(json.dumps({"file": orig_path, "pos": pos}).encode())

        #receive data and write to file
        # TODO: Create a timeout in case the server goes down
        data = client_socket.recv(1024000)

        #This is for the logging function to keep track of how far the transfer is
        log_pos = len(data)
        self.list_logger.set_target_attr(client[1])
        self.list_logger.clean_log()
        while data:
            new_file.write(data)
            self.progress_logger.write_to_log           \
            (                                           \
                file_name=name,                         \
                file_size=size,                         \
                file_hash=hash,                         \
                transferred=log_pos,                    \
                orig_path=str(Path(orig_path).parent),  \
                dest_path=str(Path(new_path).parent),   \
                client_conn=client[1]                   \
            )
            data = client_socket.recv(1024000)
            input("::")
            log_pos += len(data)

        new_file.close()
        client_socket.close()

        # verify that file has been transferred correctly
        # TODO: Do some corrective action if transfer failed
        if hash_file(new_path) != hash:
            print("File transfer failed!")
            # do more error correcting here

        else:
            self.progress_logger.clean_log()

    def client_transfer_thread(self, client, orig_path, dest_path, pos=0):
        # TODO: Check if there are any uncopied files to finish (once again put holds if there are any problems)
        if orig_path[0] == '1':
            # fetch list of files from server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(client[0])
            client_socket.send(F"{NetworkActivity.ROOT_SUBDIR_RECURSIVE}" \
                                                 .encode())
            client_socket.recv(1024)
            client_socket.send(json.dumps({"file": orig_path[2:]}).encode())
            data = client_socket.recv(1024000)
            files = ''

            while data:
                files += data.decode()
                data = client_socket.recv(1024000)

            client_socket.close()

            files = files.split("/::/")

            self.list_logger.write_to_log   \
            (                               \
                file_list=files,            \
                dest_dir=dest_path,         \
                client_conn=client[1]       \
            )

            for f in files:
                self.fetch_file_data                                   \
                (                                                      \
                    client, get_real_path(f), dest_path, orig_path[2:] \
                )


        else:
            self.fetch_file_data                                            \
            (                                                               \
                client, get_real_path(orig_path), dest_path, orig_path[2:], \
                pos                                                         \
            )

        # remove client from busy_clients
        for c in range(0, len(self.busy_clients)):
            if self.busy_clients[c] == client:
                del self.busy_clients[c]
                break

    @busy_client_check
    def transfer_data(self, orig_path, dest_path, pos=0):
        self.busy_clients.append(self.current_client)
        self.transfer_threads[self.current_client] = threading.Thread   \
        (                                                               \
            target=self.client_transfer_thread,                         \
            args=(self.current_client, orig_path, dest_path, pos)       \
        )
        self.transfer_threads[self.current_client].start()

    def get_clients(self):
        return clients

    # TODO: Use the client's hash to switch client
    def switch_client(self, client):
        if client in self.clients:
            self.current_client = client
        else:
            raise Exception("Client not in list")

    @busy_client_check
    def get_file_info(self, file_name):
        return get_file_info_helper(file_name, self.current_client)

    @busy_client_check
    def get_directory_contents(self, directory):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(self.current_client[0])
        client_socket.send(F"{NetworkActivity.ROOT_SUBDIR}".encode())
        client_socket.recv(1024)
        client_socket.send(json.dumps({"file": directory}).encode())
        data = client_socket.recv(1024000)
        client_socket.close()
        return data.decode()

    @busy_client_check
    def get_roots(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(self.current_client[0])
        client_socket.send(F"{NetworkActivity.ROOTS}".encode())
        client_socket.recv(1024)
        client_socket.send(b"{\"blank\": \"0\"}")
        data = client_socket.recv(1024000)
        client_socket.close()
        return data.decode()
