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

class Statistician:

	def __init__(self):
		self.opp1_name = ""
		self.opp2_name = ""
		self.numHandsPlayed = {self.opp1_name : 0, self.opp2_name : 0}
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Measure to see if they only play good hands
		self.instantFold = {self.opp1_name : 0, self.opp2_name : 0}
		self.myRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Pre-Flop Raise Count of the opponents
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.twoBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}

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

	def processPreflopStatistics(self, opponent_name, hand_statistics):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[-1] == opponent_name:
				if split_action[0] == RAISE 
					self.pfrCount[opponent_name] += 1

				elif split_action[0] == CALL and self.myRaiseCount > 0:
					self.callRaiseCount[opponent_name] += 1
			
			else:
				if split_action[0] == RAISE:
					self.myRaiseCount[opponent_name] += 1

		if self.myRaiseCount[opponent_name] > 0 and self.pfrCount[opponent_name] > 0:
			self.threeBCount[opponent_name] += 1 

		elif self.myRaiseCount[opponent_name] == 1 and self.pfrCount[opponent_name] == 0:
			self.twoBCount[opponent_name] += 1

		elif self.myRaiseCount[opponent_name] > 0 and self.callRaiseCount[opponent_name] < self.myRaiseCount:
			self.pfrFoldCount[opponent_name] += 1

	def processPostFlopStatistics(self, opponent_name, hand_statistics):
		pass


	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet):
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics(self.opp1_name, received_packet['last_action'])
				self.processPreflopStatistics(self.opp2_name, received_packet['last_action'])

			else:
				self.processPostFlopStatistics(self.opp1_name, received_packet['last_action'])
				self.processPostFlopStatistics(self.opp2_name, received_packet['last_action'])

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







