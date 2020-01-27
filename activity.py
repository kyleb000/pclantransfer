import json
import os
import io
import hashlib
import threading
import time
import constants

semaphore = threading.Semaphore()

#the structure is as follows: [file object, open_counter, semaphore]
#the semaphore ensures that only one thread can use the file at a time.
opened_files = {}

roots = []
root_parents = {}
server_name = ["None"]

#decodes and returns a dictionary from a given bytes string
def get_list_from_json(raw_data):
    data = raw_data.decode()
    return json.loads(data)

#creates a hashsum from a file
def hash_file(file_name):
    hasher = hashlib.sha512()

    # my pride and joy 😍😍
    with FileManager(file_name) as file_man:
        for data in file_man:
            hasher.update(data)
    return hasher.hexdigest()

def get_abs_path(hashed_path):
    # convert the relative path into an absolute path
    raw_path = hashed_path
    hash = raw_path.split('/')[0]

    base_dir = raw_path

    # remove the hash from the path
    for i in hash:
        if base_dir[0] == i:
            base_dir = base_dir.replace(base_dir[0], '', 1)
        else:
            break

    #combine the path without the hash  to the original path
    return F"{root_parents[hash]}{base_dir}"

def get_generic_path(gen_path):
    gen_path = gen_path.replace(constants.GENERIC_PATH, constants.GENERIC_SANITISE)
    gen_path = gen_path.replace(os.path.sep, constants.GENERIC_PATH)
    return gen_path

def get_real_path(gen_path):
    gen_path = gen_path.split(constants.GENERIC_SANITISE)

    fixed_path = []
    for p in gen_path:
    	fixed_path.append(p.replace(constants.GENERIC_PATH, os.path.sep))

    full_path = constants.GENERIC_PATH.join(fixed_path)
    return full_path

#opens and closes files as well as allowing for iteration and
#data management using python's 'with' statement, hiding the complexity of
#opening and closing files from the users of the class
class FileManager:

    file_name = ""
    pos = 0
    bufsize = 1000000

    def __init__(self, file_name="", pos=0, bufsize=1000000):
        self.file_name = file_name
        self.pos = pos
        self.bufsize = bufsize

    #create a new attribute 'opened' to flag a new instance opening a file
    def __enter__(self):
        setattr(self, "opened", False)
        return self

    #reads a specifiend amount of data from a file from a given position.
    #Creates a new file object if it does not exist and increments its counter for
    #every new request
    def read_file(self):

        #create a new file object
        if self.file_name not in opened_files:
            opened_files[self.file_name] = [                            \
                open(self.file_name, 'rb'), 1, threading.Semaphore()    \
            ]
            opened_files[self.file_name][2].acquire()

        else:
            opened_files[self.file_name][2].acquire()

            #check if the attribute opened is false.
            if not self.opened:
                opened_files[self.file_name][1] += 1

        self.opened = True

        #get the file and read a bufsize chunk of data from a given position
        file = opened_files[self.file_name][0]
        file.seek(self.pos)
        data = file.read(self.bufsize)

        opened_files[self.file_name][2].release()
        self.pos += self.bufsize
        return data

    def __iter__(self):
        return self

    def __next__(self):
        data = self.read_file()
        if not data:
            raise StopIteration
        else:
            return data

    #decreases the file's open counter and closes the file if the counter reaches 0
    def __exit__(self, exc_type, exc_value, traceback):

        #decrement the file counter. It is not closed immediately as other
        #objects could be using that file
        opened_files[self.file_name][2].acquire()
        opened_files[self.file_name][1] -= 1

        #delete a file reference when it's no longer in use
        if opened_files[self.file_name][1] == 0:
            opened_files[self.file_name][0].close()
            opened_files[self.file_name][2].release()
            del opened_files[self.file_name]

        else:
            opened_files[self.file_name][2].release()


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

        file_path = get_abs_path(get_real_path(arguments['file']))
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
        raw_path = get_abs_path(arguments['file'])

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
        file_path = get_abs_path(get_real_path(arguments['file']))
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
