# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_filter.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(491, 206)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(140, 170, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayoutWidget = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 471, 151))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.cb_post = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.cb_post.setObjectName("cb_post")
        self.cb_post.addItem("")
        self.cb_post.addItem("")
        self.gridLayout.addWidget(self.cb_post, 0, 1, 1, 1)
        self.cb_follower = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.cb_follower.setObjectName("cb_follower")
        self.cb_follower.addItem("")
        self.cb_follower.addItem("")
        self.gridLayout.addWidget(self.cb_follower, 2, 1, 1, 1)
        self.cb_following = QtWidgets.QComboBox(self.gridLayoutWidget)
        self.cb_following.setObjectName("cb_following")
        self.cb_following.addItem("")
        self.cb_following.addItem("")
        self.gridLayout.addWidget(self.cb_following, 1, 1, 1, 1)
        self.e_post = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.e_post.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.e_post.setObjectName("e_post")
        self.gridLayout.addWidget(self.e_post, 0, 2, 1, 1)
        self.e_following = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.e_following.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.e_following.setObjectName("e_following")
        self.gridLayout.addWidget(self.e_following, 1, 2, 1, 1)
        self.e_follower = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.e_follower.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.e_follower.setObjectName("e_follower")
        self.gridLayout.addWidget(self.e_follower, 2, 2, 1, 1)
        self.e_info = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.e_info.setObjectName("e_info")
        self.gridLayout.addWidget(self.e_info, 3, 2, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Постов"))
        self.label_3.setText(_translate("Dialog", "Подписчиков"))
        self.label_2.setText(_translate("Dialog", "Подписок"))
        self.label_4.setText(_translate("Dialog", "Информация содержит текст"))
        self.cb_post.setItemText(0, _translate("Dialog", ">"))
        self.cb_post.setItemText(1, _translate("Dialog", "<"))
        self.cb_follower.setItemText(0, _translate("Dialog", ">"))
        self.cb_follower.setItemText(1, _translate("Dialog", "<"))
        self.cb_following.setItemText(0, _translate("Dialog", ">"))
        self.cb_following.setItemText(1, _translate("Dialog", "<"))

