from xml.etree.ElementTree import Element, SubElement, Comment, \
    tostring, ParseError
from xml.etree import ElementTree
from xml.dom import minidom
import io
import os
import pathlib
from sys import platform
from copy import copy
import threading

log_semaphore = threading.Semaphore()
log_instances = {}


class LogHandler:
    log_instance = None
    target_attr = None

    LOG_FILEPROGRESS = 1
    LOG_CLIENTCONNECTION = 2
    LOG_FILELIST = 3
    LOG_SERVER = 4

    LOG_NAMES = ("fileprogress", "clientconnection", "filelist", "server")

    def __init__(self, log_type=None):
        if log_type:
            try:
                self.log_instance = log_instances[self.LOG_NAMES[log_type-1]]
            except KeyError:
                if log_type == self.LOG_FILEPROGRESS:
                    log_instances[self.LOG_NAMES[log_type-1]] = FileProgressLogger()
                elif log_type == self.LOG_CLIENTCONNECTION:
                    log_instances[self.LOG_NAMES[log_type-1]] = \
                        ClientConnectionLogger()
                elif log_type == self.LOG_SERVER:
                    log_instances[self.LOG_NAMES[log_type-1]] = ServerLogger()
                else:
                    log_instances[self.LOG_NAMES[log_type-1]] = FileListLogger()
                self.log_instance = log_instances[self.LOG_NAMES[log_type-1]]
        else:
            raise Exception("no log type specifiend")

    def write_to_log(self, *args, **kwargs):
        log_semaphore.acquire()

        try:
            self.log_instance.write_log(*args, **kwargs)
        except:
            log_semaphore.release()
            raise
        log_semaphore.release()

    def clean_log(self, *args, **kwargs):
        log_semaphore.acquire()
        kwargs['client_hash'] = self.target_attr

        try:
            self.log_instance.clean_log(*args, **kwargs)
        except:
            log_semaphore.release()
            raise
        log_semaphore.release()

    def set_target_attr(self, attr):
        self.target_attr = attr


def get_log_path():

    # for Windows
    if platform.startswith('win'):
        return os.getenv('LOCALAPPDATA')

    # Unix-based OSes
    else:
        return str(pathlib.Path.home())

class ClientAlreadyExists(Exception):
    pass

class ServerNameSet(Exception):
    pass

class Logger:
    LOG_DIR = ".pclt_logs"

    log_path = ""
    log_name = ""
    xml_root =""

    #helpers

    def make_pretty(self,raw_xml):
        rough_string = ElementTree.tostring(raw_xml, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")

    def clean_output(self,out):
        clean_out = io.StringIO()
        for line in out.splitlines():
            test_str = line.strip()
            if len(test_str) > 0:
                clean_out.write("{0}\n".format(line))
        return clean_out.getvalue()

    def get_xml(self,xml_data):
        pretty_data = self.make_pretty(xml_data)
        return self.clean_output(pretty_data)

    def find_element_data(self, document, element_name, data):
        for node in document.iter(element_name):
            if node.text == data:
                return True
        return False

    def get_file_entry(self,document, file_name, element_name, element_pos):
        for node in document.iter(element_name):
            if node[element_pos].text == file_name:
                return node

    # class specific code

    def __init__(self, log_name=""):
        self.log_path = get_log_path()
        self.log_name = log_name
        if not os.path.exists(self.path_builder()):
            try:
                os.makedirs(self.path_builder(True))
            except FileExistsError:
                pass
        try:
            self.xml_root = ElementTree.parse(self.path_builder()).getroot()
        except FileNotFoundError:
            self.xml_root = Element("files")
        except ParseError:
            self.xml_root = Element("files")

    def path_builder(self, dir_only=False):
        log_file = os.path.join(self.log_path, self.LOG_DIR)
        if not dir_only:
            log_file = os.path.join(log_file, self.log_name)
        return log_file

    def write_log(self, *args, **kwargs):
        raise Exception("Implement in child class")

    def clean_log(self, *args, **kwargs):
        raise Exception("Implement in child class")


class FileProgressLogger(Logger):
    def __init__(self, log_name="file_progress_log.xml"):
        super().__init__(log_name)

    def write_log(self, *args, **kwargs):
        if not self.find_element_data(                  \
            self.xml_root, 'name', kwargs['file_name']  \
        ):

            new_entry = SubElement(self.xml_root, "file_entry")
            new_entry.set('conn', kwargs['client_conn'])

            new_entry_name = SubElement(new_entry, "name")
            new_entry_name.text = kwargs['file_name']

            new_entry_size = SubElement(new_entry, "size")
            new_entry_size.text = str(kwargs['file_size'])

            new_entry_hash = SubElement(new_entry, "hash")
            new_entry_hash.text = kwargs['file_hash']

            new_entry_tfer = SubElement(new_entry, "tfer")
            new_entry_tfer.text = str(kwargs['transferred'])

            new_entry_orig = SubElement(new_entry, "orig")
            new_entry_orig.text = kwargs['orig_path']

            new_entry_dest = SubElement(new_entry, "dest")
            new_entry_dest.text = kwargs['dest_path']

        else:
            file_node = self.get_file_entry(self.xml_root, kwargs['file_name'], "file_entry", 0)
            file_node[3].text = str(kwargs['transferred'])

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def clean_log(self, *args, **kwargs):
        for node in self.xml_root.iter("file_entry"):
            if node[3].text == node[1].text:
                self.xml_root.remove(node)

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def get_outstanding_files(self, hasher):
        file_info = []
        for node in self.xml_root.iter("file_entry"):
            if node.get('conn') == hasher:
                for i in range(0, 6):
                    file_info.append(node[i].text)
        return file_info


# TODO: Associate logs with a specific IP
class ClientConnectionLogger(Logger):
    def __init__(self, log_name="clients.xml"):
        super().__init__(log_name)

    def clean_log_decorator(func):
        def inner(context, *args, **kwargs):
            file_node = self.get_file_entry(            \
                context.xml_root, kwargs['client_addr'] \
            )
            file_node[3].text = "False"
            func()
        return inner

    def write_log(self, *args, **kwargs):
        if not self.find_element_data(                              \
            self.xml_root, 'client_address', kwargs['client_addr']  \
        ):
            new_entry = SubElement(self.xml_root, "client")

            new_entry_name = SubElement(new_entry, "client_address")
            new_entry_name.text = kwargs['client_addr']

            new_entry_name = SubElement(new_entry, "client_port")
            new_entry_name.text = str(kwargs['client_port'])

            new_entry_name = SubElement(new_entry, "client_hash")
            new_entry_name.text = kwargs['client_hash']

            new_entry_name = SubElement(new_entry, "opened_conn")
            new_entry_name.text = "True"
        else:
            client_node = self.get_file_entry(self.xml_root, kwargs['client_addr'], "client", 0)
            client_node[0].text = str(kwargs['client_addr'])
            client_node[1].text = str(kwargs['client_port'])

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    @clean_log_decorator
    def clean_log(self):
        for node in self.xml_root.iter("client"):
            if node[3].text == "False":
                self.xml_root.remove(node)

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def get_clients(self):
        clients = []
        try:
            for node in self.xml_root.iter("client"):
                client_entry = (                                    \
                    copy(node[0].text), int(copy(node[1].text)),    \
                    copy(node[2].text)                              \
                )
                clients.append(client_entry)
        except:
            pass

        return clients

class FileListLogger(Logger):
    def __init__(self, log_name="file_list.xml"):
        super().__init__(log_name)

    def write_log(self, *args, **kwargs):
        new_entry = SubElement(self.xml_root, "file_list")

        new_entry.set('conn', kwargs['client_conn'])
        new_entry.set('dest', kwargs['dest_dir'])

        for file in kwargs['file_list']:
            new_entry_name = SubElement(new_entry, "file")
            new_entry_name.text = file

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def clean_log(self, *args, **kwargs):
        try:
            root_node = None
            for root in self.xml_root.iter("file_list"):
                if root.get('conn') == kwargs['client_hash']:
                    root_node = root
                    break
            node = next(root_node.iter("file"))
            self.xml_root.remove(node)
        except:
            pass

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def get_file_list(self, context):
        file_list = []
        root_node = None

        for root in self.xml_root.iter("file_list"):
            if root.get('conn') == context:
                root_node = root
                break

        if root_node:
            for file in root_node.iter("file"):
                file_list.append(file.text)

            dest_dir = root_node.get('dest')

            return file_list, dest_dir
        else:
            return None

class ServerLogger(Logger):
    def __init__(self, log_name="server.xml"):
        super().__init__(log_name)

    def write_log(self, *args, **kwargs):
        if not self.find_element_data(self.xml_root, 'set', 'set'):
            new_entry = SubElement(self.xml_root, "server")
            server_set = SubElement(new_entry, "set")
            server_set.text = "set"
            server_hash = SubElement(new_entry, "hash")
            server_hash.text = kwargs['hash']
        elif kwargs['override']:
            client_node = self.get_file_entry(self.xml_root, kwargs['hash'], "server", 0)
            client_node[0].text = str(kwargs['hash'])
        else:
            raise ServerNameSet()

        with open(self.path_builder(), "w") as xml_file:
            xml_file.write(self.get_xml(self.xml_root))

    def get_hash(self):
        for root in self.xml_root.iter("server"):
            return root[1].text


class UserLogger:
    pass
