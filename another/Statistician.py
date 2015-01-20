import argparse
import sys
import socket

from util import packet_parse

RAISE = "RAISE"
CALL = "CALL"
FOLD = "FOLD"
CHECK = "CHECK"
BET = "BET"

SHOW = "SHOW"
FLOP = "FLOP"
TURN = "TURN"
RIVER = "RIVER"

class Statistician:

	def __init__(self):
		self.opp1_name = ""
		self.opp2_name = ""
		self.numHandsPlayed = 0
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.myWinCount = 0
		self.myRaiseCount = 0
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.twoBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrBoolean = {self.opp1_name: False, self.opp2_name: False}

		# Post-Flop statistics below
		# Determine how many times each opponent goes to Flop
		self.seenFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.cbCountBool = {self.opp1_name : False, self.opp2_name : False}
		# How often opponent makes another cont. bet after first one
		self.doubleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.doubleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		self.tripleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.tripleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}
		# To compute Check-Raise
		self.checkCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountRiver = {self.opp1_name : 0, self.opp2_name : 0}
		# self.foldcbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.fold2cbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountRiver = {self.opp1_name : 0, self.opp2_name : 0}


	def processPreflopStatistics(self, opponent_names, hand_statistics):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == RAISE 
					self.pfrCount[opponent_name] += 1
					self.pfrBoolean[opponent_name] = True

				elif split_action[0] == CALL and self.myRaiseCount > 0:
					self.callRaiseCount[opponent_name] += 1
			
			else:
				if split_action[0] == RAISE:
					self.myRaiseCount += 1

		for opp_name in opponent_names:
			if self.myRaiseCount > 0 and self.pfrCount[opp_name] > 0:
				self.threeBCount[opp_name] += 1 

			elif self.myRaiseCount == 1 and self.pfrCount[opp_name] == 0:
				self.twoBCount[opp_name] += 1

			elif self.myRaiseCount > 0 and self.callRaiseCount[opp_name] < self.myRaiseCount:
				self.pfrFoldCount[opp_name] += 1

	def processPostFlopStatistics(self, opponent_names, hand_statistics, board_state):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			#Count Opponent Statistics
			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				self.seenFlop[opponent_name] += 1

				if split_action[0] == CHECK:
					if board_state == FLOP:
						self.checkCountFlop[opponent_name] += 1
					
					# elif board_state == TURN:
					# 	self.checkCountTurn[opponent_name] += 1
					
					# else:
					# 	self.checkCountRiver[opponent_name] += 1
					self.checkCount[opponent_name] += 1

				elif split_action[0] == RAISE:
					
					if self.pfrBoolean[opponent_name] and board_state == FLOP:
						self.cbCount[opponent_name] += 1
						self.raiseCountFlop[opponent_name] += 1
						self.cbCountBool[opponent_name] = True
					
					elif self.cbCountBool[opponent_name] and board_state == TURN:
						self.doubleBarrelCount[opponent_name] += 1
						# self.raiseCountTurn[opponent_name] += 1
						self.doubleBarrelBool[opponent_name] = True

					elif self.doubleBarrelBool[opponent_name] and board_state == RIVER:
						self.tripleBarrelCount[opponent_name] += 1
						# self.raiseCountRiver[opponent_name] += 1
						self.tripleBarrelBool[opponent_name] = True

					self.raiseCountPost[opponent_name] += 1

				elif split_action[0] == CALL:
					self.callCountPost[opponent_name] += 1 

				elif split_action[0] == BET:
					self.betCountPost[opponent_name] += 1

				else:
					self.foldCount[opponent_name] += 1

		for opp_name in opponent_names:
			if (board_state == FLOP and (self.checkCountFlop[opp_name] == self.raiseCountFlop[opp_name])):
				self.checkRaise[opp_name] += 1
			# elif (board_state == TURN and (self.checkCountTurn[opp_name] == self.raiseCountTurn[opp_name])):
			# 	self.checkRaise[opp_name] += 1		
			# elif (board_state == RIVER and (self.checkCountRiver[opp_name] == self.raiseCountRiver[opp_name])):
			# 	self.checkRaise[opp_name] += 1	
	
	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet, hand_id):
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']
		self.numHandsPlayed = hand_id

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'])

			else:
				state = ""
				if received_packet['num_boardcards'] == 3:
					state = FLOP
				elif received_packet['num_boardcards'] == 4:
					state = TURN
				else:
					state =  RIVER
				self.processPostFlopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], state)


		#HANDOVER
		else:
			winner_string = received_packet['last_action'][-1]
			winner_string_split = winner_string.split(":")
			hand_winner = winner_string_split[-1]
			winning_amount = winner_string_split[-2]

			if winning_amount > 10:
				if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
					self.winCount[hand_winner] += 1
				else:
					self.myWinCount += 1

			#Compute showdown Count
			for last_action in received_packet['last_action']:
				last_action_split = last_action.split(":")
				
				if last_action_split[0] == SHOW:
					self.showdownCount[last_action_split[-1]] += 1

	def compileMatchStatistics(self):
		pass
	
	def getPFR():
		pass

	def getPFRFold():
		pass

	def getWinPercent():
		pass

	def getCallRaisePercent():
		pass

	def getCheckRaise():
		pass

	def getShowdownPercent():
		pass










import argparse
import sys
import socket

from util import packet_parse

RAISE = "RAISE"
CALL = "CALL"
FOLD = "FOLD"
CHECK = "CHECK"
BET = "BET"

SHOW = "SHOW"
FLOP = "FLOP"
TURN = "TURN"
RIVER = "RIVER"

class Statistician:

	def __init__(self):
		self.opp1_name = ""
		self.opp2_name = ""
		self.numHandsPlayed = 0
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.myWinCount = 0
		self.myRaiseCount = 0
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.twoBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrBoolean = {self.opp1_name: False, self.opp2_name: False}

		# Post-Flop statistics below
		# Determine how many times each opponent goes to Flop
		self.seenFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.cbCountBool = {self.opp1_name : False, self.opp2_name : False}
		# How often opponent makes another cont. bet after first one
		self.doubleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.doubleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		self.tripleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.tripleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}
		# To compute Check-Raise
		self.checkCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountRiver = {self.opp1_name : 0, self.opp2_name : 0}
		# self.foldcbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.fold2cbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountRiver = {self.opp1_name : 0, self.opp2_name : 0}


	def processPreflopStatistics(self, opponent_names, hand_statistics):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == RAISE 
					self.pfrCount[opponent_name] += 1
					self.pfrBoolean[opponent_name] = True

				elif split_action[0] == CALL and self.myRaiseCount > 0:
					self.callRaiseCount[opponent_name] += 1
			
			else:
				if split_action[0] == RAISE:
					self.myRaiseCount += 1

		for opp_name in opponent_names:
			if self.myRaiseCount > 0 and self.pfrCount[opp_name] > 0:
				self.threeBCount[opp_name] += 1 

			elif self.myRaiseCount == 1 and self.pfrCount[opp_name] == 0:
				self.twoBCount[opp_name] += 1

			elif self.myRaiseCount > 0 and self.callRaiseCount[opp_name] < self.myRaiseCount:
				self.pfrFoldCount[opp_name] += 1

	def processPostFlopStatistics(self, opponent_names, hand_statistics, board_state):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			#Count Opponent Statistics
			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				self.seenFlop[opponent_name] += 1

				if split_action[0] == CHECK:
					if board_state == FLOP:
						self.checkCountFlop[opponent_name] += 1
					
					# elif board_state == TURN:
					# 	self.checkCountTurn[opponent_name] += 1
					
					# else:
					# 	self.checkCountRiver[opponent_name] += 1
					self.checkCount[opponent_name] += 1

				elif split_action[0] == RAISE:
					
					if self.pfrBoolean[opponent_name] and board_state == FLOP:
						self.cbCount[opponent_name] += 1
						self.raiseCountFlop[opponent_name] += 1
						self.cbCountBool[opponent_name] = True
					
					elif self.cbCountBool[opponent_name] and board_state == TURN:
						self.doubleBarrelCount[opponent_name] += 1
						# self.raiseCountTurn[opponent_name] += 1
						self.doubleBarrelBool[opponent_name] = True

					elif self.doubleBarrelBool[opponent_name] and board_state == RIVER:
						self.tripleBarrelCount[opponent_name] += 1
						# self.raiseCountRiver[opponent_name] += 1
						self.tripleBarrelBool[opponent_name] = True

					self.raiseCountPost[opponent_name] += 1

				elif split_action[0] == CALL:
					self.callCountPost[opponent_name] += 1 

				elif split_action[0] == BET:
					self.betCountPost[opponent_name] += 1

				else:
					self.foldCount[opponent_name] += 1

		for opp_name in opponent_names:
			if (board_state == FLOP and (self.checkCountFlop[opp_name] == self.raiseCountFlop[opp_name])):
				self.checkRaise[opp_name] += 1
			# elif (board_state == TURN and (self.checkCountTurn[opp_name] == self.raiseCountTurn[opp_name])):
			# 	self.checkRaise[opp_name] += 1		
			# elif (board_state == RIVER and (self.checkCountRiver[opp_name] == self.raiseCountRiver[opp_name])):
			# 	self.checkRaise[opp_name] += 1	
	
	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet, hand_id):
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']
		self.numHandsPlayed = hand_id

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'])

			else:
				state = ""
				if received_packet['num_boardcards'] == 3:
					state = FLOP
				elif received_packet['num_boardcards'] == 4:
					state = TURN
				else:
					state =  RIVER
				self.processPostFlopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], state)


		#HANDOVER
		else:
			winner_string = received_packet['last_action'][-1]
			winner_string_split = winner_string.split(":")
			hand_winner = winner_string_split[-1]
			winning_amount = winner_string_split[-2]

			if winning_amount > 10:
				if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
					self.winCount[hand_winner] += 1
				else:
					self.myWinCount += 1

			#Compute showdown Count
			for last_action in received_packet['last_action']:
				last_action_split = last_action.split(":")
				
				if last_action_split[0] == SHOW:
					self.showdownCount[last_action_split[-1]] += 1

	def compileMatchStatistics(self):
		pass
	
	def getPFR():
		pass

	def getPFRFold():
		pass

	def getWinPercent():
		pass

	def getCallRaisePercent():
		pass

	def getCheckRaise():
		pass

	def getShowdownPercent():
		pass










import argparse
import sys
import socket

from util import packet_parse

RAISE = "RAISE"
CALL = "CALL"
FOLD = "FOLD"
CHECK = "CHECK"
BET = "BET"

SHOW = "SHOW"
FLOP = "FLOP"
TURN = "TURN"
RIVER = "RIVER"

class Statistician:

	def __init__(self):
		self.opp1_name = ""
		self.opp2_name = ""
		self.numHandsPlayed = 0
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.myWinCount = 0
		self.myRaiseCount = 0
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.twoBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrBoolean = {self.opp1_name: False, self.opp2_name: False}

		# Post-Flop statistics below
		# Determine how many times each opponent goes to Flop
		self.seenFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.cbCountBool = {self.opp1_name : False, self.opp2_name : False}
		# How often opponent makes another cont. bet after first one
		self.doubleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.doubleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		self.tripleBarrelCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.tripleBarrelBool = {self.opp1_name : False, self.opp2_name : False}
		
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}
		# To compute Check-Raise
		self.checkCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.raiseCountRiver = {self.opp1_name : 0, self.opp2_name : 0}
		# self.foldcbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.fold2cbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountTurn = {self.opp1_name : 0, self.opp2_name : 0}
		# self.checkCountRiver = {self.opp1_name : 0, self.opp2_name : 0}


	def processPreflopStatistics(self, opponent_names, hand_statistics):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == RAISE 
					self.pfrCount[opponent_name] += 1
					self.pfrBoolean[opponent_name] = True

				elif split_action[0] == CALL and self.myRaiseCount > 0:
					self.callRaiseCount[opponent_name] += 1
			
			else:
				if split_action[0] == RAISE:
					self.myRaiseCount += 1

		for opp_name in opponent_names:
			if self.myRaiseCount > 0 and self.pfrCount[opp_name] > 0:
				self.threeBCount[opp_name] += 1 

			elif self.myRaiseCount == 1 and self.pfrCount[opp_name] == 0:
				self.twoBCount[opp_name] += 1

			elif self.myRaiseCount > 0 and self.callRaiseCount[opp_name] < self.myRaiseCount:
				self.pfrFoldCount[opp_name] += 1

	def processPostFlopStatistics(self, opponent_names, hand_statistics, board_state):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			#Count Opponent Statistics
			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				self.seenFlop[opponent_name] += 1

				if split_action[0] == CHECK:
					if board_state == FLOP:
						self.checkCountFlop[opponent_name] += 1
					
					# elif board_state == TURN:
					# 	self.checkCountTurn[opponent_name] += 1
					
					# else:
					# 	self.checkCountRiver[opponent_name] += 1
					self.checkCount[opponent_name] += 1

				elif split_action[0] == RAISE:
					
					if self.pfrBoolean[opponent_name] and board_state == FLOP:
						self.cbCount[opponent_name] += 1
						self.raiseCountFlop[opponent_name] += 1
						self.cbCountBool[opponent_name] = True
					
					elif self.cbCountBool[opponent_name] and board_state == TURN:
						self.doubleBarrelCount[opponent_name] += 1
						# self.raiseCountTurn[opponent_name] += 1
						self.doubleBarrelBool[opponent_name] = True

					elif self.doubleBarrelBool[opponent_name] and board_state == RIVER:
						self.tripleBarrelCount[opponent_name] += 1
						# self.raiseCountRiver[opponent_name] += 1
						self.tripleBarrelBool[opponent_name] = True

					self.raiseCountPost[opponent_name] += 1

				elif split_action[0] == CALL:
					self.callCountPost[opponent_name] += 1 

				elif split_action[0] == BET:
					self.betCountPost[opponent_name] += 1

				else:
					self.foldCount[opponent_name] += 1

		for opp_name in opponent_names:
			if (board_state == FLOP and (self.checkCountFlop[opp_name] == self.raiseCountFlop[opp_name])):
				self.checkRaise[opp_name] += 1
			# elif (board_state == TURN and (self.checkCountTurn[opp_name] == self.raiseCountTurn[opp_name])):
			# 	self.checkRaise[opp_name] += 1		
			# elif (board_state == RIVER and (self.checkCountRiver[opp_name] == self.raiseCountRiver[opp_name])):
			# 	self.checkRaise[opp_name] += 1	
	
	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet, hand_id):
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']
		self.numHandsPlayed = hand_id

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'])

			else:
				state = ""
				if received_packet['num_boardcards'] == 3:
					state = FLOP
				elif received_packet['num_boardcards'] == 4:
					state = TURN
				else:
					state =  RIVER
				self.processPostFlopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], state)


		#HANDOVER
		else:
			winner_string = received_packet['last_action'][-1]
			winner_string_split = winner_string.split(":")
			hand_winner = winner_string_split[-1]
			winning_amount = winner_string_split[-2]

			if winning_amount > 10:
				if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
					self.winCount[hand_winner] += 1
				else:
					self.myWinCount += 1

			#Compute showdown Count
			for last_action in received_packet['last_action']:
				last_action_split = last_action.split(":")
				
				if last_action_split[0] == SHOW:
					self.showdownCount[last_action_split[-1]] += 1

	def compileMatchStatistics(self):
		pass
	
	def getPFR():
		pass

	def getPFRFold():
		pass

	def getWinPercent():
		pass

	def getCallRaisePercent():
		pass

	def getCheckRaise():
		pass

	def getShowdownPercent():
		pass










