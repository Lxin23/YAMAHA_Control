#  === TCP 服务端程序 server.py ===
import threading
import socket
import time
import traceback

from share import ShareInfo

# 主机地址为空字符串，表示绑定本机所有网络接口ip地址
# 等待客户端来连接
IP = '192.168.31.105'
# 端口号
PORT = 24
# 定义一次从socket缓冲区最多读入512个字节数据
BUFLEN = 1024
point_num = 50  # 第一个坐标点的编号
# msg_next_shape = 'ok'
msg_next_point = 'GoAhead'
msg_next_shape = 'ShapeSend'
msg_start_point = 'PointSend'
msg_stop_send_point = 'Finished'
state_point = 0


def msg_send_shape(dataSocket):
    if len(ShareInfo.gstore.msg_shapes):
        print('send shape:', ShareInfo.gstore.msg_shapes[0])
        dataSocket.send(ShareInfo.gstore.msg_shapes[0].encode())
        ShareInfo.gstore.msg_shapes.pop(0)
    else:
        print('no shape to send')


def msg_send_point(dataSocket):
    if len(ShareInfo.gstore.msg_points):
        print('msg send:', ShareInfo.gstore.msg_points[0])
        dataSocket.send(ShareInfo.gstore.msg_points[0].encode())
        ShareInfo.gstore.msg_points.pop(0)
    else:
        print('no point to send')


def connectionRun():
    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    listenSocket.bind((IP, PORT))

    listenSocket.listen(8)
    print(f'服务端启动成功，在{PORT}端口等待客户端连接...')

    dataSocket, addr = listenSocket.accept()
    print('接受一个客户端连接:', addr)
    global state_point
    while True:
        recved = dataSocket.recv(BUFLEN)    # 期望接受 ShapeSend, PointSend

        if not recved:
            continue

        info = recved.decode()
        print(f'收到对方信息： {info}')
        if msg_next_shape in info:  # 发送形状码
            print('accept the start imformation')
            # ShareInfo.gstore.update_msg()
            msg_send_shape(dataSocket)  # 发送ShapeCode

        if msg_start_point in info:  # 发送坐标信息
            while True:
                msg_send_point(dataSocket)  # 发送单个point
                recved_GoAhead = dataSocket.recv(BUFLEN)        # 期望接收 GoAhead
                if msg_next_point in recved_GoAhead.decode():  # 等待接收消息发送下一个坐标点
                    continue
                elif msg_stop_send_point in recved_GoAhead.decode():
                    print('point msg send finished')
                    break
                else:
                    print('error: accept the', recved_GoAhead.decode())
                    break

    dataSocket.close()
    listenSocket.close()
    print('connection closed')


def server_thread():
    while True:
        try:
            connectionRun()
        except:
            print(traceback.format_exc())


def start_server_thread():
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
