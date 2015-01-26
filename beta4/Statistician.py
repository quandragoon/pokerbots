import argparse
import sys
import socket
import pbots_calc

from util import packet_parse

RAISE = "RAISE"
CALL = "CALL"
FOLD = "FOLD"
CHECK = "CHECK"
BET = "BET"

SHOW = "SHOW"
PREFLOP = "PREFLOP"
FLOP = "FLOP"
TURN = "TURN"
RIVER = "RIVER"

WIN = "WIN"

FOLDED  = -1
INVALID = -1

DEAL = "DEAL"
POST = "POST"

I_TO_NUM_BC = {0 : 0, 1 : 3, 2 : 4, 3 : 5}

class Statistician:

	def __init__(self, myName, opp1, opp2):
		self.myName = myName
		# self.myStatus = True
		self.opp1_name = opp1
		self.opp2_name = opp2
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
		self.postFlopCount    = {self.opp1_name : 0, self.opp2_name : 0}
		self.postFlopWinPct   = {self.opp1_name : 0, self.opp2_name : 0}
		################# POST-FLOP WIN PERCENTAGE ####################
		# Post-Flop statistics below
		# True if we have gone to Flop, False Otherwise
		self.playerSeenFlop = False
		self.playerSeenTurn = False
		self.playerSeenRiver = False
		self.playerSeenShowdown = False
		# Determine how many times each opponent goes to Flop
		# self.aggressionPercent = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.twoPlayershowdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threePlayershowdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldcbBet = {self.opp1_name : 0, self.opp2_name : 0}
		self.playercBetBool = False
		# To compute Check-Raise
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountFlop = {self.opp1_name : 0, self.opp2_name : 0}
		# Average Hand Equity for each opponent
		# self.numActivePlayersPreflop = 0
		# self.numActivePlayersFlop = 0
		# self.numActivePlayersTurn = 0
		# self.numActivePlayersRiver = 0
		self.equity_table_2 = {}
		self.equity_table_3 = {}


		self.averageEquityTwo     = {self.opp1_name : {0 : 0.4, 3 : 0.5, 4 : 0.6, 5 : 0.7}, self.opp2_name : {0 : 0.4, 3 : 0.5, 4 : 0.6, 5 : 0.7}}
		self.averageEquityThree   = {self.opp1_name : {0 : 0.3, 3 : 0.4, 4 : 0.5, 5 : 0.6}, self.opp2_name : {0 : 0.3, 3 : 0.4, 4 : 0.5, 5 : 0.6}}

		self.minEquityTwo    = {self.opp1_name : {0:1, 3:1, 4:1, 5:1}, self.opp2_name : {0:1, 3:1, 4:1, 5:1}}
		self.minEquityThree  = {self.opp1_name : {0:1, 3:1, 4:1, 5:1}, self.opp2_name : {0:1, 3:1, 4:1, 5:1}}

		# ====== PERCENTAGES ==========
		self.foldPercentage = {self.opp1_name : 0, self.opp2_name : 0}
		self.aggressionPercent = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrPercent = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldPercent = {self.opp1_name : 0, self.opp2_name : 0}
		self.vpipPercent = {self.opp1_name : 0, self.opp2_name : 0}

		# Quan's code
		self.actionHistory = []
		self.numActivePlayersBeforeFold = {self.opp1_name : [], self.opp2_name : [], self.myName : []}
		self.handDict = {self.opp1_name : "", self.opp2_name : "", self.myName : ""}
		self.madeActionLastRound = {self.opp1_name : False, self.opp2_name : False, self.myName : False}
		self.alpha = 0.2



	def calculateEquityStat (self, name, hand, numActivePlayersBeforeFold, boardcards):
		for i in range(len(numActivePlayersBeforeFold)):
			numBc = I_TO_NUM_BC[i]
			if numActivePlayersBeforeFold[i] == 2:
				eq = 0
				if numBc == 0:
					eq = self.equity_table_2[hand]
				else:
					eq = pbots_calc.calc(':'.join([hand, 'xx']), ''.join(boardcards[:numBc]), "", 1000).ev[0]
				self.minEquityTwo[name][numBc] = min(eq, self.minEquityTwo[name][numBc])
				self.averageEquityTwo[name][numBc] = self.alpha * eq + (1 - self.alpha) * self.averageEquityTwo[name][numBc]
			elif numActivePlayersBeforeFold[i] == 3:
				eq = 0
				if i == 0:
					eq = self.equity_table_3[hand]
				else:
					eq = pbots_calc.calc(':'.join([hand, 'xx', 'xx']), ''.join(boardcards[:numBc]), "", 1000).ev[0]
				self.minEquityThree[name][numBc] = min(eq, self.minEquityThree[name][numBc])
				self.averageEquityThree[name][numBc] = self.alpha * eq + (1 - self.alpha) * self.averageEquityThree[name][numBc]



	def recordActions (self, last_actions):
		self.actionHistory.extend(last_actions)
		print "====> History: " + repr(self.actionHistory)


	def getNumActivePlayers(self, num_active):
		self.numActivePlayersPreflop = num_active



	def updateHandCount(self, name, hand_id):
		self.numHandsPlayed[name] = hand_id






	# Update opponent statistics after each hand
	# playerAction is the most recent action that our player took
	def updateOpponentStatistics(self, received_packet, hand_id, num_active_players):		


		# if received_packet['packet_name'] == "GETACTION":

		# 	if received_packet['num_boardcards'] == 0:
		# 		self.processPreflopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], playerAction)

		# 	else:
		# 		state = ""
		# 		if received_packet['num_boardcards'] == 3:
		# 			state = FLOP
		# 		elif received_packet['num_boardcards'] == 4:
		# 			state = TURN
		# 		else:
		# 			state =  RIVER
		# 		self.processPostFlopStatistics([self.opp1_name, self.opp2_name], received_packet['last_action'], state)

		# HANDOVER
		# else:


		# This function is now only called after hand is over

		#############################################################################
		self.actionHistory.extend(received_packet['last_action'])
		print "====> History: " + repr(self.actionHistory)

		numActivePlayers = num_active_players
		boardState = PREFLOP 
		pfrBoolean = {self.opp1_name : False, self.opp2_name : False}

		for act in self.actionHistory:
			act_split = act.split(":")

			if act_split[0] == FOLD:
				numActivePlayers -= 1
				self.numActivePlayersBeforeFold[act_split[-1]].append(FOLDED)
				if act_split[-1] != self.myName: 
					if boardState == PREFLOP:
						self.foldCountpFr[act_split[-1]] += 1
					self.foldCount[act_split[-1]] += 1

			elif act_split[0] == DEAL: 
				boardState = act_split[1]
				prev_index =  self.actionHistory.index(act) - 1
				action_before = (self.actionHistory[prev_index].split(":"))[0]
				action_before_before = (self.actionHistory[prev_index - 1].split(":"))[0]
				# if nigga has two consecutive deals
				if action_before == DEAL or action_before == CHECK or action_before_before == CHECK:
					for name in self.numActivePlayersBeforeFold:
						self.numActivePlayersBeforeFold[name].append(INVALID)
				else:
					for name in self.numActivePlayersBeforeFold:
						if self.numActivePlayersBeforeFold[name] == [] or self.numActivePlayersBeforeFold[name][-1] != FOLDED:
							if self.madeActionLastRound[name]:
								self.numActivePlayersBeforeFold[name].append(numActivePlayers)
							else:
								self.numActivePlayersBeforeFold[name].append(INVALID)
						else:
							self.numActivePlayersBeforeFold[name].append(FOLDED)
				self.madeActionLastRound = {self.opp1_name : False, self.opp2_name : False, self.myName : False}

			elif act_split[0] == SHOW:
				name = act_split[-1]
				if self.numActivePlayersBeforeFold[name] == [] or self.numActivePlayersBeforeFold[name][-1] != FOLDED:
					self.numActivePlayersBeforeFold[name].append(numActivePlayers)
				else:
					self.numActivePlayersBeforeFold[name].append(FOLDED)
				self.handDict[act_split[-1]] = act_split[1] + act_split[2]

			elif act_split[0] == RAISE:
				if act_split[-1] != self.myName:
					self.raiseCount[act_split[-1]] += 1
					if boardState == PREFLOP:
						self.pfrCount[act_split[-1]] += 1
						pfrBoolean[act_split[-1]] = True

			elif act_split[0] == BET:
				if act_split[-1] != self.myName:
					self.betCount[act_split[-1]] += 1

			elif act_split[0] == CALL:
				if act_split[-1] != self.myName: 
					self.callCount[act_split[-1]] += 1

			elif act_split[0] == CHECK:
				if act_split[-1] != self.myName:
					self.checkCount[act_split[-1]] += 1

			elif act_split[0] == CHECK:
				if act_split[-1] != self.myName:
					self.checkCount[opponent_name] += 1 

			elif act_split[0] == WIN:
				winner = act_split[-1]
				win_amount = int(act_split[-2])
				if boardState != PREFLOP:
					if winner != self.myName:
						self.postFlopCount[winner] += 1
						self.postFlopWinCount[winner] += 1


			if act_split[0] in [POST, CALL, BET, RAISE, CHECK, FOLD]:
				self.madeActionLastRound[act_split[-1]] = True

		# Compute equity
		for name in self.numActivePlayersBeforeFold:
			if name != self.myName:
				if len(self.numActivePlayersBeforeFold[name]) == 4 and self.numActivePlayersBeforeFold[name][-1] != FOLDED:
					print "NIG NAME: " + name
					self.calculateEquityStat(name, self.handDict[name], self.numActivePlayersBeforeFold[name], received_packet['boardcards'])


		print "====> SHITs  : " + repr(self.numActivePlayersBeforeFold)
		print "====> MIN_2  : " + repr(self.minEquityTwo) 
		print "====> MIN_3  : " + repr(self.minEquityThree) 
		print "====> AVG_2  : " + repr(self.averageEquityTwo) 
		print "====> AVG_3  : " + repr(self.averageEquityThree) 
		self.actionHistory = []
		self.numActivePlayersBeforeFold = {self.opp1_name : [], self.opp2_name : [], self.myName : []}
		#############################################################################



			# for last_action in received_packet['last_action'][::-1]:
			# 	last_action_split = last_action.split(":")
			# 	if (last_action_split[0] == SHOW and last_action_split[-1] == self.myName):
			# 		self.playerSeenShowdown = True
			
			# if (not self.playerSeenFlop):	
			# 	self.numActivePlayersPreflop -= 1
			# 	print "FOLD PREFLOP IF PLAYER INACTIVE"
			
			# elif (not self.playerSeenTurn):
			# 	self.numActivePlayersFlop -= 1
			# 	print "FOLD FLOP IF PLAYER INACTIVE"
			
			# elif (not self.playerSeenRiver):
			# 	self.numActivePlayersTurn -= 1
			# 	print "FOLD TURN IF PLAYER INACTIVE"

			# elif (not self.playerSeenShowdown and self.playerSeenRiver):
			# 	self.numActivePlayersRiver -= 1
			# 	print "FOLD RIVER IF PLAYER INACTIVE"

			# self.numActivePlayersFlop = self.numActivePlayersPreflop
			# self.numActivePlayersTurn = self.numActivePlayersFlop
			# self.numActivePlayersRiver = self.numActivePlayersTurn

			# flop_index = 0
			# If my player folds preflop from the button and the hand
			# goes into or past the flop, the code below tracks statistics for
			# active opponent
			# if (not self.playerSeenFlop and received_packet['num_boardcards'] >= 3):
			# 	for index in range(len(received_packet['last_action'])):
			# 		last_action = received_packet['last_action'][index]
			# 		split_action = last_action.split(":")
			# 		if split_action[0] == "DEAL" and split_action[-1] == FLOP:
			# 			flop_index = index
			# 			break
			# 	for last_action in received_packet['last_action'][:flop_index]:
			# 		last_action_split = last_action.split(":")

			# 		if (last_action_split[-1] == self.opp1_name or last_action_split[-1] == self.opp2_name):
			# 			opponent_name = last_action_split[-1]

			# 			if last_action_split[0] == RAISE:
			# 				self.pfrCount[opponent_name] += 1
			# 				self.raiseCount[opponent_name] += 1
			# 				self.pfrBoolean[opponent_name] = True

						# elif last_action_split[0] == CALL:
						# 	self.callCount[opponent_name] += 1

						# elif last_action_split[0] == CHECK:
						# 	self.checkCount[opponent_name] += 1

			# winner_string = received_packet['last_action'][-1]
			# winner_string_split = winner_string.split(":")
			# if winner_string_split[0] == WIN:
			# 	hand_winner = winner_string_split[-1]
			# 	winning_amount = int(winner_string_split[-2])

			# 	if received_packet['num_boardcards'] >= 3:
			# 		if hand_winner != self.myName:
			# 			self.postFlopCount += 1
			# 			self.postFlopWinCount[hand_winner] += 1

				# if winning_amount > 10:
				# 	if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
				# 		self.winCount[hand_winner] += 1
				# 	else:
				# 		self.myWinCount += 1

			# for last_action in received_packet['last_action'][flop_index:]:
			# 	last_action_split = last_action.split(":")

			# 	if (last_action_split[-1] == self.opp1_name or last_action_split[-1] == self.opp2_name):
			# 		opponent_name = last_action_split[-1]

			# 		if last_action_split[0] == RAISE:
			# 			if received_packet['num_boardcards'] == 0:
			# 				self.opponentRaisedPreFlop = True
			# 			elif received_packet['num_boardcards'] == 3:
			# 				if self.pfrBoolean[opponent_name]:
			# 					self.cbCount[opponent_name] += 1
			# 			self.raiseCount[opponent_name] += 1

					# elif last_action_split[0] == BET:
					# 	if received_packet['num_boardcards'] == 3:
					# 		if self.pfrBoolean[opponent_name]:
					# 			self.cbCount[opponent_name] += 1
					# 	self.betCount[opponent_name] += 1

					# elif last_action_split[0] == CALL:
					# 	self.callCount[opponent_name] += 1

					# elif last_action_split[0] == CHECK:
					# 	self.checkCount[opponent_name] += 1

					# elif last_action_split[0] == FOLD:
					# 	if received_packet['num_boardcards'] == 0:
					# 		if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
					# 			self.foldCountpFr[opponent_name] += 1
					# 	self.foldCount[opponent_name] += 1
					
					# elif last_action_split[0] == SHOW:
					# 	print "## DEBUG 1: " + str(self.numActivePlayersRiver)
					# 	print "## Showdown dict ", self.twoPlayershowdownCount, self.threePlayershowdownCount
					# 	if self.numActivePlayersRiver == 2:
					# 		print "DEBUG 2 Player"
					# 		self.twoPlayershowdownCount[opponent_name] += 1
					# 	else:
					# 		print "DEBUG 3 Player"
					# 		self.threePlayershowdownCount[opponent_name] += 1
						
						# hand = last_action_split[1] + last_action_split[2]
						# boardcards = received_packet['boardcards']
						# if opponent_name == self.opp1_name:
						# 	self.calculateAvgEquityP1(opponent_name, hand, self.numActivePlayersPreflop, [])
						# 	self.calculateAvgEquityP1(opponent_name, hand, self.numActivePlayersFlop, boardcards[0:3])
						# 	self.calculateAvgEquityP1(opponent_name, hand, self.numActivePlayersTurn, boardcards[0:4])
						# 	self.calculateAvgEquityP1(opponent_name, hand, self.numActivePlayersRiver, boardcards)
						# 	self.calculateMinEquityP1(opponent_name, hand, self.numActivePlayersPreflop, [])
						# 	self.calculateMinEquityP1(opponent_name, hand, self.numActivePlayersFlop, boardcards[0:3])
						# 	self.calculateMinEquityP1(opponent_name, hand, self.numActivePlayersTurn, boardcards[0:4])
						# 	self.calculateMinEquityP1(opponent_name, hand, self.numActivePlayersRiver, boardcards)
						# elif opponent_name == self.opp2_name:
						# 	self.calculateAvgEquityP2(opponent_name, hand, self.numActivePlayersPreflop, [])
						# 	self.calculateAvgEquityP2(opponent_name, hand, self.numActivePlayersFlop, boardcards[0:3])
						# 	self.calculateAvgEquityP2(opponent_name, hand, self.numActivePlayersTurn, boardcards[0:4])
						# 	self.calculateAvgEquityP2(opponent_name, hand, self.numActivePlayersRiver, boardcards)
						# 	self.calculateMinEquityP2(opponent_name, hand, self.numActivePlayersPreflop, [])
						# 	self.calculateMinEquityP2(opponent_name, hand, self.numActivePlayersFlop, boardcards[0:3])
						# 	self.calculateMinEquityP2(opponent_name, hand, self.numActivePlayersTurn, boardcards[0:4])
						# 	self.calculateMinEquityP2(opponent_name, hand, self.numActivePlayersRiver, boardcards)
				
			# self.playerRaisedPreFlop = False
			# self.playercBetBool = False
			# self.opponentRaisedPreFlop = False
			# self.playerSeenFlop = False
			# self.playerSeenTurn = False
			# self.playerSeenRiver = False
			# self.playerSeenShowdown = False
			# self.pfrBoolean = {self.opp1_name : False, self.opp2_name : False}
			# self.numActivePlayersPreflop = 0
			# self.numActivePlayersFlop = 0
			# self.numActivePlayersTurn = 0
			# self.numActivePlayersRiver = 0

	def getPostFlopWinPct(self):
		if self.postFlopCount[self.opp1_name] > 0:
			self.postFlopWinPct[self.opp1_name] = float(self.postFlopWinCount[self.opp1_name]) / self.postFlopCount[self.opp1_name]
		if self.postFlopCount[self.opp2_name] > 0:
			self.postFlopWinPct[self.opp2_name] = float(self.postFlopWinCount[self.opp2_name]) / self.postFlopCount[self.opp2_name]

	def compileMatchStatistics(self, hand_id):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			if self.numHandsPlayed[opponent_name] == 0:
				self.numHandsPlayed[opponent_name] = hand_id

		self.getPFR()
		self.getPFRFold()
		self.getFoldPercent()
		self.getAggressionPercent()
		self.getVPIPPercent()

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
		print "Showdown Count (2 player): ", self.twoPlayershowdownCount
		print "Showdown Count (3 player): ", self.threePlayershowdownCount
		# print "Continuation Bet: ", self.cbCount
		print "FOLD PERCENTAGE: ", self.foldPercentage
		print "PREFLOP FOLD PERCENTAGE: ", self.pfrFoldPercent
		print "VPIP PERCENTAGE: ", self.vpipPercent
		print "AGGRESSION PERCENT: ", self.aggressionPercent
		print "PREFLOP RAISE PERCENT: ", self.pfrPercent		
		print "######### END POST FLOP STATS  ##########"

	def getPrecomputedHashtables(self, equity_table_2, equity_table_3):
		self.equity_table_2 = equity_table_2
		self.equity_table_3 = equity_table_3

	def getPFR(self):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			self.pfrPercent[opponent_name] = float(self.pfrCount[opponent_name])/ self.numHandsPlayed[opponent_name]

	def getPFRFold(self):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			self.pfrFoldPercent[opponent_name] = float(self.foldCountpFr[opponent_name]) / self.numHandsPlayed[opponent_name]

	def getFoldPercent(self):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			self.foldPercentage[opponent_name] = float(self.foldCount[opponent_name]) / self.numHandsPlayed[opponent_name]

	def getAggressionPercent(self):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			self.aggressionPercent[opponent_name] = float(self.raiseCount[opponent_name] + self.betCount[opponent_name]) / (self.raiseCount[opponent_name] + self.betCount[opponent_name] + self.callCount[opponent_name] + self.checkCount[opponent_name] + self.foldCount[opponent_name])

	def getVPIPPercent(self):
		for opponent_name in [self.opp1_name, self.opp2_name]:
			self.vpipPercent[opponent_name] = self.vpipCount[opponent_name] / self.numHandsPlayed[opponent_name]
	






	# def processPreflopStatistics(self, opponent_names, hand_statistics, playerAction):
	# 	if playerAction.split(":")[0] == RAISE:
	# 		self.myRaiseCount += 1
	# 		self.playerRaisedPreFlop = True

	# 	for last_action in hand_statistics:
	# 		split_action = last_action.split(":")

	# 		if split_action[-1] in opponent_names:
	# 			opponent_name = split_action[-1]

	# 			if split_action[0] == RAISE: 
	# 				self.pfrCount[opponent_name] += 1
	# 				self.vpipCount[opponent_name] += 1
	# 				self.raiseCount[opponent_name] += 1
	# 				self.pfrBoolean[opponent_name] = True
	# 				self.opponentRaisedPreFlop = True

	# 			elif split_action[0] == CALL:
	# 				self.callCount[opponent_name] += 1
	# 				self.vpipCount[opponent_name] += 1

	# 			elif split_action[0] == FOLD:
	# 				if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
	# 					self.foldCountpFr[opponent_name] += 1
	# 				self.foldCount[opponent_name] += 1
	# 				self.numActivePlayersPreflop -= 1
	# 				print "FOLD PREFLOP OPP FOLD"

	# 			elif split_action[0] == CHECK:
	# 				self.checkCount[opponent_name] += 1



	# def processPostFlopStatistics(self, opponent_names, hand_statistics, board_state):
	# 	flop_index = 0
	# 	if board_state == FLOP:
	# 		self.playerSeenFlop = True
	# 		for index in range(len(hand_statistics)):
	# 			split_action = hand_statistics[index].split(":")
	# 			if split_action[0] == "DEAL":
	# 				flop_index = index

	# 		# Computing any Preflop Stats that we missed in the above function
	# 		# that occured after we had already made our move
	# 		for last_action in hand_statistics[:flop_index]:
	# 			split_action = last_action.split(":")

	# 			if split_action[-1] in opponent_names:
	# 				opponent_name = split_action[-1]

	# 				if split_action[0] == CALL:
	# 					self.callCount[opponent_name] += 1
	# 					self.vpipCount[opponent_name] += 1

	# 				elif split_action[0] == FOLD:
	# 					if (self.playerRaisedPreFlop or self.opponentRaisedPreFlop):
	# 						self.foldCountpFr[opponent_name] += 1
	# 					self.foldCount[opponent_name] += 1
	# 					self.numActivePlayersPreflop -= 1
	# 					print "FOLD PREFLOP OPP FOLD"

	# 				elif split_action[0] == CHECK:
	# 					self.checkCount[opponent_name] += 1
		
	# 	elif board_state == TURN:
	# 		self.playerSeenTurn = True

	# 	elif board_state == RIVER:
	# 		self.playerSeenRiver = True

	# 	self.numActivePlayersFlop = self.numActivePlayersPreflop
		
	# 	# Post Flop Statistics begins here
	# 	for last_action in hand_statistics[flop_index:]:
	# 		split_action = last_action.split(":")

	# 		if board_state == FLOP:
	# 			if (split_action[-1] == self.myName and split_action[0] == RAISE and self.playerRaisedPreFlop):
	# 				self.playercBetBool = True

	# 		#Count Opponent Statistics
	# 		if split_action[-1] in opponent_names:
	# 			opponent_name = split_action[-1]

	# 			if split_action[0] == CHECK:
	# 				if board_state == FLOP:
	# 					self.checkCountFlop[opponent_name] += 1
	# 				self.checkCount[opponent_name] += 1

	# 			elif split_action[0] == RAISE:
	# 				if self.pfrBoolean[opponent_name] and board_state == FLOP:
	# 					self.cbCount[opponent_name] += 1
	# 					self.raiseCountFlop[opponent_name] += 1
	# 				self.raiseCount[opponent_name] += 1

	# 			elif split_action[0] == CALL:
	# 				self.callCount[opponent_name] += 1 

	# 			elif split_action[0] == BET:
	# 				if self.pfrBoolean[opponent_name] and board_state == FLOP:
	# 					self.cbCount[opponent_name] += 1
	# 				self.betCount[opponent_name] += 1

	# 			elif split_action[0] == FOLD:
	# 				if self.playercBetBool:
	# 					self.foldcbBet[opponent_name] += 1
	# 				self.foldCount[opponent_name] += 1
	# 				if board_state == FLOP:
	# 					self.numActivePlayersFlop -= 1
	# 					print "FOLD FLOP IF OPP FOLD"
	# 				self.numActivePlayersTurn = self.numActivePlayersFlop
	# 				if board_state == TURN:
	# 					self.playerSeenTurn = True
	# 					self.numActivePlayersTurn -= 1
	# 					print "FOLD TURN IF OPP FOLD"
	# 				self.numActivePlayersRiver = self.numActivePlayersTurn
	# 				if board_state == RIVER:
	# 					self.playerSeenRiver = True
	# 					self.numActivePlayersRiver -= 1
	# 					print "FOLD RIVER IF OPP FOLD"

	# 	for opp_name in opponent_names:
	# 		if (board_state == FLOP and (self.checkCountFlop[opp_name] == self.raiseCountFlop[opp_name])):
	# 			self.checkRaise[opp_name] += 1





