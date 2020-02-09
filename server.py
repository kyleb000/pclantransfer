import socket
import threading
import select
import json
import time
import activity
from activity import NetworkActivity
from utils.str_functions import get_list_from_json
import traceback
import os
import pathlib
import hashlib
from loghandler import LogHandler, ServerNameSet
import random
import string
import constants

# TODO: put a number before all paths to let the client determine if it's a folder, file or symlink
# TODO: Log the roots for when the program has to recover from a previous session
# TODO: Let the user set the listening port
# TODO: Let the user set a name for the server so it makes resuming easier
# TODO: Don't start the server with __init__ rather make a separate function. Maybe the user
# does not want to run a server
class FileServer:
    roots = activity.roots
    root_parents = activity.root_parents
    connections = {}
    closed_connections = []
    opened_files = {}
    server_socket = None
    listener_thread = None
    closer_thread = None
    run = True
    close_run = True
    logger = None
    server_name = activity.server_name

    def open_server(self, name=""):

        self.logger = LogHandler(log_type=LogHandler.LOG_SERVER)

        try:
            server_hash = name + ':' + ''.join(random.SystemRandom().choice( \
                                      string.ascii_uppercase + \
                                      string.digits + \
                                      string.ascii_lowercase \
                                  )for _ in range(11))
            self.logger.write_to_log(hash=server_hash, override=False)
            self.server_name[0] = server_hash
        except ServerNameSet:
            self.server_name[0] = self.logger.log_instance.get_hash()

        self.run = True
        self.close_run = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', 10031))

        self.listener_thread = threading.Thread \
        (                                       \
            target=self.listen_for_connections  \
        )
        self.listener_thread.start()

        self.closer_thread = threading.Thread       \
        (                                           \
            target=self.close_finished_connections  \
        )
        self.closer_thread.start()


    # Listen for incoming connectons and forward the connecton to a thread
    def listen_for_connections(self):
        self.server_socket.listen(5)
        data = ''
        read_list = [self.server_socket]

        # listen during the runtime of the program
        while self.run:

            try:

                # this makes the server listen in non-blocking mode
                readable, writable, errored = select.select(read_list, [], [], 1)
                for s in readable:
                    if s is self.server_socket:

                        # accept connection
                        client_socket, address = self.server_socket.accept()

                        # create a thread and pass connection to the thread
                        self.connections[address] = threading.Thread    \
                        (                                               \
                            target=self.deal_with_client,               \
                            args=(client_socket, address)               \
                        )
                        self.connections[address].start()
            except:
                pass

        for key, value in self.connections.items():
            value.join()

    def close(self):
        self.run = False
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        self.listener_thread.join()
        self.close_run = False
        self.closer_thread.join()
        self.roots.clear()
        self.root_parents.clear()

    # # TODO: Log root
    # TODO: Determine if root is file or folder
    def add_root(self, root):

        #first check if path is valid
        if os.path.exists(root):

            #hash the parent directory
            par_dir = str(pathlib.Path(root).parents[0])
            par_hash = hashlib.sha1(par_dir.encode()).hexdigest()

            #determine if root is a file or folder
            if os.path.isfile(root):
                par_hash = F"0-{par_hash}"
            else:
                par_hash = F"1-{par_hash}"

            self.root_parents[par_hash.split('-')[1]] = par_dir
            new_root = \
                F"{par_hash}{constants.GENERIC_PATH}{os.path.basename(root)}"
            if new_root not in self.roots:
                self.roots.append(new_root)
        else:
            raise FileNotFoundError

    def remove_root(self, root_name):

        parent_hash = []
        pos = 0
        for i in self.roots:
            if os.path.basename(i) == root_name:
                del self.roots[pos]
                parent_hash = i.split('/')[0]
                break
            pos += 1

        cnt = 0
        for i in self.roots:
            if i.split('/')[0] == parent_hash:
                cnt += 1

        if not cnt:
            del self.root_parents[parent_hash.split('-')[1]]


    # Periodically closes any connections that have been marked for closing
    def close_finished_connections(self):
        while self.close_run:
            try:
                # run through marked connections
                for c in self.closed_connections:

                    # stop the thread
                    self.connections[c].join()

                    del self.connections[c]

                # reset the closed_connections list
                self.closed_connections.clear()
            except:
                pass
            time.sleep(0.5)

    # listen for client requests and respond with an appropriate activity
    # to deal with the client's needs
    def deal_with_client(self, client, address):
        net_activity = NetworkActivity()
        while True:
            try:

                # listen in non-blocking mode
                readable, writable, errored = select.select([client], [], [])
                for s in readable:
                    data = s.recv(102400)
                    if data:
                        try:
                            data = data.decode()[0]

                            # get appropriate activity
                            function = net_activity.activity_function_factory( \
                                int(data)                                      \
                            )

                            # inform client request has been acknowledged
                            s.send("{0}".format(            \
                                net_activity.DATA_RECEIVED  \
                            ).encode())

                            # the activity will take over from here
                            function(s, get_list_from_json(s.recv(102400)))

                        # TODO: If clients arguments are invalid, inform the client
                        except json.decoder.JSONDecodeError:
                            raise Exception()
                            self.closed_connections.append(address)

                        # TODO: Make this better
                        except Exception as e:
                            print(traceback.print_exc())
                            s.send(b"Error in data transfer")

                    else:
                        raise Exception()

            # this is called when a client drops a connecton. The connection is marked for closing
            except Exception as e:
                self.closed_connections.append(address)
                break
