import threading

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
