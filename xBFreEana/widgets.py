try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *


import sys


class VerticalButton(QToolButton):
    def __init__(self, parent=None, orientation=Qt.ToolBarArea.LeftToolBarArea):
        super(VerticalButton, self).__init__(parent)
        self.orientation = orientation

    def sizeHint(self):
        sh = QToolButton.sizeHint(self)
        sh.transpose()
        return sh

    def paintEvent(self, event: QPaintEvent):
        painter = QStylePainter(self)
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        if self.orientation == Qt.ToolBarArea.RightToolBarArea:
            painter.rotate(90)
            painter.translate(0, -1 * self.width())
        else:
            painter.rotate(-90)
            painter.translate(-1 * self.height(), 0)
        option.rect = option.rect.transposed()
        painter.drawComplexControl(QStyle.ComplexControl.CC_ToolButton, option)


class SideBar(QToolBar):
    def __init__(self, parent=None, area=Qt.ToolBarArea.LeftToolBarArea, movable: bool =False):
        super(SideBar, self).__init__(parent)
        self.setMovable(movable)
        self.area = area
        self.button_list = []
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.topLevelChanged.connect(self.on_topLevelChanged)

    def on_topLevelChanged(self, tl):
        self.area = self.parent().toolBarArea(self)
        for w in self.button_list:
            w.orientation = self.area

    def addButton(self, text, icon: QIcon = None, icon_size: QSize = None, checkable: bool = True,
                  checked: bool = False, button_style: Qt.ToolButtonStyle = Qt.ToolButtonStyle.ToolButtonFollowStyle,
                  tooltip: str =
                  None):
        button = VerticalButton(self, self.area)
        button.setText(text)
        if icon:
            button.setIcon(icon)
        if icon_size:
            button.setIconSize(icon_size)
        button.setCheckable(checkable)
        button.setChecked(checked)
        button.setToolButtonStyle(button_style)
        button.setToolTip(tooltip)

        self.addWidget(button)
        self.button_list.append(button)
        return button

    def addSpacer(self):
        s = QWidget()
        s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addWidget(s)
        return s



class My(QMainWindow):
    def __init__(self):
        super(My, self).__init__()
        print(type(self))
        sb = SideBar(self, Qt.ToolBarArea.RightToolBarArea)

        b1 = sb.addButton('Test', button_style=Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        s = sb.addSpacer()
        b2 = sb.addButton('Test2', button_style=Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, sb)
        w = QWidget()
        l = QHBoxLayout(w)
        # l.setContentsMargins(25, 25, 25, 25)
        self.setCentralWidget(w)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = My()
    w.show()
    sys.exit(app.exec())
