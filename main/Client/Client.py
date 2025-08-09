import socket
import time
import tkinter as tk
from tkinter import messagebox
import threading
import queue

LOG_DELAY = 0.5
log_queue = queue.Queue()

def logger_thread():
    while True:
        msg = log_queue.get()
        print(f"[CLIENT][{time.strftime('%H:%M:%S')}] {msg}")
        time.sleep(LOG_DELAY)

def log(msg):
    log_queue.put(msg)

threading.Thread(target=logger_thread, daemon=True).start()

def show_notification(message):
    log("[NOTIFICATION] Preparing to show notification window.")
    log(f"[NOTIFICATION] Message: '{message}'")
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Make sure the window is on top
    messagebox.showinfo("ControlCast Notification", message, master=root)
    root.destroy()
    log("[NOTIFICATION] Notification window closed.")

SERVER_IP = "192.168.50.161"  # Change to your server's IP if needed
SERVER_PORT = 6000  # Must match CLIENT_SOCKET_PORT in Server.py

def connect_and_listen(server_ip, server_port):
    while True:
        try:
            log("[NETWORK] Starting connection attempt to server.")
            log(f"[NETWORK] Target server: {server_ip}:{server_port}")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            log("[NETWORK] Socket created.")
            s.connect((server_ip, server_port))
            log("[NETWORK] Socket connected to server.")
            s.sendall(b'hello')
            log("[NETWORK] Sent handshake 'hello' to server.")
            response = s.recv(1024)
            log(f"[NETWORK] Received handshake response: {response}")
            if response == b'hello_ack':
                log("[NETWORK] Handshake confirmed by server.")
                log("[NETWORK] Ready to receive commands.")
                buffer = b''
                while True:
                    data = s.recv(1024)
                    if not data:
                        log("[NETWORK] Server closed connection. Exiting inner loop.")
                        break
                    buffer += data
                    while b'\n' in buffer:
                        cmd, buffer = buffer.split(b'\n', 1)
                        command = cmd.decode('utf-8')
                        log(f"[COMMAND] Received command: {command}")
                        if command.startswith("notify:"):
                            message = command[len("notify:"):]
                            log(f"[COMMAND] Notification command detected. Message: '{message}'")
                            show_notification(message)
                        else:
                            log(f"[COMMAND] Unknown command received: {command}")
            else:
                log(f"[NETWORK] Handshake failed. Response: {response}")
            s.close()
            log("[NETWORK] Socket closed.")
        except Exception as e:
            log(f"[ERROR] Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    log("[SYSTEM] Client starting up.")
    connect_and_listen(SERVER_IP, SERVER_PORT)
