import socket
import select
import sys
import os
from threading import Thread
from PyQt5 import QtCore, QtGui, QtWidgets

class Client(QtWidgets.QWidget):
	def __init__(self, host, port, nickname, parent = None):
		super(Client, self).__init__(parent)

		layout = QtWidgets.QHBoxLayout()
		self.choose = Choose(self)
		self.chat = Chat(self)
		self.randomRole = RandomRole(self)
		self.gameSeat = GameSeat(self)
		self.truth = Truth(self)
		layout.addWidget(self.choose)
		layout.addWidget(self.randomRole)
		layout.addWidget(self.gameSeat)
		layout.addWidget(self.truth)
		layout.addWidget(self.chat)
		self.choose.hide()
		self.randomRole.hide()
		self.gameSeat.hide()
		self.truth.hide()

		self.chat.quit.clicked.connect(self.close)

		#視窗設定
		#視窗初始大小
		#widget.resize(500, 400)
		#視窗初始位置
		self.move(200, 200)
		self.showMaximized()
		#視窗標題
		vision = '1.0'
		self.setWindowTitle("Avalon 阿瓦隆 V" + vision + " - " + nickname)
		self.setWindowIcon(QtGui.QIcon("images/Avalon2.png"))
		#視窗排版
		self.setLayout(layout)

		#預設焦點
		self.chat.le.setFocus()

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((host, port))
		self.input = self.socket.makefile('rb', 0)
		self.output = self.socket.makefile('wb', 0)

		#傳送暱稱給服務器
		authenticationDemand = self.input.readline().decode('utf-8')
		if not authenticationDemand.startswith("Who are you?"):
			raise Exception ("This doesn't seem to be a Python Chat Server.")
		self.output.write((nickname + '\r\n').encode('utf-8'))

		#藉由印出成員名單開始
		self.output.write(('/names\r\n').encode('utf-8'))
		string = self.input.readline().decode('utf-8').strip()
		self.again = False
		self.person = len(string.split("  "))
		if self.person == 1:
			self.game_host = True
			self.choose.init()
			self.choose.show()
		else:
			self.game_host = False
			self.choose.init()
		self.join_quit(string)
		
		out = Output(self.input)
		out.start()

	def alert(self, string1, string2):
		#字體大小
		f = QtGui.QFont()
		f.setPointSize(14)
		#訊息窗 & 標題
		alert = QtWidgets.QDialog()
		alert.setWindowTitle(string1)
		#訊息
		label = QtWidgets.QLabel("  " + string2 + "  ")
		label.setFont(f)
		#按鈕
		button = QtWidgets.QPushButton("我知道了啦")
		#水平排版
		hl = QtWidgets.QHBoxLayout()
		hl.addStretch(1)
		hl.addWidget(button)
		hl.addStretch(1)
		#垂直排版
		vl = QtWidgets.QVBoxLayout()
		vl.addWidget(label)
		vl.addStretch(1)
		vl.addLayout(hl)
		alert.setLayout(vl)
		#按鈕事件
		button.clicked.connect(alert.accept)
		#運行
		alert.exec_()

	def join_quit(self, string):
		self.chat.label2.setText(str(self.person))
		self.chat.label3.setText(string)

		good_num = 0
		bad_num = 0
		#9, 10
		if (self.person > 8):
			good_num = 6
		#8
		elif (self.person > 7):
			good_num = 5
		#6, 7
		elif (self.person > 5):
			good_num = 4
		#5
		elif (self.person > 4):
			good_num = 3
		#10
		if (self.person > 9):
			bad_num = 4
		#7, 8, 9
		elif (self.person > 6):
			bad_num = 3
		#5, 6
		elif (self.person > 4):
			bad_num = 2
		self.choose.label2.setText(str(good_num))
		self.choose.label6.setText(str(bad_num))


class Output(Thread):

	def __init__(self, input):
		Thread.__init__(self)
		self.setDaemon(True)
		self.input = input

	#開始一個分開的執行緒去聚集鍵盤輸入當我們在等待網路傳來的訊息時，這使得使用者同時收發變為可行
	def run(self):

		#從網路讀取然後印出接收到的所有東西到標準輸出，一旦資料停止從網路進來，則它代表失聯了
		inputText = True
		while inputText:
			inputText = self.input.readline().decode('utf-8')
			if inputText:
				if inputText[0] == '/':
					if inputText[1] == 'j':
						window.person = window.person + 1
					elif inputText[1] == 'q':
						window.person = window.person - 1
					if inputText[1] == 'j' or inputText[1] == 'q':
						window.join_quit(inputText[2:].strip())
					if inputText[1:8] == 'prepare':
						goods = self.input.readline().decode('utf-8').strip().split(' ')
						bads = self.input.readline().decode('utf-8').strip().split(' ')
						for good in goods:
							window.choose.good_choosen.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/" + good + ".jpg"), good))
						for bad in bads:
							window.choose.bad_choosen.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/" + bad + ".jpg"), bad))
						window.choose.showed.emit()
					if inputText[1:5] == 'role':
						window.gameSeat.role = inputText[6:-2]
						window.randomRole.l1.setText("你是 " + window.gameSeat.role)
						window.randomRole.l2.setPixmap(QtGui.QPixmap("images/" + window.gameSeat.role + ".jpg"))
						window.randomRole.l3.setText(self.input.readline().decode('utf-8').strip())
						window.gameSeat.see = self.input.readline().decode('utf-8').strip()
						window.randomRole.l4.setText(window.gameSeat.see)
						window.randomRole.showed.emit()
						window.choose.hided.emit()
					if inputText[1:5] == 'seat':
						window.randomRole.hided.emit()
						window.gameSeat.inited.emit(inputText[6:-2])
						window.gameSeat.showed.emit()
					if inputText[1:7] == 'assign':
						window.gameSeat.l29.setText('亞瑟王正在選騎士')
					if inputText[1:7] == 'assig2':
						window.gameSeat.assigned.emit()
					if inputText[1:5] == 'vote':
						window.gameSeat.knights = inputText[6:-2].split(', ')
						window.gameSeat.l14.setText(inputText[6:-2])
						window.gameSeat.voted.emit()
						window.gameSeat.l29.setText('請等候所有玩家投完票')
					if inputText[1:8] == 'mission':
						if inputText[-2] == 'y':
							if nickname in window.gameSeat.knights:
								window.gameSeat.missioned.emit()
						else:
							window.gameSeat.vote_num += 1
							window.gameSeat.l25.setText(str(window.gameSeat.vote_num))
					#if inputText[1:6] == 'alert':
					#	window.gameSeat.alerted.emit(self.input.readline().decode('utf-8').strip(), self.input.readline().decode('utf-8').strip())
					if inputText[1:9] == 'gameover':
						window.gameSeat.hided.emit()
						window.truth.showed.emit()
						window.truth.inited.emit(self.input.readline().decode('utf-8').strip())
						if inputText[10] == 'g':
							window.gameSeat.alerted.emit('好人獲勝', '好人獲勝！')
						else:
							window.gameSeat.alerted.emit('壞人獲勝', '壞人獲勝！')
					if inputText[1:9] == 'assassin':
						if (window.gameSeat.role == '刺客'):
							window.gameSeat.assassinated.emit()
						else:
							window.gameSeat.l29.setText('請等待刺客刺殺')
					if inputText[1:3] == 'gw':
						window.gameSeat.gw += 1
						window.gameSeat.l21.setText(str(window.gameSeat.gw))
						window.gameSeat.l19.setText(str(window.gameSeat.gw + window.gameSeat.bw + 1))
					if inputText[1:3] == 'bw':
						window.gameSeat.bw += 1
						window.gameSeat.l23.setText(str(window.gameSeat.bw))
						window.gameSeat.l19.setText(str(window.gameSeat.gw + window.gameSeat.bw + 1))
					if inputText[1:5] == 'acer':
						window.gameSeat.acered.emit()
					if inputText[1:7] == 'rerole':
						window.truth.hided.emit()
						window.again = True
						window.choose.inited.emit()
						if window.game_host:
							window.choose.showed.emit()
				else:
					if inputText[0] == '<':
						window.chat.chat.append(inputText.strip())
					else:
						window.chat.chat.append('<div style="color:red">' + inputText.strip() + '</div>')
					window.chat.chat.verticalScrollBar().setValue(window.chat.chat.verticalScrollBar().maximum())

class Chat(QtWidgets.QWidget):
	def __init__(self, client, parent = None):
		super(Chat, self).__init__(parent)

		self.client = client

		self.label1 = QtWidgets.QLabel('<在線玩家>')

		self.label2 = QtWidgets.QLabel()
		
		self.label3 = QtWidgets.QLabel()
		
		self.chat = QtWidgets.QTextBrowser()
		self.chat.setStyleSheet("color: blue;")
		self.chat.setFont(QtGui.QFont( "Timers" , 10 ,  QtGui.QFont.Normal))
		
		self.label4 = QtWidgets.QLabel('<' + nickname + '>')
		
		#輸入框
		self.le = QtWidgets.QLineEdit()
		
		#按鈕 * 2
		self.send = QtWidgets.QPushButton("發送 &send (Alt + &s)")
		self.clear = QtWidgets.QPushButton("清空 &clear (Alt + &c)")
		
		#音樂條
		#self.bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		#self.bar.setRange(0, 100)
		
		#音樂格
		#self.sb = QtWidgets.QSpinBox()
		#self.sb.setSuffix("%")
		#self.sb.setRange(0, 100)

		self.quit = QtWidgets.QPushButton("離開 &quit (Alt + &q)")

		#事件
		self.le.returnPressed.connect(self.say)
		self.send.clicked.connect(self.say)
		self.clear.clicked.connect(self.le.clear)
		#self.sb.valueChanged.connect(self.bar.setValue)
		#self.bar.valueChanged.connect(self.sb.setValue)

		#水平排版 (每個皆為一行)
		l1 = QtWidgets.QHBoxLayout()
		l1.addWidget(self.label1)
		l1.addWidget(self.label2)
		l1.addStretch(1)

		l2 = QtWidgets.QHBoxLayout()
		l2.addWidget(self.label3)

		l3 = QtWidgets.QHBoxLayout()
		l3.addWidget(self.chat)

		l4 = QtWidgets.QHBoxLayout()
		l4.addWidget(self.label4)

		l5 = QtWidgets.QHBoxLayout()
		l5.addWidget(self.le)

		l6 = QtWidgets.QHBoxLayout()
		l6.addStretch(1)
		l6.addWidget(self.send)
		l6.addWidget(self.clear)

		#l7 = QtWidgets.QHBoxLayout()
		#l7.addWidget(self.bar)
		#l7.addWidget(self.sb)

		l8 = QtWidgets.QHBoxLayout()
		l8.addStretch(1)
		l8.addWidget(self.quit)

		#垂直排版
		layout = QtWidgets.QVBoxLayout()
		layout.addLayout(l1)
		layout.addLayout(l2)
		layout.addLayout(l3)
		layout.addLayout(l4)
		layout.addLayout(l5)
		layout.addLayout(l6)
		#layout.addLayout(l7)
		layout.addLayout(l8)
	
		self.setLayout(layout)
		
	def say(self, temp = None):
		#當從標準輸入讀入時沒必要去解密
		inputText = self.le.text().strip()
		if inputText:
			window.output.write((inputText + '\r\n').encode('utf-8'))
		self.chat.append('<div style = "color:green">' + self.le.text() + '</div>')
		self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())
		self.le.clear()


class Choose(QtWidgets.QWidget):

	inited = QtCore.pyqtSignal()
	showed = QtCore.pyqtSignal()
	hided = QtCore.pyqtSignal()
		
	def __init__(self, client, parent = None):
		super(Choose, self).__init__(parent)

		self.client = client
		self.inited.connect(self.init)

	@QtCore.pyqtSlot()
	def init(self):
		if self.client.again:
			self.layout().deleteLater()
			QtWidgets.QWidget().setLayout(self.layout())
		self.pf = False
		self.good_choose = QtWidgets.QListWidget()
		self.good_choose.setIconSize(QtCore.QSize(200, 100))
		if self.client.game_host:
			self.good_choose.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/派西維爾.jpg"), "派西維爾"))
		self.bad_choose = QtWidgets.QListWidget()
		self.bad_choose.setIconSize(QtCore.QSize(200, 100))
		if self.client.game_host:
			self.bad_choose.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/莫甘娜.jpg"), "莫甘娜"))
			self.bad_choose.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/莫德雷德.jpg"), "莫德雷德"))
			self.bad_choose.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/奧伯倫.jpg"), "奧伯倫"))
		self.label1 = QtWidgets.QLabel('好人人數')
		self.label2 = QtWidgets.QLabel()
		self.label3 = QtWidgets.QLabel('>>')
		self.add = QtWidgets.QPushButton("新增 &add (Alt + &a)")
		if self.client.game_host:
			self.start = QtWidgets.QPushButton("遊戲開始 game start")
		else:
			self.start = QtWidgets.QPushButton("準備")
		self.remove = QtWidgets.QPushButton("移除 &remove (Alt + &r)")
		self.label4 = QtWidgets.QLabel('<<')
		self.label5 = QtWidgets.QLabel('壞人人數')
		self.label6 = QtWidgets.QLabel()
		self.good_choosen = QtWidgets.QListWidget()
		self.good_choosen.setIconSize(QtCore.QSize(200, 100))
		if self.client.game_host:
			self.good_choosen.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/梅林.jpg"), "梅林"))
		self.bad_choosen = QtWidgets.QListWidget()
		self.bad_choosen.setIconSize(QtCore.QSize(200, 100))
		if self.client.game_host:
			self.bad_choosen.addItem(QtWidgets.QListWidgetItem(QtGui.QIcon("images/刺客.jpg"), "刺客"))

		#事件
		self.add.clicked.connect(self.addList)
		self.remove.clicked.connect(self.removeList)
		self.good_choose.clicked.connect(self.chooseOne1)
		self.bad_choose.clicked.connect(self.chooseOne2)
		self.good_choosen.clicked.connect(self.chooseOne3)
		self.bad_choosen.clicked.connect(self.chooseOne4)
		if self.client.game_host:
			self.start.clicked.connect(self.choosen)
		else:
			self.start.clicked.connect(self.prepare)
		self.showed.connect(self.show)
		self.hided.connect(self.hide)

		#水平排版 (每個皆為一行)
		l1 = QtWidgets.QVBoxLayout()
		if self.client.game_host:
			#未選
			l1.addWidget(self.good_choose)
			l1.addWidget(self.bad_choose)

			l2 = QtWidgets.QVBoxLayout()
			#好人人數
			l21 = QtWidgets.QHBoxLayout()
			l21.addStretch(1)
			l21.addWidget(self.label1)
			l21.addStretch(1)
			l21.addWidget(self.label2)
			l21.addStretch(1)
			l2.addLayout(l21)
			#空白
			l2.addStretch(1)
			#>>
			l22 = QtWidgets.QHBoxLayout()
			l22.addStretch(1)
			l22.addWidget(self.label3)
			l22.addStretch(1)
			l2.addLayout(l22)
			#按鈕
			l2.addWidget(self.add)
			l2.addWidget(self.start)
			l2.addWidget(self.remove)
			#<<
			l23 = QtWidgets.QHBoxLayout()
			l23.addStretch(1)
			l23.addWidget(self.label4)
			l23.addStretch(1)
			l2.addLayout(l23)
			#空白
			l2.addStretch(1)
			#壞人人數
			l24 = QtWidgets.QHBoxLayout()
			l24.addStretch(1)
			l24.addWidget(self.label5)
			l24.addStretch(1)
			l24.addWidget(self.label6)
			l24.addStretch(1)
			l2.addLayout(l24)
			#已選
			l3 = QtWidgets.QVBoxLayout()
			l3.addWidget(self.good_choosen)
			l3.addWidget(self.bad_choosen)
		else:
			#好人人數
			l11 = QtWidgets.QHBoxLayout()
			l11.addStretch(1)
			l11.addWidget(self.label1)
			l11.addStretch(1)
			l11.addWidget(self.label2)
			l11.addStretch(1)
			l1.addLayout(l11)
			#已選
			l1.addWidget(self.good_choosen)
			l1.addWidget(self.start)
			l1.addWidget(self.bad_choosen)
			#壞人人數
			l12 = QtWidgets.QHBoxLayout()
			l12.addStretch(1)
			l12.addWidget(self.label5)
			l12.addStretch(1)
			l12.addWidget(self.label6)
			l12.addStretch(1)
			l1.addLayout(l12)

		#垂直排版
		layout = QtWidgets.QHBoxLayout()
		layout.addLayout(l1)
		if self.client.game_host:
			layout.addLayout(l2)
			layout.addLayout(l3)
	
		self.setLayout(layout)

	def addList(self):
		temp = self.good_choose.selectedItems()
		if temp:
			self.good_choose.takeItem(self.good_choose.row(temp[0]))
			self.good_choosen.addItem(temp[0])
			self.good_choose.setCurrentRow(-1)
			self.good_choosen.setCurrentRow(self.good_choosen.row(temp[0]))
		temp = self.bad_choose.selectedItems()
		if temp:
			self.bad_choose.takeItem(self.bad_choose.row(temp[0]))
			self.bad_choosen.addItem(temp[0])
			self.bad_choose.setCurrentRow(-1)
			self.bad_choosen.setCurrentRow(self.bad_choosen.row(temp[0]))

	def removeList(self):
		temp = self.good_choosen.selectedItems()
		if temp:
			self.good_choosen.takeItem(self.good_choosen.row(temp[0]))
			self.good_choose.addItem(temp[0])
			self.good_choosen.setCurrentRow(-1)
			self.good_choose.setCurrentRow(self.good_choose.row(temp[0]))
		temp = self.bad_choosen.selectedItems()
		if temp:
			self.bad_choosen.takeItem(self.bad_choosen.row(temp[0]))
			self.bad_choose.addItem(temp[0])
			self.bad_choosen.setCurrentRow(-1)
			self.bad_choose.setCurrentRow(self.bad_choose.row(temp[0]))

	def chooseOne1(self):
		self.bad_choose.setCurrentRow(-1)
		self.bad_choosen.setCurrentRow(-1)
		self.good_choosen.setCurrentRow(-1)

	def chooseOne2(self):
		self.good_choose.setCurrentRow(-1)
		self.good_choosen.setCurrentRow(-1)
		self.bad_choosen.setCurrentRow(-1)

	def chooseOne3(self):
		self.bad_choose.setCurrentRow(-1)
		self.bad_choosen.setCurrentRow(-1)
		self.good_choose.setCurrentRow(-1)

	def chooseOne4(self):
		self.good_choose.setCurrentRow(-1)
		self.good_choosen.setCurrentRow(-1)
		self.bad_choose.setCurrentRow(-1)

	def choosen(self):
		good_num = 0
		bad_num = 0
		#9, 10
		if (window.person > 8):
			good_num = 6
		#8
		elif (window.person > 7):
			good_num = 5
		#6, 7
		elif (window.person > 5):
			good_num = 4
		#5
		elif (window.person > 4):
			good_num = 3
		#10
		if (window.person > 9):
			bad_num = 4
		#7, 8, 9
		elif (window.person > 6):
			bad_num = 3
		#5, 6
		elif (window.person > 4):
			bad_num = 2
		if (window.person < 5):
			window.alert("設定錯誤", "目前玩家人數不滿五人")
			return
		elif (window.choose.bad_choosen.count() > bad_num):
			window.alert("設定錯誤", "邪惡方所選角色數目超過邪惡方人數上限")
			return
		self.start.setEnabled(False)
		text = '/roleg'
		for i in range(window.choose.good_choosen.count()):
			text += ' ' + window.choose.good_choosen.item(i).text()
		for i in range(good_num - window.choose.good_choosen.count()):
			text += ' 忠臣'
		text += '\n'
		window.output.write(text.encode('utf-8'))
		text = '/roleb'
		for i in range(window.choose.bad_choosen.count()):
			text += ' ' + window.choose.bad_choosen.item(i).text()
		for i in range(bad_num - window.choose.bad_choosen.count()):
			text += ' 爪牙'
		text += '\n'
		window.output.write(text.encode('utf-8'))

	def prepare(self):
		if self.pf:
			self.start.setText('準備')
			self.pf = False
			self.client.output.write(('/prepare n\n').encode('utf-8'))
		else:
			self.start.setText('取消準備')
			self.pf = True
			self.client.output.write(('/prepare y\n').encode('utf-8'))

class RandomRole(QtWidgets.QWidget):

	showed = QtCore.pyqtSignal()
	hided = QtCore.pyqtSignal()

	def __init__(self, client, parent = None):
		super(RandomRole, self).__init__(parent)

		self.client = client

		self.l1 = QtWidgets.QLabel()
		self.l2 = QtWidgets.QLabel()
		self.l3 = QtWidgets.QLabel()
		self.l4 = QtWidgets.QLabel()

		#垂直排版
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.l1)
		layout.addWidget(self.l2)
		layout.addWidget(self.l3)
		layout.addWidget(self.l4)

		self.setLayout(layout)

		self.showed.connect(self.show)
		self.hided.connect(self.hide)

class GameSeat(QtWidgets.QWidget):

	showed = QtCore.pyqtSignal()
	hided = QtCore.pyqtSignal()
	inited = QtCore.pyqtSignal(str)
	assigned = QtCore.pyqtSignal()
	voted = QtCore.pyqtSignal()
	missioned = QtCore.pyqtSignal()
	alerted = QtCore.pyqtSignal(str, str)
	acered = QtCore.pyqtSignal()
	assassinated = QtCore.pyqtSignal()

	def __init__(self, client, parent = None):
		super(GameSeat, self).__init__(parent)

		self.client = client

		#座位
		self.l1 = QtWidgets.QLabel()
		self.l2 = QtWidgets.QLabel()
		self.l3 = QtWidgets.QLabel()
		self.l4 = QtWidgets.QLabel()
		self.l5 = QtWidgets.QLabel()
		self.l6 = QtWidgets.QLabel()
		self.l7 = QtWidgets.QLabel()
		self.l8 = QtWidgets.QLabel()
		self.l9 = QtWidgets.QLabel()
		self.l10 = QtWidgets.QLabel()
		#亞瑟王
		self.l11 = QtWidgets.QLabel('亞瑟王 - ')
		self.l12 = QtWidgets.QLabel()
		#騎士
		self.l13 = QtWidgets.QLabel('出任務騎士 - ')
		self.l14 = QtWidgets.QLabel()
		#身分
		self.l15 = QtWidgets.QLabel('你是 ')
		self.l16 = QtWidgets.QLabel()
		#天黑請閉眼
		self.l17 = QtWidgets.QLabel()
		#局數
		self.l18 = QtWidgets.QLabel('第')
		self.l19 = QtWidgets.QLabel('1')
		self.l26 = QtWidgets.QLabel('局')
		#好盃
		self.l20 = QtWidgets.QLabel('好人贏')
		self.l21 = QtWidgets.QLabel('0')
		self.l27 = QtWidgets.QLabel('局')
		#壞盃
		self.l22 = QtWidgets.QLabel('壞人贏')
		self.l23 = QtWidgets.QLabel('0')
		self.l28 = QtWidgets.QLabel('局')
		#投票次數
		self.l24 = QtWidgets.QLabel('投票次數 : ')
		self.l25 = QtWidgets.QLabel('0')
		#提示框
		self.l29 = QtWidgets.QLabel()

		self.showed.connect(self.show)
		self.hided.connect(self.hide)
		self.inited.connect(self.init)
		self.assigned.connect(self.assign)
		self.voted.connect(self.vote)
		self.alerted.connect(self.alert)
		self.missioned.connect(self.mission)
		self.acered.connect(self.chooseAcer)
		self.assassinated.connect(self.assassinate)


	@QtCore.pyqtSlot(str)
	def init(self, text):
		self.gw = 0
		self.bw = 0
		self.acer = -1
		self.vote_num = 0

		if self.client.again:
			self.l14.setText('')
			self.l19.setText('1')
			self.l21.setText('0')
			self.l23.setText('0')
			self.l25.setText('0')
		else:
			self.labels = []
			self.labels.append(self.l9)
			if window.person > 8:
				self.labels.append(self.l10)
			if window.person > 6:
				self.labels.append(self.l7)
			self.labels.append(self.l5)
			if window.person % 2 == 0:
				self.labels.append(self.l3)
			self.labels.append(self.l2)
			self.labels.append(self.l1)
			self.labels.append(self.l4)
			if window.person > 6:
				self.labels.append(self.l6)
			if window.person > 8:
				self.labels.append(self.l8)

			for label in self.labels:
				label.setStyleSheet('border:2px solid gray;')
				label.setMinimumSize(label.size().width() / 10, label.size().height() / 10);
				label.setAlignment(QtCore.Qt.AlignCenter); 

			#垂直排版
			l0 = QtWidgets.QHBoxLayout()
			l0.addWidget(self.l18)
			l0.addWidget(self.l19)
			l0.addWidget(self.l26)
			l0.addStretch(1)
			l0.addWidget(self.l20)
			l0.addWidget(self.l21)
			l0.addWidget(self.l27)
			l0.addStretch(1)
			l0.addWidget(self.l22)
			l0.addWidget(self.l23)
			l0.addWidget(self.l28)
			l0.addStretch(1)
			l0.addWidget(self.l24)
			l0.addWidget(self.l25)

			l1 = QtWidgets.QHBoxLayout()
			l1.addWidget(self.l11)
			l1.addWidget(self.l12)
			l1.addStretch(1)
			l1.addWidget(self.l13)
			l1.addWidget(self.l14)

			l2 = QtWidgets.QHBoxLayout()
			l2.addStretch(1)
			l2.addWidget(self.l1)
			l2.addStretch(1)
			l2.addWidget(self.l2)
			if window.person % 2 == 0:
				l2.addStretch(1)
				l2.addWidget(self.l3)
			l2.addStretch(1)

			l3 = QtWidgets.QHBoxLayout()
			l3.addWidget(self.l4)
			l3.addStretch(1)
			l3.addWidget(self.l29)
			l3.addStretch(1)
			l3.addWidget(self.l5)

			l4 = QtWidgets.QHBoxLayout()
			l4.addWidget(self.l6)
			l4.addStretch(1)
			l4.addWidget(self.l7)

			l5 = QtWidgets.QHBoxLayout()
			l5.addStretch(1)
			if window.person > 8:
				l5.addWidget(self.l8)
				l5.addStretch(1)
			l5.addWidget(self.l9)
			if window.person > 8:
				l5.addStretch(1)
				l5.addWidget(self.l10)
			l5.addStretch(1)

			l6 = QtWidgets.QHBoxLayout()
			l6.addWidget(self.l15)
			l6.addWidget(self.l16)
			l6.addStretch(1)
			l6.addWidget(self.l17)

			layout = QtWidgets.QVBoxLayout()
			layout.addLayout(l0)
			layout.addLayout(l1)
			layout.addStretch(1)
			layout.addLayout(l2)
			layout.addStretch(1)
			layout.addLayout(l3)
			layout.addStretch(1)
			if window.person > 6:
				layout.addLayout(l4)
				layout.addStretch(1)
			layout.addLayout(l5)
			layout.addStretch(1)
			layout.addLayout(l6)

			self.setLayout(layout)
		
		self.seats = text.split(' ')
		flag = False
		count = 0
		for seat in self.seats:
			if nickname == seat:
				flag = True
			if flag:
				self.labels[count].setText(seat)
				count = count + 1
		for seat in self.seats:
			if nickname == seat:
				flag = False
			if flag:
				self.labels[count].setText(seat)
				count = count + 1
		self.l16.setText(self.role)
		self.l17.setText(self.see)

	@QtCore.pyqtSlot()
	def chooseAcer(self):
		self.acer = (self.acer + 1) % window.person
		self.l12.setText(self.seats[self.acer])
		for label in self.labels:
			if label.text() == self.seats[self.acer]:
				label.setStyleSheet('border:3px solid red;color:red;')
			else:
				label.setStyleSheet('border:2px solid gray;')

	@QtCore.pyqtSlot()
	def assign(self):
		ad = AssignDlg()
		self.knights = []
		if ad.exec_():
			text = ' '.join(self.knights)
			window.output.write(('/assign ' + text + '\r\n').encode('utf-8'))

	@QtCore.pyqtSlot()
	def vote(self):
		for label in self.labels:
			if label.text() in self.knights:
				label.setStyleSheet(label.styleSheet() + "background-color:lightgreen;")
		vd = VoteDlg()
		if vd.exec_():
			window.output.write(('/vote a\r\n').encode('utf-8'))
		else:
			window.output.write(('/vote r\r\n').encode('utf-8'))
			
	@QtCore.pyqtSlot()
	def mission(self):
		self.vote_num = 0
		self.l25.setText(str(window.gameSeat.vote_num))
		self.l29.setText('請等候所有騎士出任務')
		md = MissionDlg()
		if md.exec_():
			window.output.write(('/mission g\r\n').encode('utf-8'))
		else:
			window.output.write(('/mission b\r\n').encode('utf-8'))

	@QtCore.pyqtSlot(str, str)
	def alert(self, str1, str2):
		window.alert(str1, str2)

	@QtCore.pyqtSlot()
	def assassinate(self):
		ad = AssassinDlg()
		if ad.exec_():
			window.output.write(('/assassin ' + ad.ap + '\r\n').encode('utf-8'))
	
class Truth(QtWidgets.QWidget):

	showed = QtCore.pyqtSignal()
	hided = QtCore.pyqtSignal()
	inited = QtCore.pyqtSignal(str)

	def __init__(self, client, parent = None):
		super(Truth, self).__init__(parent)

		self.client = client
		self.showed.connect(self.show)
		self.hided.connect(self.hide)
		self.inited.connect(self.init)

	@QtCore.pyqtSlot()
	def rerole(self):
		window.output.write(('/rerole\r\n').encode('utf-8'))

	@QtCore.pyqtSlot(str)
	def init(self, text):
		if self.client.again:
			self.layout().deleteLater()
			QtWidgets.QWidget().setLayout(self.layout())
		roles = text.split(' ')
		layout = QtWidgets.QVBoxLayout()
		for i in range(len(roles)):
			l = QtWidgets.QHBoxLayout()
			temp = QtWidgets.QLabel()
			pic = QtGui.QPixmap('images/' + roles[i] + '.jpg')
			#pic = pic.scaled(pic.width()/4, pic.height()/4, QtCore.Qt.KeepAspectRatio);
			pic = pic.scaled(pic.width() * (window.height()/(window.person + 1)) / pic.height(), window.height()/(window.person + 1), QtCore.Qt.KeepAspectRatio);
			temp.setPixmap(pic)
			l.addWidget(temp)
			l.addStretch(1)
			l.addWidget(QtWidgets.QLabel(roles[i]))
			l.addWidget(QtWidgets.QLabel(window.gameSeat.seats[i]))
			layout.addLayout(l)
		if window.game_host:
			l = QtWidgets.QHBoxLayout()
			l.addStretch(1)
			rerole = QtWidgets.QPushButton("重選角色")
			l.addWidget(rerole)
			l.addStretch(1)
			quit = QtWidgets.QPushButton("不玩了")
			l.addWidget(quit)
			l.addStretch(1)
			layout.addLayout(l)

			rerole.clicked.connect(self.rerole)
			quit.clicked.connect(window.close)
		self.setLayout(layout)


class AssignDlg(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(AssignDlg,self).__init__(parent)
		self.setWindowTitle(nickname + ' - 指派任務')
		self.num = 0
		if window.person < 8:
			if window.gameSeat.gw + window.gameSeat.bw == 0:
				self.num = 2
			elif window.person == 5 and window.gameSeat.gw + window.gameSeat.bw == 2:
				self.num = 2
			elif window.person == 6 and (window.gameSeat.gw + window.gameSeat.bw == 2 or window.gameSeat.gw + window.gameSeat.bw == 4):
				self.num = 4
			elif window.person == 7 and window.gameSeat.gw + window.gameSeat.bw > 2:
				self.num = 4
			else:
				self.num = 3
		else:
			if window.gameSeat.gw + window.gameSeat.bw == 0:
				self.num = 3
			elif window.gameSeat.gw + window.gameSeat.bw > 2:
				self.num = 5
			else:
				self.num = 4
		layout = QtWidgets.QVBoxLayout()

		self.le = QtWidgets.QLineEdit()
		self.send = QtWidgets.QPushButton("發送")
		l1 = QtWidgets.QHBoxLayout()
		l1.addWidget(self.le)
		l1.addWidget(self.send)
		layout.addLayout(l1)
		self.le.returnPressed.connect(self.say)
		self.send.clicked.connect(self.say)

		l = QtWidgets.QLabel('請指派要出任務的 ' + str(self.num) + ' 位騎士')
		layout.addWidget(l)
		self.cb = []
		for count in range(window.person):
			self.cb.append(QtWidgets.QCheckBox(window.gameSeat.seats[count]))
			layout.addWidget(self.cb[count])
		pb = QtWidgets.QPushButton('確定')
		layout.addWidget(pb)
		self.setLayout(layout)
		pb.clicked.connect(self.check)
	
	def check(self):
		for count in range(window.person):
			if (self.cb[count].isChecked()):
				window.gameSeat.knights.append(window.gameSeat.seats[count])
		if (self.num != len(window.gameSeat.knights)):
			window.alert("設定錯誤", "指派人數和規定不符")
			window.gameSeat.knights = []
		else:
			self.accept()
	
	def say(self, temp = None):
		#當從標準輸入讀入時沒必要去解密
		inputText = self.le.text().strip()
		if inputText:
			window.output.write((inputText + '\r\n').encode('utf-8'))
		window.chat.chat.append('<div style = "color:green">' + self.le.text() + '</div>')
		window.chat.chat.verticalScrollBar().setValue(window.chat.chat.verticalScrollBar().maximum())
		self.le.clear()

	def closeEvent(self, evnt):
		evnt.ignore()
		alert('不給你關', '嘿嘿，不給你關')

class AssassinDlg(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(AssassinDlg,self).__init__(parent)
		self.setWindowTitle(nickname + ' - 刺殺')
		layout = QtWidgets.QVBoxLayout()

		self.le = QtWidgets.QLineEdit()
		self.send = QtWidgets.QPushButton("刺殺")
		l1 = QtWidgets.QHBoxLayout()
		l1.addWidget(self.le)
		l1.addWidget(self.send)
		layout.addLayout(l1)
		self.le.returnPressed.connect(self.say)
		self.send.clicked.connect(self.say)

		l = QtWidgets.QLabel('請刺殺 (刺中則好人輸)')
		layout.addWidget(l)
		self.cb = []
		for count in range(window.person):
			self.cb.append(QtWidgets.QCheckBox(window.gameSeat.seats[count]))
			layout.addWidget(self.cb[count])
		pb = QtWidgets.QPushButton('確定')
		layout.addWidget(pb)
		self.setLayout(layout)
		pb.clicked.connect(self.check)
	
	def check(self):
		num = 0
		for count in range(window.person):
			if (self.cb[count].isChecked()):
				self.ap = window.gameSeat.seats[count]
				num += 1
		if (num != 1):
			window.alert("設定錯誤", "必須且只能刺殺一人")
		else:
			self.accept()
	
	def say(self, temp = None):
		#當從標準輸入讀入時沒必要去解密
		inputText = self.le.text().strip()
		if inputText:
			window.output.write((inputText + '\r\n').encode('utf-8'))
		window.chat.chat.append('<div style = "color:green">' + self.le.text() + '</div>')
		window.chat.chat.verticalScrollBar().setValue(window.chat.chat.verticalScrollBar().maximum())
		self.le.clear()

	def closeEvent(self, evnt):
		evnt.ignore()
		alert('不給你關', '嘿嘿，不給你關')

class VoteDlg(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(VoteDlg,self).__init__(parent)
		self.setWindowTitle(nickname + ' - 投票')
		layout = QtWidgets.QVBoxLayout()

		self.le = QtWidgets.QLineEdit()
		self.send = QtWidgets.QPushButton("傳送")
		l1 = QtWidgets.QHBoxLayout()
		l1.addWidget(self.le)
		l1.addWidget(self.send)
		layout.addLayout(l1)
		self.le.returnPressed.connect(self.say)
		self.send.clicked.connect(self.say)

		l = QtWidgets.QLabel('亞瑟王派 ' + window.gameSeat.l14.text() + ' 出任務\n請投票，贊成票若超過玩家人數的一半即會出任務')
		layout.addWidget(l)
		pb1 = QtWidgets.QPushButton('贊成')
		pb2 = QtWidgets.QPushButton('反對')
		l1 = QtWidgets.QHBoxLayout()
		l1.addWidget(pb1)
		l1.addWidget(pb2)
		layout.addLayout(l1)
		self.setLayout(layout)
		pb1.clicked.connect(self.accept)
		pb2.clicked.connect(self.reject)
	
	def say(self, temp = None):
		#當從標準輸入讀入時沒必要去解密
		inputText = self.le.text().strip()
		if inputText:
			window.output.write((inputText + '\r\n').encode('utf-8'))
		window.chat.chat.append('<div style = "color:green">' + self.le.text() + '</div>')
		window.chat.chat.verticalScrollBar().setValue(window.chat.chat.verticalScrollBar().maximum())
		self.le.clear()

	def closeEvent(self, evnt):
		evnt.ignore()
		alert('不給你關', '嘿嘿，不給你關')

class MissionDlg(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(MissionDlg,self).__init__(parent)
		self.setWindowTitle(nickname + ' - 出任務')
		layout = QtWidgets.QVBoxLayout()
		l = QtWidgets.QLabel('亞瑟王派 ' + window.gameSeat.l14.text() + ' 出任務\n請選擇成功或失敗，好人只能選成功')
		layout.addWidget(l)
		l1 = QtWidgets.QHBoxLayout()
		pb1 = QtWidgets.QPushButton('任務成功')
		l1.addWidget(pb1)
		for i in range(window.choose.bad_choosen.count()):
			if window.gameSeat.role == window.choose.bad_choosen.item(i).text() or window.gameSeat.role == '爪牙':
				pb2 = QtWidgets.QPushButton('任務失敗')
				l1.addWidget(pb2)
				pb2.clicked.connect(self.reject)
				break
		layout.addLayout(l1)
		self.setLayout(layout)
		pb1.clicked.connect(self.accept)

	def closeEvent(self, evnt):
		evnt.ignore()
		alert('不給你關', '嘿嘿，不給你關')

class NameDlg(QtWidgets.QDialog):
	def __init__(self,parent=None):
		super(NameDlg,self).__init__(parent)
		self.setWindowTitle('取暱稱')
		l = QtWidgets.QLabel('請輸入暱稱：')
		self.le = QtWidgets.QLineEdit()
		pb = QtWidgets.QPushButton('確定')
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(l)
		layout.addWidget(self.le)
		layout.addWidget(pb)
		self.setLayout(layout)
		pb.clicked.connect(self.send)

	def send(self):
		if self.le.text().strip() == "":
			alert('', '至少輸入一個字啊')	
		elif len(self.le.text().strip()) > 8:
			alert('', '最多輸入八個字')
		elif self.le.text().strip().find(' ') != -1:
			alert('', '暱稱中間不能有空白')
		elif self.le.text().strip().find('/') != -1:
			alert('', '暱稱中間不能有 /')
		elif self.le.text().strip().find(',') != -1:
			alert('', '暱稱中間不能有 ,')
		else:
			self.accept()


def alert(string1, string2):
	#字體大小
	f = QtGui.QFont()
	f.setPointSize(14)
	#訊息窗 & 標題
	alert = QtWidgets.QDialog()
	alert.setWindowTitle(string1)
	#訊息
	label = QtWidgets.QLabel("  " + string2 + "  ")
	label.setFont(f)
	#按鈕
	button = QtWidgets.QPushButton("我知道了啦")
	#水平排版
	hl = QtWidgets.QHBoxLayout()
	hl.addStretch(1)
	hl.addWidget(button)
	hl.addStretch(1)
	#垂直排版
	vl = QtWidgets.QVBoxLayout()
	vl.addWidget(label)
	vl.addStretch(1)
	vl.addLayout(hl)
	alert.setLayout(vl)
	#按鈕事件
	button.clicked.connect(alert.accept)
	#運行
	alert.exec_()

#主函數
if __name__ == '__main__':
	#看看是否有使用者有作業系統提供的預設使用者名稱，若沒有，他們必須定義一個新的暱稱
	try:
		import pwd
		defaultNickname = pwd.getpwuid(os.getuid())[0]
	except ImportError:
		defaultNickname = None

	if len(sys.argv) < 3:
		print('Usage: %s [hostname] [port number] [username]' % sys.argv[0])
		sys.exit(1)

	hostname = sys.argv[1]
	port = int(sys.argv[2])

	if len(sys.argv) > 3:
		nickname = sys.argv[3]
	else:
		#這個系統上我們必須有使用者名稱，否則我們將要早點離開
		nickname = defaultNickname

	#每個 Qt GUI 程式都需要一個 (唯一一個) QApplication，負責管理 Qt 資源、控制執行流程和有的沒的例行事務，雖然很少會用 command line 來開 GUI 程式，還是得帶 sys.argv 參數來初始化它
	app = QtWidgets.QApplication(sys.argv)

	if not defaultNickname and len(sys.argv) < 4:
		nd = NameDlg()
		if nd.exec_():
			nickname = nd.le.text()

	window = Client(hostname, port, nickname)
	#讓 widget 顯示出來。所有圖形元件被創造時都是 hidden 狀態，可以先設定好它的外觀再顯示出來，免得一直重繪造成畫面閃爍
	window.show()

	#讓 QApplication 進入 event loop，直到程式接收結束訊號。原本 C++ Qt 是用 memfunc exec()，但在 Python 中名稱已被佔用，所以得加一個底線
	app.exec_()
