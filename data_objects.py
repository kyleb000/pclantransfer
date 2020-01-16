
# we can close all connections here
class BackendObjects:
    def __init__(self, client, server):
        self.client = client
        self.server = server

    def client():
        doc = "The client property."
        def fget(self):
            return self._client
        def fset(self, value):
            self._client = value
        def fdel(self):
            del self._client
        return locals()
    client = property(**client())

    def server():
        doc = "The server property."
        def fget(self):
            return self._server
        def fset(self, value):
            self._server = value
        def fdel(self):
            del self._server
        return locals()
    server = property(**server())
