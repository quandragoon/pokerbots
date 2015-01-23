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

WIN = "WIN"

class Statistician:

	def __init__(self, myName, opp1, opp2):
		self.myName = myName
		# self.myStatus = True
		self.opp1_name = opp1
		self.opp2_name = opp2
		self.totalNumHands = 0
		self.numHandsPlayed = {self.opp1_name : 0, self.opp2_name : 0}
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.myWinCount = 0
		self.myRaiseCount = 0
		self.playerRaisedPreFlop = False
		self.opponentRaisedPreFlop = False
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.vpipCount = {self.opp1_name : 0, self.opp2_name : 0}
		# self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldCountpFr = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrBoolean = {self.opp1_name: False, self.opp2_name: False}


		################# POST-FLOP WIN PERCENTAGE ####################
		self.postFlopWinCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.postFlopCount    = 0
		self.postFlopWinPct   = {self.opp1_name : 0, self.opp2_name : 0}
		################# POST-FLOP WIN PERCENTAGE ####################


		# Post-Flop statistics below
		# True if we have gone to Flop, False Otherwise
		self.playerSeenFlop = False
		# Determine how many times each opponent goes to Flop
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldcbBet = {self.opp1_name : 0, self.opp2_name : 0}
		self.playercBetBool = False
		# To compute Check-Raise
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountFlop = {self.opp1_name : 0, self.opp2_name : 0}

	def updateHandCount(self, name, hand_id):
		self.numHandsPlayed[name] = hand_id

	def processPreflopStatistics(self, opponent_names, hand_statistics, playerAction):
		if playerAction.split(":")[0] == RAISE:
			self.myRaiseCount += 1
			self.playerRaisedPreFlop = True

		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == RAISE: 
					self.pfrCount[opponent_name] += 1
					self.vpipCount[opponent_name] += 1
					self.raiseCount[opponent_name] += 1
					self.pfrBoolean[opponent_name] = True
					self.opponentRaisedPreFlop = True

				elif split_action[0] == CALL:
					self.callCount[opponent_name] += 1
					self.vpipCount[opponent_name] += 1

				elif split_action[0] == FOLD:
					if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
						self.foldCountpFr[opponent_name] += 1
					self.foldCount[opponent_name] += 1

				elif split_action[0] == CHECK:
					self.checkCount[opponent_name] += 1

	def processPostFlopStatistics(self, opponent_names, hand_statistics, board_state):
		flop_index = 0
		if board_state == FLOP:
			for index in range(len(hand_statistics)):
				split_action = hand_statistics[index].split(":")
				if split_action[0] == "DEAL":
					flop_index = index

			# Computing any Preflop Stats that we missed in the above function
			for last_action in hand_statistics[:flop_index]:
				split_action = last_action.split(":")

				if split_action[-1] in opponent_names:
					opponent_name = split_action[-1]

					if split_action[0] == CALL:
						self.callCount[opponent_name] += 1
						self.vpipCount[opponent_name] += 1

					elif split_action[0] == FOLD:
						if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
							self.foldCountpFr[opponent_name] += 1
						self.foldCount[opponent_name] += 1
		
		self.playerSeenFlop = True
		# Post Flop Statistics begins here
		for last_action in hand_statistics[flop_index:]:
			split_action = last_action.split(":")

			if board_state == FLOP:
				if (split_action[-1] == self.myName and split_action[0] == RAISE and self.playerRaisedPreFlop):
					self.playercBetBool = True

			#Count Opponent Statistics
			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == CHECK:
					if board_state == FLOP:
						self.checkCountFlop[opponent_name] += 1
					self.checkCount[opponent_name] += 1

				elif split_action[0] == RAISE:
					
					if self.pfrBoolean[opponent_name] and board_state == FLOP:
						self.cbCount[opponent_name] += 1
						self.raiseCountFlop[opponent_name] += 1
					self.raiseCount[opponent_name] += 1

				elif split_action[0] == CALL:
					self.callCount[opponent_name] += 1 

				elif split_action[0] == BET:
					self.betCount[opponent_name] += 1

				elif split_action[0] == FOLD:
					if self.playercBetBool:
						self.foldcbBet[opponent_name] += 1
					self.foldCount[opponent_name] += 1

		for opp_name in opponent_names:
			if (board_state == FLOP and (self.checkCountFlop[opp_name] == self.raiseCountFlop[opp_name])):
				self.checkRaise[opp_name] += 1

	# Update opponent statistics after each hand
	# playerAction is the most recent action that our player took
	def updateOpponentStatistics(self, received_packet, hand_id, playerAction):		
		# if (status == False):
		# 	self.myStatus = False

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], playerAction)

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
			flop_index = 0
			if (not self.playerSeenFlop and received_packet['num_boardcards'] >= 3):
				for index in range(len(received_packet['last_action'])):
					last_action = received_packet['last_action'][index]
					split_action = last_action.split(":")
					if split_action[0] == "DEAL" and split_action[-1] == FLOP:
						flop_index = index

				for last_action in received_packet['last_action'][:flop_index]:
					last_action_split = last_action.split(":")

					if (last_action_split[-1] == self.opp1_name or last_action_split[-1] == self.opp2_name):
						opponent_name = last_action_split[-1]

						if last_action_split[0] == RAISE:
							self.pfrCount[opponent_name] += 1
							self.vpipCount[opponent_name] += 1
							self.raiseCount[opponent_name] += 1
							self.pfrBoolean[opponent_name] = True

						elif last_action_split[0] == CALL:
							self.vpipCount[opponent_name] += 1
							self.callCount[opponent_name]

						elif last_action_split[0] == CHECK:
							self.checkCount[opponent_name] += 1

			# if self.myStatus:

			winner_string = received_packet['last_action'][-1]
			winner_string_split = winner_string.split(":")
			if winner_string_split[0] == WIN:
				hand_winner = winner_string_split[-1]
				winning_amount = int(winner_string_split[-2])

				if received_packet['num_boardcards'] >= 3:
					if hand_winner != self.myName:
						self.postFlopCount += 1
						self.postFlopWinCount[hand_winner] += 1

				# if winning_amount > 10:
				# 	if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
				# 		self.winCount[hand_winner] += 1
				# 	else:
				# 		self.myWinCount += 1

			for last_action in received_packet['last_action'][flop_index:]:
				last_action_split = last_action.split(":")

				if (last_action_split[-1] == self.opp1_name or last_action_split[-1] == self.opp2_name):
					opponent_name = last_action_split[-1]

					if last_action_split[0] == RAISE:
						if received_packet['num_boardcards'] == 0:
							self.opponentRaisedPreFlop = True
							self.pfrCount[opponent_name] += 1
							self.vpipCount[opponent_name] += 1
						elif received_packet['num_boardcards'] == 3:
							if self.pfrBoolean[opponent_name]:
								self.cbCount[opponent_name] += 1
						self.raiseCount[opponent_name] += 1

					elif last_action_split[0] == CALL:
						if received_packet['num_boardcards'] == 0:
							self.vpipCount[opponent_name] += 1
						self.callCount[opponent_name] += 1

					elif last_action_split[0] == CHECK:
						self.checkCount[opponent_name] += 1

					elif last_action_split[0] == FOLD:
						if received_packet['num_boardcards'] == 0:
							if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
								self.foldCountpFr[opponent_name] += 1
						self.foldCount[opponent_name] += 1
					
					# elif last_action_split[0] == SHOW:
						# self.showdownCount[opponent_name] += 1

			self.playerRaisedPreFlop = False
			self.playercBetBool = False
			self.opponentRaisedPreFlop = False
			self.playerSeenFlop = False
			self.pfrBoolean = {self.opp1_name : False, self.opp2_name : False}
	def getPostFlopWinPct(self):
		if self.postFlopCount > 0:
			self.postFlopWinPct[self.opp1_name] = float(self.postFlopWinCount[self.opp1_name]) / self.postFlopCount 
			self.postFlopWinPct[self.opp2_name] = float(self.postFlopWinCount[self.opp2_name]) / self.postFlopCount 

	def compileMatchStatistics(self, hand_id):
		self.totalNumHands = 0
		print "######## DEBUGGING PREFLOP STATISTICS ########"
		print "Player Name: ", self.myName
		print "Names of opponent: ", self.opp1_name, self.opp2_name
		print "Number of Hands Played: ", self.numHandsPlayed
		print "Player Raise Count: ", self.myRaiseCount
		print "Opponent Preflop Raise Count: ", self.pfrCount
		print "Opponent Preflop Fold Raise Count: ", self.foldCountpFr
		print "VPIP: ", self.vpipCount
		print "######## END DEBUG ########"

		print "Call Count: ", self.callCount
		print "Fold Count: ", self.foldCount
		print "Raise Count: ", self.raiseCount
		print "Bet Count: ", self.betCount
		print "Check Count: ", self.checkCount

		print "######### POST FLOP STATISTICS ##########"
		print "Continuation Bet: ", self.cbCount
		print "######### END POST FLOP STATS  ##########"

	def getPFR():
		pass

	def getPFRFold():
		pass

	def getAggressionPercent():
		#Raise + Bet/ Bets + Raise + Call + Check
		pass

	def getCheckRaise():
		pass

	def getShowdownPercent():
		pass


