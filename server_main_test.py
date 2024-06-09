from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QTransform, QAction, QIcon
from PySide6.QtWidgets import QWidget, QSizePolicy, QProgressBar, QProgressDialog
import qtawesome as qta
import json

from connector_server_test import start_server_thread
from share import ShareInfo, Gstore

X_MAX = 800
Y_MAX = 600
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


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(310, 80)
        # 载入进度条控件
        self.pgb = QProgressBar(self)
        self.setWindowTitle("绘制进行中...")
        self.pgb.move(30, 30)
        self.pgb.resize(250, 20)
        self.pgb.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 5px; color: rgb(20,20,20);  background-color: "
            "#FFFFFF; text-align: center;}QProgressBar::chunk {background-color: rgb(100,200,200); border-radius: "
            "10px; margin: 0.1px;  width: 1px;}")
        # 其中 width 是设置进度条每一步的宽度
        # margin 设置两步之间的间隔

        # 设置进度条的范围
        self.pgb.setMinimum(0)
        self.pgb.setMaximum(100)
        self.pgb.setValue(0)
        # 设置进度条文字格式
        self.pgb.setFormat('Finished  %p%'.format(self.pgb.value() - self.pgb.minimum()))


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
            # p_x, p_y = map(float, (self.props['空间坐标'].split('， ')))
            #
            # self.setPos(p_x, p_y)
            # qrf = self.rect()
            # print('set', cfgValue)
            # qrf.setWidth(float(cfgValue))
            # print('changed', qrf.width())
            # self.setRect(qrf)  # 重新设定

        elif cfgName == '棱形高度':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            self.setRect(qrf)  # 重新设定

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
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
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
            x = float(x)
            # y = Y_MAX - float(y)
            y = float(y)
            print("set", x, y)

            # 更新矩形的位置，但保留原来的宽度和高度
            self.setPos(x, y)
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
            self.setRect(qrf)  # 重新设定

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


class EllipseItem(Item, QtWidgets.QGraphicsEllipseItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.props = {
            '空间坐标': str(self.pos().x()) + '，' + str(self.pos().y()),
            '椭圆宽度': '100',
            '椭圆高度': '100',
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
        qrf.setWidth(float(props["椭圆宽度"]))
        qrf.setHeight(float(props["椭圆高度"]))
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
            y = float(y)
            print("set", x, y)
            self.setPos(x, y)

        elif cfgName == '椭圆宽度':
            qrf = self.rect()
            qrf.setWidth(float(cfgValue))
            self.setRect(qrf)  # 重新设定

        elif cfgName == '椭圆高度':
            qrf = self.rect()
            qrf.setHeight(float(cfgValue))
            self.setRect(qrf)  # 重新设定

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
            # y = Y_MAX - float(y)
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
        shape.props['空间坐标'] = str(shape.pos().x()) + '，' + str(shape.pos().y())
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
        self.resize(1200, 800)

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
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        action = QAction("启动")
        toolbar.insertAction(None, action)
        # actionDraws = toolbar.insertAction(toolbar.actions()[-1], action)
        # actionDraws.triggered.connect(self.draws)
        action.triggered.connect(self.start)

    def load(self):
        with open('cfg.json', 'r', encoding='utf8') as f:
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
        with open('cfg.json', 'w', encoding='utf8') as f:
            f.write(content)

    def get_pos(self):
        for item in self.scene.selectedItems():
            print('pos: %.2f %.2f' % (item.pos().x(), item.pos().y()))
            for point in item.polygon():
                print(point)
            print('')

    def delItem(self):
        import shiboken6
        items = self.scene.selectedItems()
        for item in items:
            # self.scene.removeItem(item)
            shiboken6.delete(item)

    def delAllItems(self):
        self.scene.clear()

    def start(self):
        print('start')
        draws_type = [RectItem, EllipseItem]
        for item in self.scene.items():
            if item.__class__ in draws_type:
                ShareInfo.gstore.item_list.append(item)
        ShareInfo.gstore.item_list.reverse()

        ShareInfo.gstore.update_msg()

        elapsed = 100
        self.dlg = QProgressDialog('进度', '取消', 0, elapsed, self)
        self.dlg.setWindowTitle('等待......')
        self.dlg.setWindowModality(Qt.WindowModal)
        self.dlg.setAutoClose(False)
        self.bar = ProgressBar()
        self.dlg.setBar(self.bar.pgb)
        self.dlg.show()
        self.dlg.setValue(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # 每100毫秒更新一次

    def updateProgress(self):
        if Gstore.pv != self.dlg.value():
            self.dlg.setValue(Gstore.pv)

        if Gstore.pv == 100:
            self.timer.stop()
            Gstore.pv = 0
            self.dlg.setValue(Gstore.pv)
            self.dlg.close()

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
        self.scene = QtWidgets.QGraphicsScene(-50, -50, X_MAX, Y_MAX)  # 大小为 800 X 600 像素
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


# from connector import startCommunicationThread
# startCommunicationThread()
if __name__ == '__main__':
    start_server_thread()

    app = QtWidgets.QApplication()
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)

    window = MWindow()
    window.show()
    # window.view.centerOn(QPointF(-50, -50))
    app.exec()
