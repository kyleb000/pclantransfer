import sys
from PyQt5.QtWidgets import QApplication
import threading
from gui.main_app import App
import server
import client
import loghandler
from data_objects import BackendObjects

if __name__ == "__main__":
    s = server.FileServer()
    c = client.ClientManager()
    backend = BackendObjects(c, s)
    app = QApplication(sys.argv)
    ex = App(backend)
    sys.exit(app.exec_())

    while True:
        print("Server or Client?")
        type = input()
        if type == "Client":
            print("Command:")
            command = input()
            if command == "getfileinfo":
                print("File name?")
                filename = input()
                print(c.get_file_info(filename))
            elif command == "getroots":
                print(c.get_roots())
            elif command == "getrootsubdir":
                print("Root?")
                root = input()
                print(c.get_directory_contents(root))
            elif command == "connect":
                print("IP Address?")
                ip = input()
                try:
                    c.connect_to_server(ip)
                except loghandler.ClientAlreadyExists:
                    print("Connection was already established. Reconnect?")
                    connect = input()
                    if connect == 'Y' or connect == 'y':
                        c.reestablish_connections()
            elif command == "transferdata":
                print("Origin Path?")
                orig_path = input()
                print("Destination Path?")
                dest_path = input()
                c.transfer_data(orig_path, dest_path)
        elif type == "Server":
            print("Command:")
            command = input()
            if command == "addroot":
                print("Full path:")
                path = input()
                s.add_root(path)
