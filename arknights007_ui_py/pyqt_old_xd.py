#!/usr/bin/python

"""
ZetCode PyQt6 tutorial

This example draws three rectangles in three
different colours.

Author: Jan Bodnar
Website: zetcode.com
"""
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
import sys


class State_Form(QWidget):

    def __init__(self):
        super().__init__()

        self.init_Form()

    def init_Form(self):
        self.resize(800, 600)
        self.window_move_to_center()
        self.setWindowTitle('Arknights007')
        self.draw_labels()

        self.show()

    def window_move_to_center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.drawBackgroundRectanglesBoard(e, qp)
        qp.end()

    def draw_labels(self):
        label_title = QLabel(self)
        label_title.setStyleSheet("QLabel { color : #DBDBDB ; }")
        label_title.setText('状态')
        label_title.setGeometry(QRect(33, 10, 33 + 80, 19 + 53))
        font = QFont('Source Han Sans', 35, QFont.Weight.Light)

        font.setPixelSize(40)
        label_title.setFont(font)

    def drawBackgroundRectanglesBoard(self, event, qp):
        qp.setPen(QPen(QColor('#707070'), 2, Qt.PenStyle.SolidLine))

        qp.setBrush(QColor('#597370'))
        qp.drawRect(0, 0, 545, 396)

        qp.setBrush(QColor('#556361'))
        qp.drawRect(545, 0, 255, 396)

        qp.setBrush(QColor('#343434'))
        qp.drawRect(0, 396, 800, 204)

        qp.setPen(QPen(QColor('#929f9e'), 2, Qt.PenStyle.SolidLine))
        qp.drawLine(23, 78, 523, 78)

        qp.setPen(QPen(QColor('#6d8482'), 2, Qt.PenStyle.SolidLine))
        qp.drawLine(273, 105, 273, 105 + 267)
        qp.drawLine(295, 139, 295 + 228, 139)
        qp.drawLine(33, 239, 33 + 205, 239)
        qp.drawLine(413, 198, 104 + 413, 198)

        qp.setPen(QPen(QColor('#2F53E1'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#2F53E1'))
        qp.drawRect(25, 106, 5, 27)

        qp.setPen(QPen(QColor('#50AACC'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#50AACC'))
        qp.drawRect(25, 148, 5, 27)

        qp.setPen(QPen(QColor('#F5B556'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#F5B556'))
        qp.drawRect(25, 190, 5, 27)

        qp.setPen(QPen(QColor('#FF9800'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#FF9800'))
        qp.drawRect(25, 257, 5, 27)

        qp.setPen(QPen(QColor('#D45A5A'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#D45A5A'))
        qp.drawRect(25, 299, 5, 27)

        qp.setPen(QPen(QColor('#8E8E8E'), 0, Qt.PenStyle.NoPen))
        qp.setBrush(QColor('#8E8E8E'))
        qp.drawRect(25, 341, 5, 27)


def main():
    app = QApplication(sys.argv)
    ex = State_Form()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
