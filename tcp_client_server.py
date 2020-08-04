#TCP Group project
#Submitted by John Adedigba and Gnana Soundari Arockiaraj
#As part of WS2018 Internet protocols
"""
TCP Client Server Application
"""
import sys
import os
import signal
from tkinter import Tk, Label, Button, Entry, filedialog, Frame
from tkinter import BOTH, RIGHT, LEFT, END, DISABLED, NORMAL, E, W, S, N
from tkinter.messagebox import showerror, showinfo, showwarning, askquestion
from tkinter.scrolledtext import ScrolledText

from time import sleep
from os import listdir
from datetime import datetime
import platform

import threading

import select
import socket
import json

SERVER_MODE = 0
CLIENT_MODE = 1

MODE_STR = ["Server", "Client"]

class Status:
    """
    Enum class for Client / Server connection status
    """
    DISCONNECTED = 0
    SERVER_READY = 1
    CLIENT_CONNECTED = 2

    def __init__(self):
        pass

class TCPClientServer():
    """
    Main entry class asking for Server or Client mode
    """
    MIN_WIDTH = 400
    MIN_HEIGHT = 100

    dir_name = ''
    top = None

    def __init__(self):
        pass

    def _create_window(self):
        top = self.top

        top.title("TCP Client Server")

        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = int((top.winfo_screenwidth() // 2) - (width // 2))
        y = int(((top.winfo_screenheight() // 2) - (height // 2))    / 2)

        top.geometry('{}x{}+{}+{}'.format(self.MIN_WIDTH, self.MIN_HEIGHT, x, y))
        top.resizable(False, False)

    def _create_icons(self):
        top = self.top

    def server_mode(self):
        self.app = MainWindow(SERVER_MODE).start(self.top)

    def client_mode(self):
        self.app = MainWindow(CLIENT_MODE).start(self.top)

    def start(self):
        # Instantiate GUI
        self.top = Tk()
        top = self.top
        top.withdraw()

        top.attributes('-topmost', True)


        # Create main display window
        self._create_window()

        f = Frame(top)
        f.pack_propagate(0) # don't shrink
        f.pack(padx=10, pady=10, fill="both", expand=True)

        Label(f, text="Choose the application type!").pack()
        Button(f, text='Server', command=self.server_mode, padx=50) \
                .pack(side=LEFT, padx=20, pady=5)
        Button(f, text='Client', command=self.client_mode, padx=50) \
                .pack(side=RIGHT, padx=20, pady=5)


        # Create ICONS
        self._create_icons()

        # Start the window before all windows

        top.update()
        top.deiconify()
        top.after_idle(top.attributes, '-topmost', False)
        # Runs in a loop
        top.mainloop()


class ClientWindow(Frame):
    """
    Client mode class
    """
    server = None

    BUFFER_SIZE = 1024 + 128    # Normally 1024, but we want fast response

    status = Status.DISCONNECTED
    abort = False
    def __init__(self, mode):
        Frame.__init__(self)
        self.mode = CLIENT_MODE
        self.initUI()

    def updateStatus(self, status):
        self.status = status

        if self.status == Status.DISCONNECTED:
            self.connbtn.config(text="Connect")
            self.area.config(state=DISABLED)
            self.port.config(state=NORMAL)
            self.ip.config(state=NORMAL)

        elif self.status == Status.CLIENT_CONNECTED:
            self.connbtn.config(text="Disconnect")
            self.area.config(state=NORMAL)
            self.port.config(state=DISABLED)
            self.ip.config(state=DISABLED)


    def startClient(self):
        port = self.port.get()
        tcp_ip = self.ip.get()
        if port == "" or tcp_ip == "":
            showerror("Error", "Enter a valid IP/Port")
            return

        TCP_PORT = int(port)
        TCP_IP = str(tcp_ip)

        print("Connect to {}:{}".format(TCP_IP, TCP_PORT))
        keepopen = True

        # Create a socket for the server to listen to
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((TCP_IP, TCP_PORT))
        except:
            showerror("Connection Error",
                      "Unable to connect to the server. "
                      "Please check if the server is up")
            return
        self.updateStatus(Status.CLIENT_CONNECTED)
        self.abort = False

        while True:
            data = None
            try:
                data = self.sock.recv(self.BUFFER_SIZE)
            except Exception as e:
                print(str(e))
                # Socket probably aborted by local disconnect
                # Set keepopen to false to start a new sock connection
                pass


            if not data:
                if not self.abort:
                    showerror("Error", "Server Disconnected")
                break

            # Data is received as a JSON in the form
            #     {
            #         'ACTION' : <ACTION>,
            #         'DATA'     " <TEXT>
            #     }
            # This is to accomodate future work if client
            # wants to send a special command like CLOSE, SEND ME SOMETHING, etc
            # to the server
            # For now we will be using only the 'DATA' as text
            jdata = json.loads(data)

            if jdata.get("data"):
                self.area.config(state=NORMAL)
                self.area.delete(1.0, END)
                self.area.insert(END, jdata.get("data"))
        self.sock.close()

        self.updateStatus(Status.DISCONNECTED)

    def startClientThread(self):
        # Start the thread if not already started
        if self.status == Status.DISCONNECTED:
            t = threading.Thread(target=self.startClient)
            t.daemon = True
            t.start()

        else:
            self.abort = True
            # Attempt to shutdown the server if open
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print("Exception1: " + str(e))

            # Attempt to close the server if open
            try:
                self.sock.close()
            except Exception as e:
                print("Exception2: " + str(e))

    def sendText(self):
        print("Sending text")
        msg = self.area.get(1.0, END)
        msg = msg.strip()
        if len(msg) > 1000:
            showwarning("Message Truncated", "Sending only the first 1000 characters")
            msg = msg[:1000]

        self.sock.send(json.dumps({"action" : "TEXT", "data" : msg}).encode())
        showinfo("Sending", "Sent {} characters to TCP server".format(len(msg)))

    def saveText(self):
        fp = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
        if fp:
            fname = fp.name
            txt = str(self.area.get(1.0, END)).strip()
            fp.write(txt)
            fp.close()
            showinfo("Saved", "Saved {} characters to {}".format(len(txt), fname))

    def exit(self):
        result = askquestion("Exit", "Are You Sure?", icon='warning')
        if result == 'yes':
            exit()

    def initUI(self):

        self.master.title("TCP " + MODE_STR[self.mode])
        self.pack(fill=BOTH, expand=True)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(5, pad=10)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        iplbl = Label(self, text="Server IP: ")
        iplbl.grid(row=0, column=0, pady=4)
        self.ip = Entry(self, width=15)
        self.ip.insert(END, socket.gethostname())
        self.ip.grid(row=0, column=1, pady=4)

        portlbl = Label(self, text="Port: ")
        portlbl.grid(row=0, column=2, pady=4)
        self.port = Entry(self, width=5)
        self.port.insert(END, "5001")
        self.port.grid(row=0, column=3, pady=4)

        self.connbtn = Button(self, text="Connect", command=self.startClientThread)
        self.connbtn.grid(row=0, column=5, pady=4)

        self.area = ScrolledText(self)
        self.area.config(highlightbackground="GREEN")
        self.area.grid(row=1, column=0, columnspan=6, rowspan=4,
                       padx=5, sticky=E+W+S+N)

        hbtn = Button(self, text="Exit", command=self.exit)
        hbtn.grid(row=5, column=0, padx=5)

        savebtn = Button(self, text="Save", command=self.saveText)
        savebtn.grid(row=5, column=4)

        sendbtn = Button(self, text="Send", command=self.sendText)
        sendbtn.grid(row=5, column=5)


class ServerWindow(Frame):
    """
    Server mode class
    """
    client = None

    TCP_IP = '127.0.0.1'
    # TCP_IP = '10.239.80.39'
    BUFFER_SIZE = 1024 + 128    # Normally 1024, but we want fast response

    status = Status.DISCONNECTED
    abort = False

    def __init__(self, mode):
        Frame.__init__(self)
        self.mode = SERVER_MODE
        self.initUI()

    def updateStatus(self, status):
        self.status = status

        if self.status == Status.DISCONNECTED:
            self.connbtn.config(text="Connect")
            self.sendbtn.config(state=DISABLED)
            self.st2lbl.config(text="-")
            self.port.config(state=NORMAL)
            self.area.config(state=DISABLED)

        elif self.status == Status.SERVER_READY:
            self.connbtn.config(text="Disconnect")
            self.sendbtn.config(state=DISABLED)
            self.st2lbl.config(text="Ready")
            self.port.config(state=DISABLED)
            self.area.config(state=DISABLED)

        elif self.status == Status.CLIENT_CONNECTED:
            self.connbtn.config(text="Disconnect")
            self.sendbtn.config(state=NORMAL)
            self.st2lbl.config(text="Active")
            self.port.config(state=DISABLED)
            self.area.config(state=NORMAL)

    def startServer(self):
        tcp_ip = self.ip.get()
        port = self.port.get()
        if port == "" or tcp_ip == "":
            showerror("Error", "Enter a valid IP/Port")
            return

        TCP_PORT = int(port)
        TCP_IP = str(tcp_ip)
        keepopen = True

        # Create a socket for the server to listen to
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock .setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((TCP_IP, TCP_PORT))
        self.sock.listen(1)
        self.abort = False

        while keepopen:
            self.updateStatus(Status.SERVER_READY)

            client, addr = None, None
            read_list = [self.sock]
            while not client:
                try:
                    readable, writable, errored = select.select(read_list, [], [])
                    for r in readable:
                        if self.sock is r:
                            client, addr = self.sock.accept()
                            print('Connection address:' + str(addr))
                            break
                except Exception as e:
                    print(str(e))
                    self.updateStatus(Status.DISCONNECTED)
                    return

            self.client = client
            self.updateStatus(Status.CLIENT_CONNECTED)


            while True:
                try:
                    data = self.client.recv(self.BUFFER_SIZE)
                except Exception as e:
                    # Socket probably aborted by local disconnect
                    # Set keepopen to false to start a new sock connection
                    print(str(e))
                    keepopen = False
                    break

                if self.abort:
                    # Socket probably aborted by local disconnect
                    # Set keepopen to false to start a new sock connection
                    keepopen = False
                    break

                if not data:
                    showerror("Error", "Client Disconnected")
                    break

                # Data is received as a JSON in the form
                #     {
                #         'ACTION' : <ACTION>,
                #         'DATA'     " <TEXT>
                #     }
                # This is to accomodate future work if client
                # wants to send a special command like CLOSE, SEND ME SOMETHING, etc
                # to the server
                # For now we will be using only the 'DATA' as text
                jdata = json.loads(data)

                if jdata.get("data"):
                    self.area.config(state=NORMAL)
                    self.area.delete(1.0, END)
                    self.area.insert(END, jdata.get("data"))

            try:
                self.client.close()
            except:
                pass

        self.updateStatus(Status.DISCONNECTED)

    def startServerThread(self):
        # Start the thread if not already started
        if self.status == Status.DISCONNECTED:
            t = threading.Thread(target=self.startServer)
            t.daemon = True
            t.start()

        else:
            # Attempt to shutdown the server if open
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print("Exception1: " + str(e))

            # Attempt to close the server if open
            try:
                self.sock.close()
            except Exception as e:
                print("Exception2: " + str(e))

            # Attempt to disconnect the client connection if open
            try:
                if self.client:
                    self.abort = True
                    self.client.shutdown(socket.SHUT_RDWR)
                    self.client.close()
                    self.client = None
            except Exception as e:
                print("Exception3: " + str(e))

    def sendText(self):
        print("Sending text")
        msg = self.area.get(1.0, END)
        msg = msg.strip()
        if len(msg) > 1000:
            showwarning("Message Truncated", "Sending only the first 1000 characters")
            msg = msg[:1000]

        self.client.send(json.dumps({"action" : "TEXT", "data" : msg}).encode())
        showinfo("Sending", "Sent {} characters to TCP client".format(len(msg)))

    def saveText(self):
        fp = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
        if fp:
            fname = fp.name
            txt = str(self.area.get(1.0, END)).strip()
            fp.write(txt)
            fp.close()
            showinfo("Saved", "Saved {} characters to {}".format(len(txt), fname))

    def exit(self):
        result = askquestion("Exit", "Are You Sure?", icon='warning')
        if result == 'yes':
            exit()

    def initUI(self):

        self.master.title("TCP " + MODE_STR[self.mode])
        self.pack(fill=BOTH, expand=True)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(5, pad=10)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        iplbl = Label(self, text="IP: ")
        iplbl.grid(row=0, column=0, pady=4)
        self.ip = Entry(self, width=15)
        self.ip.insert(END, socket.gethostname())
        self.ip.grid(row=0, column=1, pady=4)

        portlbl = Label(self, text="Port: ")
        portlbl.grid(row=0, column=2, pady=4)
        self.port = Entry(self, width=5)
        self.port.insert(END, "5001")
        self.port.grid(row=0, column=3, pady=4)

        self.st2lbl = Label(self, text="-")
        self.st2lbl.grid(row=0, column=4, pady=4)

        self.connbtn = Button(self, text="Connect", command=self.startServerThread)
        self.connbtn.grid(row=0, column=5, pady=4)

        self.area = ScrolledText(self)
        self.area.config(highlightbackground="GREEN", state=DISABLED)
        self.area.grid(row=1, column=0, columnspan=6, rowspan=4,
                       padx=5, sticky=E+W+S+N)

        hbtn = Button(self, text="Exit", command=self.exit)
        hbtn.grid(row=5, column=0, padx=5)

        savebtn = Button(self, text="Save", command=self.saveText)
        savebtn.grid(row=5, column=4)

        self.sendbtn = Button(self, text="Send", command=self.sendText)
        self.sendbtn.grid(row=5, column=5)


class MainWindow:
    """
    Helper class invoked when mode is chosen by the user
    """
    def __init__(self, mode):
        self.mode = mode

    def start(self, old):
        old.destroy()
        root = Tk()
        root.geometry("400x300+300+300")
        if self.mode == SERVER_MODE:
            app = ServerWindow(self.mode)
        else:
            app = ClientWindow(self.mode)
        root.resizable(False, False)
        root.mainloop()

t = TCPClientServer()
t.start()
