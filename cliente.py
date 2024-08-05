import socket
import cv2
import pickle
import struct
import threading

def send_video(connection, webcam):
    while True:
        ret, frame = webcam.read()
        if not ret:
            break
        data = pickle.dumps(frame)
        message_size = struct.pack("L", len(data))
        connection.sendall(message_size + data)
        if cv2.waitKey(1) == ord("f"):
            break

def receive_video(connection):
    data = b""
    payload_size = struct.calcsize("L")
    while True:
        while len(data) < payload_size:
            packet = connection.recv(4096)
            if not packet:
                break
            data += packet
        if not data:
            break
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += connection.recv(4096)
        
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        cv2.imshow('Server Video', frame)
        if cv2.waitKey(1) == ord("q"):
            break

def main():
    ip = '127.0.0.1'  # Endereço IP do servidor (local)
    porta = 5000  # Porta do servidor

    conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao.connect((ip, porta))

    webcam = cv2.VideoCapture(0)

    send_thread = threading.Thread(target=send_video, args=(conexao, webcam))
    receive_thread = threading.Thread(target=receive_video, args=(conexao,))
    
    send_thread.start()
    receive_thread.start()
    
    send_thread.join()
    receive_thread.join()

    conexao.close()
    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
