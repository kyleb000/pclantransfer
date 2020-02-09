import json
import os
import io
import hashlib
import threading
import time
import constants
from utils.str_functions import get_abs_path, hash_file, get_generic_path, \
    get_real_path

semaphore = threading.Semaphore()

#the structure is as follows: [file object, open_counter, semaphore]
#the semaphore ensures that only one thread can use the file at a time.
opened_files = {}

roots = []
root_parents = {}
server_name = ["None"]


class NetworkActivity:

    #constants for identifying what a client wants to do
    FILE_INFO = 0
    ROOT_SUBDIR = 1
    ROOT_SUBDIR_RECURSIVE = 2
    FILE_DATA = 3
    TRANSFER_OK = 4
    DATA_RECEIVED = 5
    TRANSFER_FAILED = 6
    ROOTS = 7
    SERVER_NAME = 8

    #extracts information from a file and sends it to the client
    def get_file_info(self, client, arguments):

        file_path = get_abs_path(get_real_path(arguments['file']), root_parents)
        name = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        hash = hash_file(file_path)
        client.send(json.dumps({                    \
                                    "name": name,   \
                                    "size": size,   \
                                    "hash": hash    \
                                }).encode())

    #sends the contents of a folder's subdirectory to the client
    def get_root_subdir(self, client, arguments):
        client.send('/::/'.join(os.listdir(arguments['file'])).encode())

    #traverses the entire directory tree for a given directory and adds the path
    #to a list and sends the list to the client
    def get_root_subdir_rec(self, client, arguments):
        paths = []

        # convert the relative path into an absolute path
        raw_path = get_abs_path(arguments['file'], root_parents)

        for path,dirs,files in os.walk(raw_path):
            for filename in files:
                base_dir = path
                for i in raw_path:
                	if base_dir[0] == i:
                		base_dir = base_dir.replace(base_dir[0], '', 1)
                	else:
                		break
                base_dir = F"{arguments['file']}{base_dir}"
                paths.append(get_generic_path(os.path.join(base_dir,filename)))

        paths = '/::/'.join(paths)

        #makes it easier to send the paths in chunks over the network
        stio = io.StringIO(paths)

        while True:
            data = stio.read(65536)
            if not data:
                break
            client.send(data.encode())

        client.close()
        stio.close()

    #reads data from a file and sends it to the client
    def get_file_data(self, client, arguments):
        file_path = get_abs_path(get_real_path(arguments['file']), root_parents)
        with FileManager(file_path) as file_man:
            for data in file_man:
                client.send(data)
        client.close()

    #sends all roots of the server to the client
    def get_roots(self, client, arguments):
        if not len(roots):
            client.send(b"No roots")
        client.send("/::/".join(roots).encode())

    def get_server_name(self, client, arguments):
        client.send(server_name[0].encode())

    #determine what the client wants to do and return the appropriate function
    #to complete the task
    def activity_function_factory(self, activity):
        if activity == self.ROOTS:
            return self.get_roots
        if activity == self.SERVER_NAME:
            return self.get_server_name
        if activity == self.FILE_INFO:
            return self.get_file_info
        if activity == self.ROOT_SUBDIR:
            return self.get_root_subdir
        if activity == self.ROOT_SUBDIR_RECURSIVE:
            return self.get_root_subdir_rec
        if activity == self.FILE_DATA:
            return self.get_file_data
        if activity == self.TRANSFER_FAILED:
            return handle_failure
        raise ValueError("Key not recognised")
