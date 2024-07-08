from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QTransform, QAction, QIcon
from PySide6.QtWidgets import QWidget, QSizePolicy, QProgressBar, QProgressDialog, QVBoxLayout, QLabel, QDialog
from qt_material import apply_stylesheet
# import qtawesome as qta
import qdarkstyle
import json
import sys

from connector_server_test import start_server_thread
from share import ShareInfo, Gstore

canvas_X_MAX = 958
canvas_Y_MAX = 600
# X_MAX = 210， Y_MAX = 150，机械臂活动范围
shape_draw = ["rectangle", "ellipse", "diamond", "line", "text"]
tableStyle = '''
QTableWidget {
    gridline-color: #e0e0e0;
}

QHeaderView::section {     
    background-color: #f8f8f8;
    border-top: 0px solid #e0e0e0;
    border-left: 0px solid #e0e0e0;
    border-right: 1px solid #e0e0e0;
    border-bottom: 1px solid #e0e0e0;
'''


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
        # self.setLayout(layout)


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

        if change == QtWidgets.QGraphicsItem.ItemPositionChange and value == True:
            # 更新属性表中的坐标值
            self.props['空间坐标'] = f"{value.x()}，{value.y()}"
            print(value.x(), value.y())
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

        self.props = {
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
            # 'length': '10',
            '棱形宽度': '100',
            '棱形高度': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '1',
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
        qrf.setWidth(float(props["棱形宽度"]))
        qrf.setHeight(float(props["棱形高度"]))
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
            x, y = cfgValue.split('，')
            x = float(x)
            y = float(y)
            print("set", x, y)

            # 更新矩形的位置，但保留原来的宽度和高度
            self.setPos(x, y)
            print("changed", self.pos().x(), self.pos().y())

        elif cfgName == '棱形宽度':
            q_ls = [QPointF(self.pos().x(), self.pos().y())]
            width = float(cfgValue)
            height = float(self.props['棱形高度'])
            q_ls.append(QPointF(self.pos().x() + width / 2, self.pos().y() + height / 2))
            q_ls.append(QPointF(self.pos().x(), self.pos().y() + height))
            q_ls.append(QPointF(self.pos().x() - width / 2, self.pos().y() + height / 2))
            self.setPolygon(q_ls)
            self.setPos(int(self.props['空间坐标'].split('，')[0]), int(self.props['空间坐标'].split('，')[1]))
            # p_x, p_y = map(float, (self.props['空间坐标'].split('， ')))
            #
            # self.setPos(p_x, p_y)
            # qrf = self.rect()
            # print('set', cfgValue)
            # qrf.setWidth(float(cfgValue))
            # print('changed', qrf.width())
            # self.setRect(qrf)  # 重新设定

        elif cfgName == '棱形高度':
            x, y = self.props['空间坐标'].split('，')
            x = float(x)
            y = float(y)
            q_ls = [QPointF(x, y)]
            height = float(cfgValue)
            width = float(self.props['棱形宽度'])
            q_ls.append(QPointF(x + width / 2, y + height / 2))
            q_ls.append(QPointF(x, y + height))
            q_ls.append(QPointF(x - width / 2, y + height / 2))
            self.setPolygon(q_ls)
            self.setPos(x, y)

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


class RectItem(Item, QtWidgets.QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '空间坐标': '0，0',
            '矩形宽度': '100',
            '矩形高度': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '1',
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


class EllipseItem(Item, QtWidgets.QGraphicsEllipseItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '空间坐标': '0，0',
            '圆形直径': '100',
            '填充颜色': '222, 241, 255, 0',
            '线条宽度': '1',
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

        elif cfgName == '圆形半径':
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
        self.setPos(x, y)
        self.setZValue(float(props["zValue"]))

        # 其他设置
        line = self.line()
        line.setLine(x, y, x + float(props["线长"]), y)
        line.setAngle(float(props["旋转角度"]))
        # print("线条",line)
        self.setLine(line)

        pen = self.pen()
        pen.setWidth(int(props["线宽"]))
        pen.setColor(QtGui.QColor(*[int(v) for v in props["颜色"].replace(' ', '').split(',')]))
        self.setPen(pen)

    def itemPropChanged(self, cfgName, cfgValue: str):
        self.props[cfgName] = cfgValue

        if cfgName == '空间坐标':
            # print(cfgValue)
            # qrf = self.pen()
            x, y = cfgValue.split('，')
            x = float(x)
            y = canvas_Y_MAX - float(y)
            y = float(y)
            self.setPos(x, y)

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

        if picName == "rectangle":
            shape = RectItem(0, 0, 100, 100)
        elif picName == "ellipse":
            shape = EllipseItem(0, 0, 100, 100)
        elif picName == "line":
            shape = LineItem(0, 0, 100, 0)
            pen = shape.pen()
            pen.setWidth(3)
            shape.setPen(pen)
        elif picName == "text":
            shape = TextItem("文本内容")
        elif picName == "diamond":
            shape = DiamondItem([QPointF(0, 0), QPointF(50, 50), QPointF(0, 100), QPointF(-50, 50)])
            # shape.props['length'] = str(shape.polygon().length())

        shape.setPos(e.position())
        print(shape.pos().y() , self.rect().height())
        y = shape.pos().y()
        if picName == "rectangle" or picName == "ellipse":
            y = canvas_Y_MAX - shape.pos().y() - shape.rect().height()
        elif picName == "line":
            y = canvas_Y_MAX - shape.pos().y()
        shape.props['空间坐标'] = str(shape.pos().x()) + '，' + str(y)
        # print(shape.pos())
        self.scene().addItem(shape)

        # 设置item可以移动
        # shape.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
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
        self.resize(1400, 900 - 240)

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

        self.setupToolBar()
        # self.view.centerOn(50, -50)

        # self.setCanvasTransform()

    def setCanvasTransform(self):
        # 翻转Y轴，使其向上为正方向
        transform = QTransform()
        transform.scale(1, -1)  # 纵向翻转
        self.view.setTransform(transform)

    def setupToolBar(self):

        # 创建 工具栏 对象 并添加
        toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(toolbar)

        # 添加 工具栏 条目Action
        actionSave = toolbar.addAction("保存")  # qta.icon("ph.download-light",color='green'),
        actionSave.triggered.connect(self.save)

        actionLoad = toolbar.addAction("加载")
        actionLoad.triggered.connect(self.load)

        actionDelItem = toolbar.addAction("删除")
        actionDelItem.triggered.connect(self.delItem)

        actionDelAllItem = toolbar.addAction("清空")
        actionDelAllItem.triggered.connect(self.delAllItems)

        actionGetPosItem = toolbar.addAction("输出")
        actionGetPosItem.triggered.connect(self.get_pos)

        # 添加右侧的伸缩空间，将后续的 Action 推到最右边
        # spacer = QWidget()
        # spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # toolbar.addWidget(spacer)

        # action = QAction("启动")
        # toolbar.insertAction(None, action)
        # actionDraws = toolbar.insertAction(toolbar.actions()[-1], action)
        # actionDraws.triggered.connect(self.draws)
        # action.triggered.connect(self.start)
        # print(toolbar.height())

    def load(self):
        with open('data/cfg.json', 'r', encoding='utf8') as f:
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
            # item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            # 设置item可以选中
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            # 设置item可以聚焦，这样才会有键盘按键回调keyPressEvent
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

    def save(self):
        itemSaveDataList = []
        for item in self.scene.items():
            if hasattr(item, 'toSaveData'):
                # print(item.pos().x(), item.pos().y())
                saveData = item.toSaveData()
                itemSaveDataList.append(saveData)

        # print(itemSaveDataList)

        content = json.dumps(itemSaveDataList, indent=4, ensure_ascii=False)
        with open('data/cfg.json', 'w', encoding='utf8') as f:
            f.write(content)

    def get_pos(self):
        for item in self.scene.selectedItems():
            # print('pos: %.2f %.2f' % (item.pos().x(), item.pos().y()))
            if item.__class__.__name__ == "DiamondItem":
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
            else:
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
                for i in range(len(x_ls)):
                    print('%.2f %.2f' % (x_ls[i], y_ls[i]))
            print('')

    def delItem(self):
        import shiboken6
        items = self.scene.selectedItems()
        for item in items:
            # self.scene.removeItem(item)
            shiboken6.delete(item)

    def delAllItems(self):
        self.scene.clear()
        self.scene.addItem(QtWidgets.QGraphicsRectItem(0, 0, 936, canvas_Y_MAX))

    def start(self):
        print('start')
        ShareInfo.gstore.msg_dialog = ''
        draws_type = [RectItem, EllipseItem, LineItem]
        for item in self.scene.items():
            if item.__class__ in draws_type:
                ShareInfo.gstore.item_list.append(item)
        ShareInfo.gstore.item_list.reverse()

        ShareInfo.gstore.update_msg()

        self.pgb = ProgressBar()
        self.pgb.exec()
        # self.pgb.show()
        # self.pgb.setFocus()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # 每100毫秒更新一次

    def updateProgress(self):
        if ShareInfo.gstore.msg_dialog == 'stop':
            self.timer.stop()
            self.pgb.close()

    def clear_buff(self):
        print('clear buffer')
        ShareInfo.gstore.clear_buff()

    def setupLeftPane(self):
        leftLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(leftLayout)

        pixmapLayout = QtWidgets.QGridLayout()
        leftLayout.addLayout(pixmapLayout)
        leftLayout.addStretch()

        row, col = 0, 0

        for shape in shape_draw:

            pixmap = QtGui.QPixmap(f'./images/{shape}.png')
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
        self.scene = QtWidgets.QGraphicsScene(0, 0, canvas_X_MAX, canvas_Y_MAX)  # 大小为 800 X 600 像素
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
        self.tabWidget.setStyleSheet(tableStyle)
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
        button_clear_buff = QtWidgets.QPushButton('清空缓冲', self)
        button_draws = QtWidgets.QPushButton('绘制', self)
        button_clear_scene = QtWidgets.QPushButton('清除画布', self)

        layout_V_2.addWidget(button_draws)
        layout_V_2.addWidget(button_clear_buff)
        layout_V_3.addWidget(button_clear_scene)
        layout_V_3.addWidget(button_start)

        # button_start.setStyleSheet("QPushButton{font: 25 14pt '微软雅黑 Light';color: rgb(255,255,255);background-color: rgb(20,196,188);"
        #                         "border: none;border-radius:15px;}"
        #                         "QPushButton:hover{background-color: rgb(22,218,208);}"
        #                         "QPushButton:pressed{background-color: rgb(17,171,164);}")
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
    # qss_file = './QSS-master/lightstyle.qss'
    # window.setStyleSheet(load_qss(qss_file))

    # 第二种设置主题方法，通过 apply_stylesheet
    # apply_stylesheet(app, theme='dark_blue.xml')

    # 第三种设置主题方法，通过 qdarkstyle
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
    pa = qdarkstyle.palette.Palette
    pa.ID = 'dark'  # 调色板，可选 'dark', 'light'
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6', palette=pa))

    window.show()
    window.setWindowTitle('绘图窗口')
    # window.view.centerOn(QPointF(-50, -50))
    app.exec()
