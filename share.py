shape = {'RectItem': '1\r\n', 'EllipseItem': '2\r\n'}
proportion = 1.2  # 机械臂坐标系大小为画布大小的几倍
point_num = 50  # 初始点位
msg_hanji_satrtcode = '1\r\n'


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
    if point_num > 53:
        point_num = 50
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
        print('item_list ', len(self.item_list))
        for item in self.item_list:
            self.msg_shapes.append(shape.get(item.__class__.__name__))
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
                self.msg_points.append(msg_transform(x_ls[i], y_ls[i]))
        print('shapes %d\npoints %d' % (len(self.msg_shapes), len(self.msg_points)))
        self.item_list.clear()

    def clear_buff(self):
        self.item_list.clear()
        self.msg_shapes.clear()
        self.msg_points.clear()
        print('len item_list%d\nshapes %d\npoints %d' % (len(self.item_list), len(self.msg_shapes), len(self.msg_points)))


class ShareInfo:
    gstore = Gstore()
