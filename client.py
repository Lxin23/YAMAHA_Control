import threading
import socket
import time
import traceback

from share import Gstore

IP = '192.168.0.120'
SERVER_PORT = 24
BUFLEN = 1024
point_num = 50  # 第一个坐标点的编号
proportion = 1.2  # 机械臂坐标系大小为画布大小的几倍
msg = []
msg_shapes = []
shape = {'RectItem': '0\n', 'EllipseItem': '1\n'}
msg_next_shape = 'ok'
msg_next_point = 'GoAhead'


def format_number(num):
    """
    :param num: the number to be formatted
    :return: the number after formatted
    """
    # 确保数字是浮点数
    num = float(num)
    # 使用format进行格式化
    formatted_num = "{:0.3f}".format(num)
    # 分割整数部分和小数部分
    integer_part, decimal_part = formatted_num.split('.')
    # 如果整数部分不足三位，前面补零
    integer_part = integer_part.zfill(3)
    # 如果小数部分不足三位，后面补零
    decimal_part = decimal_part.ljust(3, '0')
    # 加上正负号和小数点，并返回结果
    return f"{num >= 0 and '+' or ''}{integer_part}.{decimal_part}"


def update_msg():
    """
    to update the msg to send
    :return:
    """
    print('len item_list', len(Gstore.item_list))
    for item in Gstore.item_list:
        msg_shapes.append(shape[item.__class__.__name__])
        # x_1 = item.pos().x()
        # y_1 = item.pos().y()
        x_1, y_1 = item.props['空间坐标'].split('，')
        x_1 = float(x_1)
        y_1 = float(y_1)
        x_2 = x_1 + item.rect().width()
        y_2 = y_1 + item.rect().height()
        # detail = f'{item.__class__.__name__}.pos:\n({x_1}, {y_1})\t({x_2}, {y_1})\t({x_1}, {y_2})\t({x_2}, {y_2})'
        x_ls = [x_1, x_2, x_2, x_1]
        y_ls = [y_1, y_1, y_2, y_2]
        '''
        P1 = 0 0 0 0 0 0
        P2 = 100.00 200.00 50.00 0.00 0.00 0.00
        P3 = 10.00 0.00 0.00 0.00 0.00 0.00
        '''

        for i in range(4):
            # msg.append(f'P{point_num} = {x_ls[i]} {y_ls[i]} 0 0 0 0')
            msg.append(msg_transform(x_ls[i], y_ls[i]))
    print('shapes %d\npoints %d' % (len(msg_shapes), len(msg)))
    Gstore.item_list.clear()


# 对画布中坐标点转换到机械臂坐标系中
def msg_transform(fx, fy, fz=0.0, fr=0.0, fa=0.0, fb=0.0, f=1, f_1=0, f_2=0):
    """
    Pmmmm = fxxxxxx fyyyyyy fzzzzzz frrrrrr faaaaaa fbbbbbb
    P50=315.850 251.048 0.037 169.873 0.000 0.000 1 0 0
    P50=69.146 211.981 2.401 139.730 0.000 0.000 1 0 0
    """
    global point_num

    fx /= proportion
    fy /= proportion

    # msg = f'P{point_num} = {fx} {fy} {fz} {fr} {fa} {fb}'
    # 50,+069.146,+211.981,+002.401,+139.730 0.000 0.000 1 0 0
    msg = ('%d,%s,%s,%s,%s,%s,%s,%d,%d,%d' %
           (point_num, format_number(fx), format_number(fy), format_number(fz), format_number(fr),
            format_number(fa), format_number(fb), f, f_1, f_2))
    point_num += 1
    if point_num > 53:
        point_num = 50
    return msg


def connectionRun():
    print('Connecting to server...')
    # recvbuffer = b''
    # 实例化一个socket对象，指明协议
    dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接服务端socket
    # dataSocket.bind(('localhost', 60109))
    dataSocket.connect((IP, SERVER_PORT))

    print('connection to server ok')

    while True:
        try:
            # 等待接收服务端的消息
            print('\nwaiting for message to start...')
            recved = dataSocket.recv(BUFLEN)
        except socket.timeout:
            print('time out')
            continue
        except:
            print(traceback.format_exc())
            break

        if recved.decode() == msg_next_shape:
            print('recved:', recved.decode())
            break

    while True:
        try:
            # 更新消息队列
            update_msg()
            if len(msg_shapes):
                # 消息发送
                print('send shape:', msg_shapes[0])
                dataSocket.send(msg_shapes.pop(0).encode())
            else:
                print('暂无待发送消息')
                time.sleep(1)
                continue
            # while len(msg):
            for i in range(4):
                print('msg send:', msg[0].encode())
                dataSocket.send(msg[0].encode())
                msg.pop(0)
                time.sleep(1)

            # print('等待机械臂响应...')
            while True:
                try:
                    # 等待接收服务端的消息
                    print('\nwaiting for message to next point...')
                    recved = dataSocket.recv(BUFLEN)
                except socket.timeout:
                    print('time out')
                    continue
                except:
                    print('error', traceback.format_exc())
                    break

                # 如果返回空bytes，表示对方关闭了连接
                if not recved:
                    print('server closed connection ...')
                    # 退出循环
                    break
                # 打印读取的信息
                recv = recved.decode()
                print(recv)

                if recv == msg_next_point:
                    print('accepted the message to next point')
                    break

                # endPos = recved.index(b'\x04')
                #
                # # 还没有接收到完整的消息
                # if endPos < 0:
                #     recvbuffer += recved
                #     continue
                #
                # # 接收到完整的消息
                # msgBytes = recvbuffer + recved[:endPos]
                # print('\n收到消息', msgBytes)
                #
                # recvbuffer = recved[endPos + 1:]

        except:
            print(traceback.format_exc())
            print('server closed connection')
            break

    dataSocket.close()
    print('connection closed')


def connectThread():
    while True:
        try:
            connectionRun()
        except:
            print(traceback.format_exc())


def startCommunicationThread():
    thread = threading.Thread(target=connectThread, daemon=True)
    thread.start()
