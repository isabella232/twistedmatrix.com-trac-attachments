
import os, socket

import gtk, gobject

def write(source, condition):
    os.write(source, 'x' * 65536)
    return 1


def read(source, condition):
    os.read(source, 65536)
    return 1


def main():
    port = socket.socket()
    port.listen(1)
    client = socket.socket()
    client.setblocking(False)
    client.connect_ex(port.getsockname())
    server, addr = port.accept()
    server.setblocking(False)

    gobject.io_add_watch(client.fileno(), gobject.IO_OUT, write)
    gobject.io_add_watch(server.fileno(), gobject.IO_IN, read)

    win = gtk.Window()
    win.set_size_request(300, 300)
    lab = gtk.Label("Hello")
    win.add(lab)
    win.show_all()

    gtk.main()


if __name__ == '__main__':
    main()
