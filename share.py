import math


shape = {
    'RectItem': '1\r\n',
    'EllipseItem': '2\r\n',
    "DiamondItem": '3\r\n',
    'LineItem': '4\r\n',
    'PentagonItem': '5\r\n',
    'HexagonItem': '6\r\n',
}

proportion = 4.8  # 机械臂坐标系大小为画布大小的几倍, 为 1 时为测试, 比例为 4.8
point_num = 50  # 初始点位
msg_hanji_satrtcode = '1\r\n'
f_z = -1.0  # 机械臂 z 轴坐标，往上是减
f_r = 84.5
canvas_max_y = 600


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
    if integer_part[0] == '-':
        integer_part = integer_part.zfill(4)
    else:
        integer_part = integer_part.zfill(3)
    # 如果小数部分不足三位，后面补零
    decimal_part = decimal_part.ljust(3, '0')
    # 加上正负号和小数点，并返回结果
    return f"{num >= 0 and '+' or ''}{integer_part}.{decimal_part}"


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
    msg = ('%d,%s,%s,%s,%s,%s,%s,%d,%d,%d\r\n' %
           (point_num, format_number(fx), format_number(fy), format_number(fz), format_number(fr),
            format_number(fa), format_number(fb), f, f_1, f_2))
    point_num += 1
    return msg


class Gstore:
    msg_dialog = ''
    item_list = []
    msg_shapes = []
    msg_points = []
    msg_hanji_satrt = msg_hanji_satrtcode

    def update_msg(self):
        """
        to update the msg to send
        :return:
        """
        # print('item_list ', len(self.item_list))
        global point_num

        for item in self.item_list:
            shape_code = shape.get(item.__class__.__name__)
            self.msg_shapes.append(shape_code)

            if shape_code == shape.get('RectItem'):
                x_1, y_1 = item.props['空间坐标'].split('，')
                x_1 = float(x_1)
                y_1 = float(y_1)
                x_2 = x_1 + item.rect().width()
                y_2 = y_1 + item.rect().height()
                x_ls = [x_1, x_2, x_2, x_1]
                y_ls = [y_1, y_1, y_2, y_2]
            elif shape_code == shape.get('EllipseItem'):
                x_1, y_1 = item.props['空间坐标'].split('，')
                x_1 = float(x_1)
                y_1 = float(y_1)
                x_2 = x_1 + (item.rect().width() / 2)
                y_2 = y_1 + (item.rect().height() / 2)
                x_ls = [x_1, x_2, x_1 + item.rect().width(), x_2]
                y_ls = [y_2, y_1 + item.rect().height(), y_2, y_1]
            elif shape_code == shape.get('LineItem'):
                x_1, y_1 = item.props['空间坐标'].split('，')
                x_1 = float(x_1)
                y_1 = float(y_1)
                line = item.line()
                dx = line.dx()
                dy = 0 - line.dy()
                x_2 = x_1 + dx
                y_2 = y_1 + dy
                x_ls = [x_1, x_2, x_2, x_2]
                y_ls = [y_1, y_2, y_2, y_2]
            elif shape_code == shape.get('DiamondItem'):
                # 菱形的空间坐标是正下方顶点的空间坐标
                x, y = item.props['空间坐标'].split('，')
                x = float(x)
                y = float(y)
                length = float(item.props['菱形边长'])
                l = length / 1.414

                x_1 = x
                y_1 = y

                x_2 = x_1 + l
                x_3 = x_1 - l
                y_2 = y + l
                y_3 = y + 2 * l

                x_ls = [x_1, x_2, x_1, x_3]
                y_ls = [y_1, y_2, y_3, y_2]
            elif shape_code == shape.get('PentagonItem'):
                # 五边形的坐标为顶点下方的边的中心
                x, y = item.props['空间坐标'].split('，')
                x = float(x)
                y = float(y)
                length = float(item.props['五边形边长'])
                height = 0.5 * length / math.tan(math.radians(18))

                x_1 = x
                y_1 = y + height
                x_2 = x_1 + length * math.cos(math.radians(36))
                x_3 = x_1 + 0.5 * length
                x_4 = x_1 - 0.5 * length
                x_5 = x_1 - length * math.cos(math.radians(36))
                y_2 = y_1 - length * math.sin(math.radians(36))
                y_3 = y

                # x_2 = math.cos(math.radians(36)) * length
                # y_2 = math.sin(math.radians(36)) * length
                # # x_3 = math.cos(math.radians(72)) * l
                # x_3 = 0.5 * length
                # # y_3 = math.sin(math.radians(72)) * l
                # y_3 = 0.5 * length / math.tan(math.radians(18))

                x_ls = [x_1, x_2, x_3, x_4, x_5]
                y_ls = [y_1, y_2, y_3, y_3, y_2]
            elif shape_code == shape.get('HexagonItem'):
                # 六边形的坐标为左边顶点的垂线与底边延长线的交点
                sq3 = 1.732
                x, y = item.props['空间坐标'].split('，')
                x = float(x)
                y = float(y)
                length = float(item.props['六边形边长'])
                weight = 0.5 * length
                height = sq3 * weight

                x_1 = x
                y_1 = y + height

                x_2 = x_1 + 0.5 * length
                x_3 = x_1 + 1.5 * length
                x_4 = x_1 + 2 * length
                y_2 = y
                y_3 = y + 2 * height

                x_ls = [x_1, x_2, x_3, x_4, x_3, x_2]
                y_ls = [y_1, y_3, y_3, y_1, y_2, y_2]
            else:
                print('图形信息错误', item.__class__.__name__)
                continue

            for i in range(len(x_ls)):  # 发送十个点
                # msg.append(f'P{point_num} = {x_ls[i]} {y_ls[i]} 0 0 0 0')
                self.msg_points.append(msg_transform(x_ls[i], y_ls[i], fz=f_z, fr=f_r))

            for i in range(10 - len(x_ls)):
                self.msg_points.append(msg_transform(x_ls[len(x_ls) - 1], y_ls[len(x_ls) - 1], fz=f_z, fr=f_r))

        point_num = 50
        print('shapes %d\npoints %d' % (len(self.msg_shapes), len(self.msg_points)))
        self.item_list.clear()

    def clear_buff(self):
        self.item_list.clear()
        self.msg_shapes.clear()
        self.msg_points.clear()
        print(
            'len item_list%d\nshapes %d\npoints %d' % (len(self.item_list), len(self.msg_shapes), len(self.msg_points)))


class ShareInfo:
    gstore = Gstore()
