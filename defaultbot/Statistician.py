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
		self.numHandsPlayed = {self.opp1_name : 0, self.opp2_name : 0}
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Measure to see if they only play good hands
		self.instantFold = {self.opp1_name : 0, self.opp2_name : 0}
		self.myRaiseCount = 0
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.twoBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrBoolean = {self.opp1_name: False, self.opp2_name: False}

		# Post-Flop statistics below
		self.checkRaise = {self.opp1_name : 0, self.opp2_name : 0}
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		# How often opponent makes another cont. bet after first one
		self.twocbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldcbBets = {self.opp1_name : 0, self.opp2_name : 0}
		# self.fold2cbBets = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}

	# opponent_name is the name of the opponent
	# opponent_stats is a hash table containing the opponent's stats
	def getOpponentStatistics(self, opponent_name, opponent_stats):
		self.winCount = opponent_stats['winCount']
		self.pfrCount = opponent_stats['pfrCount']

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

			if split_action[-1] in opponent_names:
				opponent_name = split_action[-1]

				if split_action[0] == CHECK:
					self.checkCount[opponent_name] += 1

				elif split_action[0] == RAISE:
					if self.pfrBoolean[opponent_name] and board_state == FLOP:
						self.cbCount[opponent_name] += 1
					self.raiseCountPost[opponent_name] += 1

				elif split_action[0] == CALL:
					self.callCountPost[opponent_name] += 1 

				elif split_action[0] == BET:
					self.betCountPost[opponent_name] += 1

				else:
					self.foldCount[opponent_name] += 1					

	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet):
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']

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
			hand_winner = winner_string.split(":")[-1]
			if hand_winner == self.opp1_name or hand_winner == self.opp2_name:
				self.winCount[hand_winner] += 1

			#Compute showdown Count
			for last_action in received_packet['last_action']:
				last_action_split = last_action.split(":")
				
				if last_action_split[0] == SHOW:
					self.showdownCount[last_action_split[-1]] += 1







