import socket
import sys
import time
import tkinter as tk
from tkinter import messagebox

def show_notification(message):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showinfo("ControlCast Notification", message)
    root.destroy()

SERVER_IP = "192.168.50.161"  # Change to your server's IP if needed
SERVER_PORT = 6000  # Must match CLIENT_SOCKET_PORT in Server.py

def connect_and_listen(server_ip, server_port):
    while True:
        try:
            print(f"[CLIENT] Attempting to connect to server at {server_ip}:{server_port}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server_ip, server_port))
            print(f"[CLIENT] Connected to server at {server_ip}:{server_port}")
            s.sendall(b'hello')
            response = s.recv(1024)
            if response == b'hello_ack':
                print(f"[CLIENT] Handshake confirmed by server.")
                buffer = b''
                while True:
                    data = s.recv(1024)
                    if not data:
                        print("[CLIENT] Server closed connection.")
                        break
                    buffer += data
                    # Split commands by newline (server should send with .encode('utf-8') + b'\n')
                    while b'\n' in buffer:
                        cmd, buffer = buffer.split(b'\n', 1)
                        command = cmd.decode('utf-8')
                        print(f"[CLIENT] Received command: {command}")
                        if command.startswith("notify:"):
                            message = command[len("notify:"):]
                            print(f"[CLIENT] Displaying notification: '{message}'")
                            show_notification(message)
                            print(f"[CLIENT] Notification window should now be visible.")
                        else:
                            print(f"[CLIENT] Unknown command received: {command}")
            else:
                print(f"[CLIENT] Handshake failed. Response: {response}")
            s.close()
        except Exception as e:
            print(f"[CLIENT] Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    connect_and_listen(SERVER_IP, SERVER_PORT)
