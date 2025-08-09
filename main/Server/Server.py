from flask import Flask, render_template_string, request
import socket
import threading
import time
import queue

LOG_DELAY = 0.5
log_queue = queue.Queue()

def logger_thread():
    while True:
        msg = log_queue.get()
        print(f"[SERVER][{time.strftime('%H:%M:%S')}] {msg}")
        time.sleep(LOG_DELAY)

def log(msg):
    log_queue.put(msg)

threading.Thread(target=logger_thread, daemon=True).start()

app = Flask(__name__)

CLIENT_IP = "127.0.0.1"  # Change to child's PC IP if needed
CLIENT_PORT = 8080  # Changed to match client
CLIENT_SOCKET_PORT = 6000  # Port for client connections

HTML = '''
<!DOCTYPE html>
<html>
<head><title>ControlCast Parent Panel</title></head>
<body>
    <h2>Send Notification to Child's PC</h2>
    <form method="post">
        <input type="text" name="message" placeholder="Notification message" required>
        <button type="submit">Send</button>
    </form>
    {% if sent %}<p>Notification sent!</p>{% endif %}
</body>
</html>
'''

client_conn = None
client_addr = None
client_ready = threading.Event()
command_queue = queue.Queue()

# Socket server for client
def client_handler(conn, addr):
    global client_conn, client_addr
    log(f"[SOCKET] Client connected from address: {addr}")
    data = conn.recv(1024)
    log(f"[SOCKET] Received handshake data from client: {data}")
    if data == b'hello':
        log("[SOCKET] Handshake 'hello' received. Sending confirmation to client.")
        conn.sendall(b'hello_ack')
        client_conn = conn
        client_addr = addr
        client_ready.set()
        log("[SOCKET] Client marked as ready. Entering command loop.")
        try:
            empty_logged = False
            while True:
                try:
                    command = command_queue.get(timeout=1)
                    log(f"[COMMAND] Sending command to client: {command}")
                    conn.sendall((command + '\n').encode('utf-8'))
                except queue.Empty:
                    if not empty_logged:
                        log("[COMMAND] No command in queue. Waiting...")
                        empty_logged = True
                    continue
        except Exception as e:
            log(f"[ERROR] Client handler encountered an error: {e}")
        finally:
            log(f"[SOCKET] Client disconnected: {addr}. Cleaning up connection state.")
            client_conn = None
            client_addr = None
            client_ready.clear()
            conn.close()
    else:
        log(f"[SOCKET] Unexpected handshake data from client: {data}. Closing connection.")
        conn.close()

def client_socket_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", CLIENT_SOCKET_PORT))
    s.listen(1)
    log(f"[SOCKET] Server listening for client connections on port {CLIENT_SOCKET_PORT}.")
    while True:
        conn, addr = s.accept()
        log(f"[SOCKET] Accepted new connection from {addr}. Spawning handler thread.")
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

# Send command to client
def send_command_to_client(command):
    if client_ready.is_set():
        log(f"[COMMAND] Queueing command for client: {command}")
        command_queue.put(command)
    else:
        log("[COMMAND] No client connected. Cannot send command.")

@app.route('/', methods=['GET', 'POST'])
def index():
    sent = False
    if request.method == 'POST':
        message = request.form['message']
        log(f"[WEB] Received request to send notification: '{message}'")
        send_command_to_client(f"notify:{message}")
        sent = True
    return render_template_string(HTML, sent=sent)

if __name__ == "__main__":
    log("[SYSTEM] Server starting up.")
    threading.Thread(target=client_socket_server, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
