import socketserver
import re
import socket
import random

#客戶端給錯誤的輸入到服務器以至於一個例外被拋出
class ClientError(Exception):
	#此 class 中新增沒有任何東西 (全都跟 Exception 一樣)
	pass

#服務器
class PythonChatServer(socketserver.ThreadingTCPServer):
	#在使用者暱稱和 socket 之間設定一個初始化的空地圖
	def __init__(self, server_address, RequestHandlerClass):
		socketserver.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
		self.users = {}

#維持使用者至服務器連線的生命週期 : 連接、聊天、執行服務器命令、斷開連接
class RequestHandler(socketserver.StreamRequestHandler):
	#合法暱稱的正則表達式
	#NICKNAME = re.compile('^[A-Za-z0-9_-]+$')

	#維持使用者至服務器連線 : 獲取使用者的暱稱，然後處理使用者的輸入 (聊天內容) 直到他們離開或中斷連線
	def handle(self):
		self.server.accept = []
		self.server.reject = []
		self.server.pc = 0

		self.nickname = None

		self.privateMessage("Who are you?")
		nickname=self.readline()
		done = False
		try:
			self.nickCommand(nickname)
			self.broadcast('%s 加入遊戲' %nickname, False)
			self.broadcast('/j' + ('  '.join(self.server.users.keys())), False)
		except (ClientError) as error:
			self.privateMessage(error.args[0])
			done = True
		except socket.error:
			done = True

		#已經登入了，開始聊天
		while not done:
			try:
				done = self.processInput()
			except (ClientError) as error:
				self.privateMessage(str(error))
			except socket.error:
				done = True

	#當 handle() 結束時被自動呼叫
	def finish(self):
		if self.nickname:
			#使用者在斷開連接之前廣播某人要離開
			message = '%s 離開遊戲' % self.nickname
			if hasattr(self, 'partingWords'):
				message = '%s 離開遊戲: %s' % (self.nickname, self.partingWords)
			self.broadcast(message, False)
			#從清單上移除該使用者因此不用繼續送訊息給該人
			if self.server.users.get(self.nickname):
				del(self.server.users[self.nickname])
			self.broadcast('/q' + (' '.join(self.server.users.keys())), False)
		self.request.shutdown(2)
		self.request.close()

	#從 socket input 讀一行然後將其解讀為命令執行之或是將其解讀為聊天內容廣播之
	def processInput(self):
		done = False
		l = self.readline()
		command, arg = self.parseCommand(l)
		if command:
			done = command(arg)
		else:
			l = '<%s> %s\n' % (self.nickname, l)
			self.broadcast(l)
		return done

	#處理暱稱的函數 (嘗試改變一個使用者的暱稱)
	def nickCommand(self,nickname):
		if not nickname:
			raise ClientError('No nickname provided.')
		#if not self.NICKNAME.match(nickname):
		#	raise ClientError('Invalid nickname: %s' % nickname)
		if nickname == self.nickname:
			raise ClientError('You\'re already known as %s.' % nickname)
		if self.server.users.get(nickname,None):
			raise ClientError('There\'s already a user named "%s" here.' %nickname)
		oldNickname = None
		if self.nickname:
			oldNickname=self.nickname
			del(self.server.users[self.nickname])
		self.server.users[nickname]=self.wfile
		self.nickname=nickname
		if oldNickname:
			self.broadcast('%s is now known as %s' % (oldNickname, self.nickname))

	#告訴其他使用者該使用者已經離開，然後保證 handler 會關閉這個連線
	def quitCommand(self, partingWords):
		if partingWords:
			self.partingWords = partingWords
		#傳回 True 確保使用者會被斷連
		return True

	#傳回該聊天室的使用者列表
	def namesCommand(self, ignored):
		self.privateMessage('  '.join(self.server.users.keys()))

	#接收好人
	def rolegCommand(self, names):
		self.server._goods = names

	#接收壞人
	def rolebCommand(self, names):
		self.server._bads = names
		self.broadcast('-', True)
		self.broadcast('房主已經選好角色了。\n好人是 ' + ', '.join(self.server._goods) + '\n壞人是 ' + ', '.join(self.server._bads), True)
		self.broadcast('請等候所有玩家準備。', True)
		self.broadcast('/prepare')
		self.broadcast(' '.join(self.server._goods))
		self.broadcast(' '.join(self.server._bads))

	def assignCommand(self, knights):
		self.server.knights = knights
		text = ', '.join(knights)
		self.broadcast('-', True)
		self.broadcast('亞瑟王選擇了 ' + text + ' 出任務', True)
		self.broadcast('開始進行投票，請等候所有玩家投完票。', True)
		self.broadcast('/vote ' + text, True)

	def voteCommand(self, vote):
		if vote[0] == 'a':
			self.server.accept.append(self.nickname)
		else:
			self.server.reject.append(self.nickname)
		if len(self.server.accept) + len(self.server.reject) == len(self.server.users):
			self.broadcast('-', True)
			self.broadcast('投票結束，投票結果如下：', True)
			if len(self.server.accept) > len(self.server.reject):
				self.broadcast('贊成票過半。', True)
			else:
				self.broadcast('贊成票沒過半。', True)
			if len(self.server.accept) == 0:
				self.broadcast('贊成 0 票', True)
			else:
				self.broadcast('贊成 ' + str(len(self.server.accept)) + ' 票：' + ', '.join(self.server.accept), True)
			if len(self.server.reject) == 0:
				self.broadcast('反對 0 票', True)
			else:
				self.broadcast('反對 ' + str(len(self.server.reject)) + ' 票：' + ', '.join(self.server.reject), True)
			if len(self.server.accept) > len(self.server.reject):
				self.server.vote_num = 0
				self.broadcast('-', True)
				self.broadcast('野豬騎士出任務囉，請等候所有騎士出完任務。', True)
				self.broadcast('/mission y\n', True)
			else:
				self.server.vote_num += 1
				self.assign()
				self.broadcast('/mission n\n', True)
			self.server.accept = []
			self.server.reject = []
	
	def missionCommand(self, vote):
		if vote[0] == 'g':
			self.server.goods += 1
		else:
			self.server.bads += 1
		if self.server.goods + self.server.bads == len(self.server.knights):
			self.broadcast('-', True)
			if self.server.bads == 0 or (self.server.bads == 1 and len(self.server.users) > 6 and (self.server.bw + self.server.gw) == 3):
				self.broadcast('任務成功，' + str(self.server.bads) + ' 個壞盃。', True)
				self.server.gw += 1
				self.broadcast('/gw\n', True)
			else:
				self.broadcast('任務失敗，' + str(self.server.bads) + ' 個壞盃。', True)
				self.server.bw += 1
				self.broadcast('/bw\n', True)
			if self.server.gw == 3:
				self.broadcast('/assassin\n', True)
				self.broadcast('-', True)
				self.broadcast('請等待刺客刺殺。', True)
			elif self.server.bw == 3:
				text = ''
				for seat in self.server.seats:
					text += self.server.role[seat] + ' '
				self.broadcast('壞人獲勝。', True)
				self.broadcast('/gameover b\n' + text + '\n', True)
			else:
				self.assign()
			self.server.goods = 0
			self.server.bads = 0

	def assassinCommand(self, ap):
		text = ''
		for seat in self.server.seats:
			text += self.server.role[seat] + ' '
		self.broadcast('-', True)
		self.broadcast('刺殺結果\n刺客刺 ' + ap[0] + '，他的身分是 ' + self.server.role[ap[0]] + '。', True)
		if self.server.role[ap[0]] != '梅林':
			self.broadcast('好人獲勝。', True)
			self.broadcast('/gameover g\n' + text + '\n', True)
		else:
			self.broadcast('壞人獲勝。', True)
			self.broadcast('/gameover b\n' + text + '\n', True)

	def prepareCommand(self, yn):
		if yn[0] == 'y':
			self.server.pc += 1
			self.broadcast(self.nickname + ' 已準備', True)
		else:
			self.server.pc -= 1
			self.broadcast(self.nickname + ' 已取消準備', True)
		if len(self.server.users) == (self.server.pc + 1):
			self.broadcast('-', True)
			self.broadcast('所有人都已就緒，遊戲準備開始...', True)

			self.server.role = {}
			roles = self.server._goods + self.server._bads
			for user, output in self.server.users.items():
				index = random.randrange(0, len(roles))
				text = self.ensureNewline('/role ' + roles.pop(index))
				output.write(text.encode('utf-8'))
				self.server.role[user] = text[6:-2]
				if self.server.role[user] == '忠臣':
					text = '你是一個好人。\n'
				elif self.server.role[user] == '梅林':
					text = '你是單身已久的大魔法師，看得見所有壞人。\n'
				elif self.server.role[user] == '派西維爾':
					text = '你是輔助梅林的小弟，可以看到梅林。\n'
				elif self.server.role[user] == '刺客':
					text = '你擅長暗殺，有機會刺殺梅林。\n'
				elif self.server.role[user] == '莫甘娜':
					text = '你擅長易容，可以模仿梅林，迷惑派西維爾。\n'
				elif self.server.role[user] == '莫德雷德':
					text = '你是壞人的老大，不會被梅林看到。\n'
				elif self.server.role[user] == '奧伯倫':
					text = '你是興趣使然的壞人，和其他壞人沒有交集。\n'
				elif self.server.role[user] == '爪牙':
					text = '你是一個壞人。\n'
				output.write(text.encode('utf-8'))
			for user, output in self.server.users.items():
				if self.server.role[user] == '忠臣' or self.server.role[user] == '奧伯倫':
					text = '你神馬都看不見 QAQ'
				if self.server.role[user] in self.server._bads and self.server.role[user] != '奧伯倫':
					text = '其他壞人是 '
					for user2, output2 in self.server.users.items():
						if self.server.role[user2] in self.server._bads and self.server.role[user2] != '奧伯倫' and user2 != user:
							text = text + user2 + ", "
				if self.server.role[user] == '梅林':
					text = '壞人是 '
					for user2, output2 in self.server.users.items():
						if self.server.role[user2] in self.server._bads and self.server.role[user2] != '莫德雷德':
							text = text + user2 + ", "
				if self.server.role[user] == '派西維爾':
					text = '梅林 (& 莫甘娜) 是 '
					for user2, output2 in self.server.users.items():
						if self.server.role[user2] == '梅林' or self.server.role[user2] == '莫甘娜':
							text = text + user2 + ", "
				output.write(self.ensureNewline(text).encode('utf-8'))
			import time
			time.sleep(5)
			self.server.seats = list(self.server.users)
			random.shuffle(self.server.seats)
			self.broadcast('/seat ' + ' '.join(self.server.seats), True)

			self.server.gw = 0
			self.server.bw = 0
			self.server.acer = -1
			self.server.goods = 0
			self.server.bads = 0
			self.server.vote_num = 0

			self.assign()

	def reroleCommand(self, ignore):
		self.server.pc = 0
		self.broadcast('/rerole', True)

	def assign(self):
		self.server.acer = (self.server.acer + 1) % len(self.server.users)
		self.broadcast('/acer', True)
		for user, output in self.server.users.items():
			if user == self.server.seats[self.server.acer]:
				output.write('/assig2\n'.encode('utf-8'))
		self.broadcast('-', True)
		self.broadcast('第 ' + str(self.server.gw + self.server.bw + 1) + ' 局 - 第 ' + str(self.server.vote_num + 1) + ' 次：', True)
		self.broadcast('亞瑟王 ' + self.server.seats[self.server.acer] + ' 正在選騎士，請等候亞瑟王指派。', True)
		self.broadcast('/assign\n', True)


	#下面為 helper methods (用來幫助其他 methods，外部不會用到)

	#傳送訊息到除了發送者之外的每個使用者端
	def broadcast(self, message, includeThisUser=False):
		message = self.ensureNewline(message)
		for user, output in self.server.users.items():
			if includeThisUser or user != self.nickname:
				output.write(message.encode('utf-8'))

	#傳送訊息至該使用者
	def privateMessage(self, message):
		self.wfile.write(self.ensureNewline(message).encode('utf-8'))

	#讀一整行，並移除首尾的每個空白
	def readline(self):
		return self.rfile.readline().strip().decode('utf-8')

	#確保一個字串會以新行 (\r\n) 結束
	def ensureNewline(self, s):
		if s and s[-1] !='\n':
			s += '\r\n'
		return s

	#解析字串成對系統的命令，若其為應用的命令則去跑對應的方法 (/xxx => xxxCommand)
	def parseCommand(self, input):
		commandMethod, arg = None, None
		if input and input[0]=='/':
			#只有一個字元 '/'
			if len(input) < 2:
				raise ClientError('Invalid command: "%s"' % input)
			#去掉 '/' , 將命令和參數分開 (命令:commandAndArg[0], 參數(們):commandAndArg[1])
			commandAndArg = input[1:].split(' ',1)
			#有參數 (command = commandAndArg[0], arg = commandAndArg[1])
			if len(commandAndArg) == 2:
				command, arg = commandAndArg
				arg = arg.split(' ')
			#無參數
			else:
				#不能沒中括號，否則其為 list
				command = commandAndArg[0]
			commandMethod = getattr(self, command + 'Command', None)
			if not commandMethod:
				raise ClientError('無此 command: "%s"' %command)
		#input[0]!='/' 代表 input 不是命令，則 commandMethod 為 None
		return commandMethod, arg

#表示當前執行的為此檔 (否則在 import 時仍會執行)
if __name__ == '__main__':
	import sys
	if len(sys.argv) < 3:
		print('Usage: %s [hostname] [port number]' %sys.argv[0])
		sys.exit(1)
	hostname = sys.argv[1]
	port = int(sys.argv[2])
	PythonChatServer((hostname,port),RequestHandler).serve_forever()
