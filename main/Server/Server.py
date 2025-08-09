from flask import Flask, render_template_string, request
import socket
import threading
import time
import queue

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
    print(f"[SERVER] Client connected from {addr}")
    data = conn.recv(1024)
    if data == b'hello':
        print("[SERVER] Handshake received from client.")
        conn.sendall(b'hello_ack')
        client_conn = conn
        client_addr = addr
        client_ready.set()
        try:
            while True:
                try:
                    command = command_queue.get(timeout=1)
                    conn.sendall((command + '\n').encode('utf-8'))
                    print(f"[SERVER] Sent command to client: {command}")
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"[SERVER] Client handler error: {e}")
        finally:
            print(f"[SERVER] Client disconnected: {addr}")
            client_conn = None
            client_addr = None
            client_ready.clear()
            conn.close()
    else:
        print(f"[SERVER] Unexpected data from client: {data}")
        conn.close()

def client_socket_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", CLIENT_SOCKET_PORT))
    s.listen(1)
    print(f"[SERVER] Waiting for client connection on port {CLIENT_SOCKET_PORT}...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

# Send command to client
def send_command_to_client(command):
    if client_ready.is_set():
        command_queue.put(command)
    else:
        print("[SERVER] No client connected.")

@app.route('/', methods=['GET', 'POST'])
def index():
    sent = False
    if request.method == 'POST':
        message = request.form['message']
        print(f"[SERVER] Received request to send notification: '{message}'")
        send_command_to_client(f"notify:{message}")
        sent = True
    return render_template_string(HTML, sent=sent)

if __name__ == "__main__":
    threading.Thread(target=client_socket_server, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
