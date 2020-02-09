import hashlib
import json
from file_manager import FileManager
import constants
import os

def str_diff(str_a, str_b):

    pos = 0
    for i in range(0, len(min(str_a, str_b))):
        if str_a[i] == str_b[i]:
            pos +=1

    return max(str_a, str_b)[pos:]

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

def get_abs_path(hashed_path, roots):
    # convert the relative path into an absolute path
    raw_path = hashed_path
    print(raw_path)
    hash = raw_path.split(constants.GENERIC_PATH)[0]

    base_dir = raw_path

    # remove the hash from the path
    for i in hash:
        if base_dir[0] == i:
            base_dir = base_dir.replace(base_dir[0], '', 1)
        else:
            break

    #combine the path without the hash  to the original path
    return F"{roots[hash]}{base_dir}"

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
