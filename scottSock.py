#!/usr/bin/env python3


# +
# import(s)
# -
import socket
import sys
import select


# +
# class: scottSock()
# -
# noinspection PyPep8Naming
class scottSock(socket.socket):

    # +
    # method; __init__()
    # -
    def __init__(self, host, port, timeout=None):

        self.host = host
        self.port = int(port)
        self.timeout = int(timeout)

        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)

        host = socket.gethostbyname(host)
        self.connect((host, int(port)))

    # +
    # method: talk()
    # -
    def talk(self, message):
        self.send(message)

    # +
    # method: listen()
    # -
    def listen(self, endchar='\n'):
        test = True
        resp = b""
        timeout = 0.1
        while test:
            try:

                ready = select.select([self], [], [], timeout)
                if ready[0]:

                    new_stuff = self.recv(128)
                else:
                    new_stuff = ""
            except socket.timeout:
                return resp

            if new_stuff:
                resp += new_stuff
            else:
                return resp
            timeout = 0.01

    # +
    # method: converse()
    # -
    def converse(self, message, endchar='\n'):
        self.talk(message)
        return self.listen(endchar=endchar)


# +
# main()
# -
if __name__ == '__main__':
    if len(sys.argv) > 3:
        soc = scottSock(sys.argv[1], sys.argv[2])
        print(soc.talk(sys.argv[3]))
