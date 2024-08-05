import eventlet
eventlet.monkey_patch()

import socket
import cv2
import pickle
import struct
import threading
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Configurações do servidor de vídeo
ip = '127.0.0.1'  # Endereço IP do servidor (local)
porta = 5000  # Porta do servidor

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ip, porta))
s.listen(5)
print(f"Servidor ouvindo em {ip}:{porta}")

new_socket, endereco = s.accept()
print(f"Conexão estabelecida com {endereco}")

webcam = cv2.VideoCapture(0)

def send_video():
    while True:
        ret, frame = webcam.read()
        if not ret:
            break
        data = pickle.dumps(frame)
        message_size = struct.pack("L", len(data))
        new_socket.sendall(message_size + data)
        if cv2.waitKey(1) == ord("f"):
            break

def receive_video():
    data = b""
    payload_size = struct.calcsize("L")
    while True:
        while len(data) < payload_size:
            packet = new_socket.recv(4096)
            if not packet:
                break
            data += packet
        if not data:
            break
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += new_socket.recv(4096)
        
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        socketio.emit('video_feed', {'image': frame})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    send_thread = threading.Thread(target=send_video)
    receive_thread = threading.Thread(target=receive_video)
    
    send_thread.start()
    receive_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=8000)
    
    send_thread.join()
    receive_thread.join()

    new_socket.close()
    webcam.release()
    cv2.destroyAllWindows()
