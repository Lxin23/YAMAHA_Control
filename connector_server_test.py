#  === TCP 服务端程序 server.py ===
import threading
import socket
import time
import traceback

from share import ShareInfo

# 主机地址为空字符串，表示绑定本机所有网络接口ip地址
# 等待客户端来连接
IP = '192.168.0.120'
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
msg_start_hanji = 'HanjiStart'
msg_complete_hanji = 'COMPLETE'
msg_hanji_satrtcode = '1\r\n'
state_point = 0


def msg_send_shape(dataSocket):
    if len(ShareInfo.gstore.msg_shapes):
        print('send shape:', ShareInfo.gstore.msg_shapes[0])
        dataSocket.send(ShareInfo.gstore.msg_shapes[0].encode())
        return ShareInfo.gstore.msg_shapes.pop(0)
    else:
        print('no shape to send')
        return -1


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
        # print('等待接收消息')
        recved = dataSocket.recv(BUFLEN)  # 期望接受 ShapeSend, PointSend

        if not recved:
            # time.sleep(5)
            # continue
            # 连接中断
            break

        info = recved.decode()
        print(f'收到对方信息： {info}')
        if msg_next_shape in info:  # 发送形状码
            print('accept the start imformation')
            # ShareInfo.gstore.update_msg()
            ShapeCode = msg_send_shape(dataSocket)  # 发送ShapeCode

            if ShapeCode == -1:
                while len(ShareInfo.gstore.msg_points) == 0:
                    time.sleep(0.5)
                msg_send_shape(dataSocket)

            # recv = dataSocket.recv(BUFLEN)
            # print(f'收到对方信息： {recv.decode()}')

            # if ShapeCode[0] in recv.decode():  # 我们发送过去的与对方接收到的一
            #     print('消息一致')
            #     continue
            # else:
            #     print('recvied error: ShapeReturn not equal ShapeSend')

        if msg_start_point in info:  # 发送坐标信息
            print('开始发送点位')
            while True:
                msg_send_point(dataSocket)  # 发送单个point
                recved_GoAhead = dataSocket.recv(BUFLEN)  # 期望接收 GoAhead

                print(recved_GoAhead.decode())

                if 'GoAhead4' in recved_GoAhead.decode():
                    print('point msg send finished')
                    break
                elif msg_next_point in recved_GoAhead.decode():  # 等待接收消息发送下一个坐标点
                    continue
                # elif msg_stop_send_point in recved_GoAhead.decode():
                #     print('point msg send finished')
                #     break
                else:
                    print('error: accept the', recved_GoAhead.decode())
                    break

        if msg_start_hanji in info:
            time.sleep(1)
            dataSocket.send(ShareInfo.gstore.msg_hanji_satrt.encode())
            print(f'发送焊机启动消息 {ShareInfo.gstore.msg_hanji_satrt}')

        if msg_complete_hanji in info:
            print('收到 焊机完成信息')
            ShareInfo.gstore.msg_dialog = 'stop'
            # print(ShareInfo.gstore.msg_dialog)

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
