# 主程序代码
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QTransform, QAction, QIcon, QPainter, QLinearGradient, QColor
from PySide6.QtWidgets import QWidget, QSizePolicy, QProgressBar, QProgressDialog, QVBoxLayout, QLabel, QDialog, \
    QInputDialog, QMessageBox, QFileDialog, QPushButton, QMenu, QLineEdit, QHBoxLayout
from qt_material import apply_stylesheet
# import qtawesome as qta
import qdarkstyle
import json
import math
import sys
import os

from connector_server import start_server_thread
from share import ShareInfo
import share

canvas_X_MAX = 958
canvas_Y_MAX = 600
# X_MAX = 210， Y_MAX = 150，机械臂活动范围
shape_draw = ["rectangle", "ellipse", "line", "diamond", "pentagon", "hexagon"]
point_format = '{:.1f}'
qss_file = './QSS_files/blacksoft.css'
json_file = ''
end = '_w.png'
# end = '.png'  # 文件后缀名，_w 指white


class SetZDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(300, 100)
        self.main_layout = QVBoxLayout()

        self.label_1 = QLabel("请输入z轴高度: ")
        self.label_1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.label_1)

        self.line_edit = QLineEdit()
        self.line_edit.setText(str(share.f_z))
        self.main_layout.addWidget(self.line_edit)

        self.label_2 = QLabel("")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.label_2)

        self.btn_1 = QPushButton("运行")
        self.btn_2 = QPushButton("修改")
        self.btn_3 = QPushButton("保存")
        layout_2 = QHBoxLayout()
        layout_2.addWidget(self.btn_1)
        layout_2.addWidget(self.btn_2)
        layout_2.addWidget(self.btn_3)

        self.main_layout.addLayout(layout_2)
        self.setLayout(self.main_layout)
        self.bind()
        self.setWindowTitle("设置z轴高度")

    def bind(self):
        self.btn_1.clicked.connect(self.send_z)
        self.btn_2.clicked.connect(self.change)
        self.btn_3.clicked.connect(self.close)

    def change(self):
        ShareInfo.gstore.msg_z_statue = 'keep'
        self.line_edit.setReadOnly(False)

    def send_z(self):
        ShareInfo.gstore.msg_z_statue = ''
        z_height = self.line_edit.text()
        share.f_z = float(z_height)
        self.label_2.setText("机械臂移动中...")
        ShareInfo.gstore.update_z_test()
        self.line_edit.setReadOnly(True)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_statue)
        self.timer.start(500)

    def update_statue(self):
        if ShareInfo.gstore.msg_set_z == 'stop':
            ShareInfo.gstore.msg_set_z = 'go'
            self.label_2.setText("机械臂移动完毕")
            self.timer.stop()

    def closeEvent(self, event):
        ShareInfo.gstore.msg_z_statue = 'finish'
        ShareInfo.gstore.clear_buff()
        event.accept()



class ProgressBar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.resize(310, 80)
        # 载入进度条控件
        # self.pgb = QProgressBar(self)
        self.setWindowTitle("绘制进行中...")
        self.text = QLabel("请等待...")
        # self.text.move(130, 30)
        self.text.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        # layout.addWidget(self.text)
        layout.addWidget(self.text, 0, Qt.AlignCenter)
        button_restart = QPushButton("重新启动")
        layout.addWidget(button_restart)
        button_restart.clicked.connect(self.restart)
        # self.setLayout(layout)

    def restart(self):
        ShareInfo.gstore.restart()

    def closeEvent(self, event):
        ShareInfo.gstore.clear_buff()

        event.accept()


class Item:
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Up:
            self.setPos(self.x(), self.y() - 1)
        elif e.key() == Qt.Key_Down:
            self.setPos(self.x(), self.y() + 1)
        elif e.key() == Qt.Key_Left:
            self.setPos(self.x() - 1, self.y())
        elif e.key() == Qt.Key_Right:
            self.setPos(self.x() + 1, self.y())

    def itemChange(self, change, value, ):

        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # 更新属性表中的坐标值
            x, y = self.map_xy(value.x(), value.y())
            if x == -0.0:
                x = 0.0
            if y == -0.0:
                y = 0.0
            self.props['空间坐标'] = f"{x}，{y}"
            # print(x, y, sep=' ')
            window.setPropTable(self.props)

        # 被选中
        if change == QtWidgets.QGraphicsItem.ItemSelectedChange and value == True:
            # 设置属性框内容
            print("item selected")
            window.setPropTable(self.props)

        return super().itemChange(change, value)

    def toSaveData(self):
        pos = self.pos()
        print([pos.x(), pos.y()])
        return {
            'type': self.__class__.__name__,
            'pos': [pos.x(), pos.y()],
            'props': self.props
        }


class DiamondItem(Item, QtWidgets.QGraphicsPolygonItem):
    def __init__(self, *args):
        super().__init__(*args)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)

        self.props = {
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
            # 'length': '10',
            '菱形边长': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '3',
            '线条颜色': '0, 0, 0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        # print(data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        length = props['菱形边长']
        self.setPolygon(float(length))
        self.setPos(*data["pos"])

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            x, y = cfgValue.split('，')
            x = float(x)
            y = float(y)
            self.setPolygon(float(self.props['菱形边长']))
            print("set", x, y)

            # 更新矩形的位置，但保留原来的宽度和高度
            # self.setPos(x, y)
            self.remap_xy(x, y)
            print("changed", self.pos().x(), self.pos().y())

        elif cfgName == '菱形边长':
            length = float(cfgValue)
            self.setPolygon(length)
            x, y = self.props['空间坐标'].split('，')
            x = float(x)
            y = float(y)
            # self.setPos(x, y)
            self.remap_xy(x, y)
            # self.moveBy()

            # self.setPos(x, y)
            # print(x, y)

        elif cfgName == '填充颜色':
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            self.setBrush(QtGui.QBrush(color))

        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def setPolygon(self, length: float):
        x = 0
        y = 0
        q_ls = []

        x_1 = x
        y_1 = y

        l = length / 1.414
        x_2 = l
        x_3 = -l
        y_2 = l
        y_3 = 2 * l

        q_ls.append(QPointF(x_1, y_1))
        q_ls.append(QPointF(x_2, y_2))
        q_ls.append(QPointF(x_1, y_3))
        q_ls.append(QPointF(x_3, y_2))

        super().setPolygon(q_ls)

    def remap_xy(self, x, y):
        x = float(x) + float(self.props['菱形边长']) / 1.414
        y = canvas_Y_MAX - float(y) - float(self.props['菱形边长']) * 1.414
        self.setPos(x, y)

    def map_xy(self, x, y):
        length = float(self.props['菱形边长']) / 1.414
        x = point_format.format(x - length)
        y = point_format.format(canvas_Y_MAX - float(y) - float(self.props['菱形边长']) * 1.414)
        return float(x), float(y)


class HexagonItem(Item, QtWidgets.QGraphicsPolygonItem):
    def __init__(self, *args):
        super().__init__(*args)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)

        self.props = {
            '空间坐标': '0，0',
            # 'length': '10',
            '六边形边长': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '3',
            '线条颜色': '0, 0, 0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        # print(data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        length = props["六边形边长"]
        self.setPolygon(float(length))
        self.setPos(*data["pos"])

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            x, y = cfgValue.split('，')
            x = float(x)
            y = float(y)
            print("set", x, y)

            # 更新矩形的位置，但保留原来的宽度和高度
            self.remap_xy(x, y)
            print("changed", self.pos().x(), self.pos().y())

        elif cfgName == '六边形边长':
            length = float(cfgValue)
            self.setPolygon(length)
            x, y = self.props['空间坐标'].split('，')
            x = float(x)
            y = float(y)
            self.remap_xy(x, y)
            # self.moveBy()

            # self.setPos(x, y)
            # print(x, y)

        elif cfgName == '填充颜色':
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            self.setBrush(QtGui.QBrush(color))

        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def setPolygon(self, length: float):
        sq3 = 1.732
        x = 0
        y = 0
        q_ls = []

        x_1 = x
        x_2 = 0.5 * length
        x_3 = 1.5 * length
        x_4 = 2 * length
        y_1 = y
        y_2 = 0.5 * sq3 * length
        y_3 = -0.5 * sq3 * length

        q_ls.append(QPointF(x_1, y_1))
        q_ls.append(QPointF(x_2, y_2))
        q_ls.append(QPointF(x_3, y_2))
        q_ls.append(QPointF(x_4, y_1))
        q_ls.append(QPointF(x_3, y_3))
        q_ls.append(QPointF(x_2, y_3))

        super().setPolygon(q_ls)

    def remap_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y) - float(self.props['六边形边长']) * 1.732 / 2
        self.setPos(x, y)

    def map_xy(self, x, y):
        x = float(x)
        y = point_format.format(canvas_Y_MAX - float(y) - float(self.props['六边形边长']) * 1.732 / 2)
        return x, float(y)


class PentagonItem(Item, QtWidgets.QGraphicsPolygonItem):
    def __init__(self, *args):
        super().__init__(*args)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)

        self.props = {
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
            # 'length': '10',
            '五边形边长': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '3',
            '线条颜色': '0, 0, 0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        # print(data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        length = props['五边形边长']
        self.setPolygon(float(length))
        self.setPos(*data["pos"])

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            x, y = cfgValue.split('，')
            x = float(x)
            y = float(y)
            print("set", x, y)

            # 更新矩形的位置，但保留原来的宽度和高度
            self.remap_xy(x, y)
            print("changed", self.pos().x(), self.pos().y())

        elif cfgName == '五边形边长':
            length = float(cfgValue)
            self.setPolygon(length)
            x, y = self.props['空间坐标'].split('，')
            x = float(x)
            y = float(y)
            self.remap_xy(x, y)

        elif cfgName == '填充颜色':
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            self.setBrush(QtGui.QBrush(color))

        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def setPolygon(self, length: float):
        x = 0
        y = 0
        # l = 0.5 * length / math.sin(math.radians(18))
        # print('%.2f' % l)
        q_ls = []

        x_1 = x
        x_2 = math.cos(math.radians(36)) * length
        y_2 = math.sin(math.radians(36)) * length
        y_1 = y
        # x_3 = math.cos(math.radians(72)) * l
        x_3 = 0.5 * length
        # y_3 = math.sin(math.radians(72)) * l
        y_3 = 0.5 * length / math.tan(math.radians(18))

        q_ls.append(QPointF(x_1, y_1))
        q_ls.append(QPointF(x_2, y_2))
        q_ls.append(QPointF(x_3, y_3))
        q_ls.append(QPointF(-x_3, y_3))
        q_ls.append(QPointF(-x_2, y_2))

        # q_ls.append(QPointF(x_1, y_1))
        # q_ls.append(QPointF(-x_3, y_3))
        # q_ls.append(QPointF(x_2, y_2))
        # q_ls.append(QPointF(-x_2, y_2))
        # q_ls.append(QPointF(x_3, y_3))

        super().setPolygon(q_ls)

    def remap_xy(self, x, y):
        x = float(x) + float(self.props['五边形边长']) * math.cos(math.radians(36))
        y = canvas_Y_MAX - float(y) - 0.5 * float(self.props['五边形边长']) / math.tan(math.radians(18))
        self.setPos(x, y)

    def map_xy(self, x, y):
        x = point_format.format(float(x) - float(self.props['五边形边长']) * math.cos(math.radians(36)))
        y = point_format.format(canvas_Y_MAX - float(y) - 0.5 * float(self.props['五边形边长']) / math.tan(math.radians(18)))
        return float(x), float(y)


class RectItem(Item, QtWidgets.QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)

        self.props = {
            '空间坐标': '0，0',
            '矩形宽度': '100',
            '矩形高度': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '3',
            '线条颜色': '0, 0, 0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        # print(data["pos"])
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        qrf = self.rect()
        qrf.setWidth(float(props["矩形宽度"]))
        qrf.setHeight(float(props["矩形高度"]))
        self.setRect(qrf)

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            # self.moveBy()
            print(cfgValue)
            # qrf = self.rect()
            x, y = cfgValue.split('，')
            # y = Y_MAX - float(y)
            print("set", x, y)

            self.remap_xy(x, y)
            # 更新矩形的位置，但保留原来的宽度和高度
            # self.setPos(self.mapFromScene(QPointF(x, y)))
            # self.setPos(QPointF(x, y))
            # self.setRect(x, y, float(self.props['矩形长度']), float(self.props['矩形高度']))

            print("changed", self.pos().x(), self.pos().y())
            # qrf.setX(float(x))
            # qrf.setY(float(y))
            # self.setRect(float(x), float(y), float(self.props['矩形长度']), float(self.props['矩形高度']))

        elif cfgName == '矩形宽度':
            qrf = self.rect()
            print('set', cfgValue)
            qrf.setWidth(float(cfgValue))
            print('changed', qrf.width())
            self.setRect(qrf)  # 重新设定

        elif cfgName == '矩形高度':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            x, y = self.props['空间坐标'].split('，')
            self.setRect(qrf)  # 重新设定
            self.remap_xy(x, y)

        elif cfgName == '填充颜色':
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            self.setBrush(QtGui.QBrush(color))

        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def remap_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y) - self.rect().height()
        self.setPos(x, y)

    def map_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y) - self.rect().height()
        return x, y


class EllipseItem(Item, QtWidgets.QGraphicsEllipseItem):
    def __init__(self, *args):
        super().__init__(*args)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)

        self.props = {
            '空间坐标': '0，0',
            '圆形直径': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '3',
            '线条颜色': '0, 0, 0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        self.setPos(*data["pos"])
        self.setZValue(float(props["zValue"]))

        # 其他设置
        qrf = self.rect()
        qrf.setWidth(float(props["圆形直径"]))
        qrf.setHeight(float(props["圆形直径"]))
        self.setRect(qrf)

        color = QtGui.QColor(*[int(v) for v in props["填充颜色"].replace(' ', '').split(',')])
        self.setBrush(QtGui.QBrush(color))

        pen = self.pen()
        pen.setWidth(int(props["线条宽度"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["线条颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            print(cfgValue)
            x, y = cfgValue.split('，')
            x = float(x)
            # y = Y_MAX - float(y)
            y = canvas_Y_MAX - float(y) - self.rect().height()
            y = float(y)
            print("set", x, y)
            self.setPos(x, y)

        elif cfgName == '圆形直径':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            qrf.setWidth(float(cfgValue))
            x, y = self.props['空间坐标'].split('，')
            self.setRect(qrf)  # 重新设定
            self.remap_xy(x, y)

        elif cfgName == '填充颜色':
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            self.setBrush(QtGui.QBrush(color))

        elif cfgName == '线条颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线条宽度':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def remap_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y) - self.rect().height()
        self.setPos(x, y)

    def map_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y) - self.rect().height()
        return x, y


class LineItem(Item, QtWidgets.QGraphicsLineItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
            '线宽': '3',
            '颜色': '0, 0, 0',
            '线长': '100',
            '旋转角度': '0',
            'zValue': '0.0',
        }

    def loadData(self, data):
        # 设置props
        self.props = data["props"]
        props = self.props
        x, y = data["pos"]
        self.setZValue(float(props["zValue"]))

        pen = self.pen()
        pen.setWidth(int(props["线宽"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

        # 其他设置
        line = self.line()
        line.setLength(float(props["线长"]))

        line.setLine(0, 0, 0 + float(props["线长"]), 0)
        # line.setAngle(float(props["旋转角度"]))
        # print("线条",line)
        self.setLine(line)
        # print(self.line().length())
        # self.setPos(*data["pos"])
        # print(*data["pos"], sep=' ')
        # print(line)
        # self.setPos(100, 100)
        self.remap_xy(*(props['空间坐标'].split('，')))

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            # print(cfgValue)
            # qrf = self.pen()
            x, y = cfgValue.split('，')
            self.remap_xy(x, y)

        if cfgName == '线宽':
            pen = self.pen()
            pen.setWidth(int(cfgValue))
            self.setPen(pen)

        elif cfgName == '颜色':
            pen = self.pen()
            color = QtGui.QColor(*[int(v) for v in cfgValue.replace(' ', '').split(',')])
            pen.setColor(color)
            self.setPen(pen)

        elif cfgName == '线长':
            line = self.line()
            line.setLength(float(cfgValue))
            self.setLine(line)

        elif cfgName == '旋转角度':
            line = self.line()
            line.setAngle(float(cfgValue))
            self.setLine(line)

        elif cfgName == 'zValue':
            self.setZValue(float(cfgValue))

        else:
            return

    def remap_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y)
        y = float(y)
        print(x, y, sep=' ')
        self.setPos(x, y)
        print(self.pos())

    def map_xy(self, x, y):
        x = float(x)
        y = canvas_Y_MAX - float(y)
        return x, y


class TextItem(Item, QtWidgets.QGraphicsTextItem):
    html_templt = '''<div style='color:$color$;
    font-size:$size$px;
    font-weight:$weight$;
    font-family:$font$;
    '>$content$</div>'''

    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '空间坐标': str(self.pos().x()) + ',' + str(self.pos().y()),
            '内容': '文字内容',
            '颜色': 'black',
            '大小': '12',
            '字体': '微软雅黑',
            '字粗': 'normal',
            'zValue': '0.0',
        }

    def set_word_content(self, ):
        html = self.html_templt.replace('$content$', self.props['内容'])
        html = html.replace('$color$', self.props['颜色'])
        html = html.replace('$size$', self.props['大小'])
        html = html.replace('$font$', self.props['字体'])
        html = html.replace('$weight$', self.props['字粗'])

        self.setHtml(html)

    def loadData(self, data):
        self.props = data["props"]
        self.setPos(*data["pos"])
        self.setZValue(float(self.props["zValue"]))
        self.set_word_content()

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            x, y = cfgValue.split('，')
            x = float(x)
            # y = Y_MAX - float(y)
            y = float(y)
            self.setPos(x, y)

        if cfgName == 'zValue':
            self.setZValue(float(cfgValue))
        else:
            self.set_word_content()


class DragLabel(QtWidgets.QLabel):

    def mouseMoveEvent(self, e):
        if e.buttons() != Qt.LeftButton:
            return

        mimeData = QtCore.QMimeData()

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.exec(Qt.DropActions.MoveAction)


class DnDGraphicView(QtWidgets.QGraphicsView):

    def __init__(self, *args):
        super().__init__(*args)
        self.lastDropItem = None

    def dragMoveEvent(self, e):
        pass

    def dragEnterEvent(self, e):

        if hasattr(e.source(), 'dndinfo'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        picName = e.source().dndinfo['name']

        if picName == shape_draw[0]:
            shape = RectItem(0, 0, 100, 100)
            shape.setPos(e.position().x(), e.position().y() - 100)

        elif picName == shape_draw[1]:
            shape = EllipseItem(0, 0, 100, 100)
            shape.setPos(e.position().x(), e.position().y() - 100)

        elif picName == shape_draw[2]:
            shape = LineItem(0, 0, 100, 0)
            pen = shape.pen()
            pen.setWidth(3)
            shape.setPen(pen)
            shape.setPos(e.position().x(), e.position().y())

        elif picName == shape_draw[3]:
            l = 100 / 1.414
            shape = DiamondItem([QPointF(0, 0), QPointF(l, l), QPointF(0, 2 * l), QPointF(-l, l)])
            shape.setPos(e.position().x() + l, e.position().y() - 2 * l)
            # shape.props['length'] = str(shape.polygon().length())

        elif picName == shape_draw[4]:
            x_1 = 100 * math.cos(math.radians(36))
            y_1 = 100 * math.sin(math.radians(36))
            l = 50 / math.sin(math.radians(18))
            x_2 = l * math.cos(math.radians(72))
            y_2 = l * math.sin(math.radians(72))
            shape = PentagonItem([QPointF(0, 0), QPointF(x_1, y_1), QPointF(x_2, y_2),
                                  QPointF(-x_2, y_2), QPointF(-x_1, y_1)])
            shape.setPos(e.position().x() + x_1, e.position().y() - y_2)

        elif picName == shape_draw[5]:
            sq3 = 1.732
            shape = HexagonItem([QPointF(0, 0), QPointF(50, 50 * sq3), QPointF(150, 50 * sq3), QPointF(200, 0),
                                 QPointF(150, -50 * sq3), QPointF(50, -50 * sq3)])
            shape.setPos(e.position().x(), e.position().y() - 50 * sq3)

        elif picName == "text":
            shape = TextItem("文本内容")
        else:
            print('no shape')
            return

        # shape.setPos(e.position())
        print(shape.pos().y(), self.rect().height())
        y = shape.pos().y()
        # x = shape.pos().x()
        x = e.position().x()
        if picName == "rectangle" or picName == "ellipse":
            y = canvas_Y_MAX - shape.pos().y() - shape.rect().height()
        elif picName == "line":
            y = canvas_Y_MAX - shape.pos().y()
        elif picName == "diamond":
            y = canvas_Y_MAX - float(y) - 100 * 1.414
        elif picName == "hexagon":
            y = canvas_Y_MAX - float(y) - 100 * 1.732 / 2
        elif picName == "pentagon":
            y = canvas_Y_MAX - float(y) - 0.5 * 100 / math.sin(math.radians(18))
        shape.props['空间坐标'] = str('{:.1f}'.format(x) + '，' + '{:.1f}'.format(y))
        # print(shape.pos())
        self.scene().addItem(shape)

        # 设置item可以移动
        shape.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        # 设置item可以选中
        shape.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
        shape.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

        shape.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)

        # 设置第一次创建的时候选中
        if self.lastDropItem:
            try:
                self.lastDropItem.setSelected(False)
            except:
                pass
        shape.setSelected(True)
        self.lastDropItem = shape

    # 该方法使得view 改变大小时（比如拖拽主窗口resize）， scene大小跟着变化
    # 否则，view和secen大小不一致， 拖放item 时，位置就不对了。
    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = event.size()
        self.setSceneRect(0, 0, size.width(), size.height())


class MWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.cwd = os.getcwd()
        self.resize(1400, 900 - 242)  # toolbar.height = 30

        # central Widget
        centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(centralWidget)

        # central Widget 里面的 主 layout
        self.mainLayout = QtWidgets.QHBoxLayout(centralWidget)

        # 左边区
        self.setupLeftPane()

        # 参数 Qt.Vertical 是垂直分裂， Qt.Horizontal是水平分裂
        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.mainLayout.addWidget(self.splitter)

        # 中间绘制区
        self.setupCanvas()
        self.splitter.insertWidget(0, self.view)

        # 右边绘制去
        self.setupRightWidget()
        self.splitter.insertWidget(0, self.view)

        self.setupQmenu()
        # self.setupToolBar()
        # self.view.centerOn(50, -50)

        # self.setCanvasTransform()

    def setCanvasTransform(self):
        # 翻转Y轴，使其向上为正方向
        transform = QTransform()
        transform.scale(1, -1)  # 纵向翻转
        self.view.setTransform(transform)

    def setupQmenu(self):
        self.menu = self.menuBar()
        self.fileMenu = QMenu("文件")
        self.file_read = QAction("读取")
        self.file_save = QAction("保存")
        self.file_save_as = QAction("另存为")
        self.fileMenu.addActions([self.file_read, self.file_save, self.file_save_as])
        self.menu.addMenu(self.fileMenu)

        self.setting = QMenu("设置")
        self.setting_fz = QAction("机械臂Z轴高度")
        self.setting.addAction(self.setting_fz)
        self.menu.addMenu(self.setting)

        self.file_read.triggered.connect(self.load)
        self.file_save.triggered.connect(self.save)
        self.file_save_as.triggered.connect(self.save_as)
        self.setting_fz.triggered.connect(self.set_fz)

    def load(self):
        fileName_read = QFileDialog.getOpenFileName(self,
                                                    "文件读取",
                                                    self.cwd,
                                                    "json (*.json)")
        if str(fileName_read[0]) == "":
            QMessageBox.information(self, "提示", "未能成功读取文件，请重新读取。")  # 调用弹窗提示
        else:
            global json_file
            json_file = fileName_read[0]
            with open(fileName_read[0], 'r', encoding='utf8') as f:
                content = f.read()

            data: list = json.loads(content)
            data.reverse()

            for itemData in data:
                typeName = itemData["type"]

                theClass = globals()[typeName]
                item = theClass()
                item.loadData(itemData)
                self.scene.addItem(item)

                # 设置item可以移动
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
                # 设置item可以选中
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
                item.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

    def save(self):
        # print(json_file)
        if os.path.exists(json_file):
            itemSaveDataList = []
            for item in self.scene.items():
                if hasattr(item, 'toSaveData'):
                    # print(item.pos().x(), item.pos().y())
                    saveData = item.toSaveData()
                    itemSaveDataList.append(saveData)

            content = json.dumps(itemSaveDataList, indent=4, ensure_ascii=False)
            with open(json_file, 'w', encoding='utf8') as f:
                f.write(content)
        else:
            self.save_as()

    def save_as(self):
        fileName_save = QFileDialog.getSaveFileName(self,
                                                    "文件保存",
                                                    self.cwd,  # 起始路径
                                                    "json file (*.json)")  # 设置文件扩展名过滤,用双分号间隔)
        if str(fileName_save[0]) == "":
            QMessageBox.information(self, "提示", "没有保存数据,请重新保存。")  # 调用弹窗提示
        else:
            global json_file
            json_file = fileName_save[0]
            itemSaveDataList = []
            for item in self.scene.items():
                if hasattr(item, 'toSaveData'):
                    # print(item.pos().x(), item.pos().y())
                    saveData = item.toSaveData()
                    itemSaveDataList.append(saveData)

            content = json.dumps(itemSaveDataList, indent=4, ensure_ascii=False)
            with open(fileName_save[0], 'w', encoding='utf8') as f:
                f.write(content)

    def set_fz(self):
        d, ok = QInputDialog.getDouble(self, "设置机械臂Z轴高度", "请输入Z轴的值:",
                                       share.f_z, -10000, maxValue=10000, decimals=2,
                                       flags=Qt.WindowFlags(), step=1)
        share.f_z = d
        print(share.f_z)

    def get_pos(self):
        for item in self.scene.selectedItems():
            # print('pos: %.2f %.2f' % (item.pos().x(), item.pos().y()))
            if item.__class__.__name__ == "DiamondItem" or item.__class__.__name__ == "HexagonItem" or item.__class__.__name__ == "PentagonItem":
                print(item.pos())
                info = item.polygon()
                print(info)
                # for point in item.polygon().data():  # 多边形（菱形）
                #     print(point)
            elif item.__class__.__name__ == "RectItem":
                x_1, y_1 = item.props['空间坐标'].split('，')
                x_1 = float(x_1)
                y_1 = float(y_1)
                x_2 = x_1 + item.rect().width()
                y_2 = y_1 + item.rect().height()
                x_ls = [x_1, x_2, x_2, x_1]
                y_ls = [y_1, y_1, y_2, y_2]
                for i in range(4):
                    print('%.2f %.2f' % (x_ls[i], y_ls[i]))
            elif item.__class__.__name__ == "EllipseItem":
                x_1, y_1 = item.props['空间坐标'].split('，')
                x_1 = float(x_1)
                y_1 = float(y_1)
                x_2 = x_1 + (item.rect().width() / 2)
                y_2 = y_1 + (item.rect().height() / 2)
                x_ls = [x_1, x_2, x_1 + item.rect().width(), x_2]
                y_ls = [y_2, y_1 + item.rect().height(), y_2, y_1]
                for i in range(len(x_ls)):
                    print('%.2f %.2f' % (x_ls[i], y_ls[i]))
            elif item.__class__.__name__ == "LineItem":
                x_1, y_1 = self.pos().x(), self.pos().y()
                x_1 = float(x_1)
                y_1 = float(y_1)
                line = item.line()
                dx = line.dx()
                dy = 0 - line.dy()
                x_2 = x_1 + dx
                y_2 = y_1 + dy
                x_ls = [x_1, x_2, ]
                y_ls = [y_1, y_2, ]
                for i in range(len(x_ls)):
                    print('%.2f %.2f' % (x_ls[i], y_ls[i]))
            print('')

    def zero(self):
        for item in self.scene.selectedItems():
            item.remap_xy(0, 0)
            # item.setPos(0.0, 438.2)

    def delItem(self):
        import shiboken6
        items = self.scene.selectedItems()
        for item in items:
            # self.scene.removeItem(item)
            shiboken6.delete(item)

    def delAllItems(self):
        global josn_file
        json_file = ''
        self.scene.clear()
        self.scene.addItem(QtWidgets.QGraphicsRectItem(0, 0, 946, canvas_Y_MAX))

    def start(self):
        print('start')
        ShareInfo.gstore.msg_dialog = ''
        draws_type = [RectItem, EllipseItem, LineItem, DiamondItem, HexagonItem, PentagonItem]
        for item in self.scene.items():
            if item.__class__ in draws_type:
                ShareInfo.gstore.item_list.append(item)
        ShareInfo.gstore.item_list.reverse()

        ShareInfo.gstore.update_msg()

        self.pgb = ProgressBar()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # 每100毫秒更新一次

        self.pgb.exec()
        # self.pgb.show()
        # self.pgb.setFocus()

    def updateProgress(self):
        if ShareInfo.gstore.msg_dialog == 'stop':
            self.timer.stop()
            # self.pgb.accept()
            self.pgb.close()
            # self.pgb.hide()
            # self.destroy()
            # print('destroy 执行')

    def clear_buff(self):
        # print('clear buffer')
        # ShareInfo.gstore.clear_buff()
        self.ser_z_dialog = SetZDialog(self)
        self.ser_z_dialog.exec()

    def setupLeftPane(self):
        leftLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(leftLayout)

        pixmapLayout = QtWidgets.QGridLayout()
        leftLayout.addLayout(pixmapLayout)
        leftLayout.addStretch()

        row, col = 0, 0

        for shape in shape_draw:
            file_path = f'./images/{shape}{end}'
            pixmap = QtGui.QPixmap(file_path)
            # 设定图片缩放大小，这里是40个像素的宽度，高度也会等比例缩放
            pixmap = pixmap.scaledToWidth(40, Qt.SmoothTransformation)

            label = DragLabel()
            label.setToolTip(shape)
            label.dndinfo = {'name': shape}

            # 设置label显示的pixmap
            label.setPixmap(pixmap)

            pixmapLayout.addWidget(label, row, col)

            if col == 1:
                row += 1
                col = 0
            else:
                col += 1

    def setupCanvas(self):
        self.scene = QtWidgets.QGraphicsScene(0, 0, canvas_X_MAX - 5, canvas_Y_MAX)
        self.scene.addItem(QtWidgets.QGraphicsRectItem(0, 0, 936, canvas_Y_MAX))
        self.view = DnDGraphicView(self.scene)
        # self.view.centerOn(QPointF(-50, -50))
        self.mainLayout.addWidget(self.view)

    def setupRightWidget(self):
        layout_V_1 = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addLayout(layout_V_1)

        # 绘制属性面板
        self.tabWidget = QtWidgets.QTableWidget(0, 2, self)
        self.tabWidget.verticalHeader().hide()  # 隐藏垂直表头
        self.tabWidget.setHorizontalHeaderLabels(['属性', '值'])
        self.tabWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tabWidget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        layout_V_1.addWidget(self.tabWidget, stretch=1)

        # 绘制button面板
        layout_H_1 = QtWidgets.QHBoxLayout()
        layout_V_1.addLayout(layout_H_1, stretch=2)
        layout_V_2 = QtWidgets.QVBoxLayout()
        layout_V_3 = QtWidgets.QVBoxLayout()
        layout_H_1.addLayout(layout_V_2)
        layout_H_1.addLayout(layout_V_3)

        button_start = QtWidgets.QPushButton('启动绘图', self)
        button_clear_buff = QtWidgets.QPushButton('Z轴设置', self)
        button_draws = QtWidgets.QPushButton('删除选中', self)
        button_clear_scene = QtWidgets.QPushButton('清空画布', self)
        # button_start.setStyleSheet()
        layout_V_2.addWidget(button_draws)
        layout_V_2.addWidget(button_clear_buff)
        layout_V_3.addWidget(button_clear_scene)
        layout_V_3.addWidget(button_start)

        # button_start.setStyleSheet("QPushButton{font: 25 14pt '微软雅黑 Light';color: rgb(255,255,255);background-color: rgb(20,196,188);"
        #                         "border: none;border-radius:15px;}"
        #                         "QPushButton:hover{background-color: rgb(22,218,208);}"
        #                         "QPushButton:pressed{background-color: rgb(17,171,164);}")
        button_draws.clicked.connect(self.delItem)
        button_clear_buff.clicked.connect(self.clear_buff)
        button_clear_scene.clicked.connect(self.delAllItems)
        button_start.clicked.connect(self.start)

    def setPropTable(self, props):
        table = self.tabWidget

        # 先解除 单元格改动信号处理函数
        try:
            table.cellChanged.disconnect(self.itemPropChanged)
        except:
            pass

        table.setRowCount(0)  # 删除原来的内容

        for i, item_name in enumerate(props.keys()):
            table.insertRow(i)
            item = QtWidgets.QTableWidgetItem(item_name)
            item.setFlags(Qt.ItemIsEnabled)
            table.setItem(i, 0, item)
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(props[item_name]))

        # 再指定单元格改动信号处理函数
        table.cellChanged.connect(self.itemPropChanged)

    def itemPropChanged(self, row, column):
        # 获取更改内容
        cfgName = self.tabWidget.item(row, 0).text()  # 首列为配置名称
        cfgValue = self.tabWidget.item(row, column).text()

        items = self.scene.selectedItems()
        if len(items) != 1:
            print('item未选中状态, 或选中不止一个')
            return

        selected = items[0]
        selected.itemPropChanged(cfgName, cfgValue)

    def set2DCoordinates(self, x, y):
        table = self.tabWidget

        # 先解除 单元格改动信号处理函数
        try:
            table.cellChanged.disconnect(self.itemPropChanged)
        except:
            pass

        table.setItem(0, 1, QtWidgets.QTableWidgetItem(f'{x}，{y}'))

        # 再指定单元格改动信号处理函数
        table.cellChanged.connect(self.itemPropChanged)


# 加载QSS文件的函数
def load_qss(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


# from connector import startCommunicationThread
# startCommunicationThread()
if __name__ == '__main__':
    start_server_thread()

    app = QtWidgets.QApplication(sys.argv)
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)
    window = MWindow()

    # 第一种设置主题方法，通过 qss 文件
    # window.setStyleSheet(load_qss(qss_file))

    # 第二种设置主题方法，通过 apply_stylesheet
    # apply_stylesheet(app, theme='dark_cyan.xml')

    # 第三种设置主题方法，通过 qdarkstyle
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
    pa = qdarkstyle.palette.Palette
    pa.ID = 'dark'  # 调色板，可选 'dark', 'light'
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6', palette=pa))

    window.scene.setBackgroundBrush(QColor(255, 255, 255))  # 设置画布背景色为白色
    window.show()
    window.setWindowIcon(QtGui.QPixmap('./images/logo.png'))
    window.setWindowTitle('绘图窗口')
    # window.view.centerOn(QPointF(-50, -50))
    app.exec()