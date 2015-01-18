import argparse
import sys
import socket

from util import packet_parse

RAISE = "RAISE"
CALL = "CALL"
FOLD = "FOLD"
CHECK = "CHECK"
BET = "BET"

class Statistician:

	def __init__(self):
		self.player_name = ""
		self.opp1_name = ""
		self.opp2_name = ""
		self.numHandsPlayed = {self.opp1_name : 0, self.opp2_name : 0}
		self.winCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Measure to see if they only play good hands
		self.instantFold = {self.opp1_name : 0, self.opp2_name : 0}
		# Pre-Flop Raise Count
		self.pfrCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.threeBCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.pfrFoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.bet3FoldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.callRaiseCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.myRaiseCount = 0

		# Post-Flop statistics below
		self.aggressionFactor = {self.opp1_name : 0, self.opp2_name : 0}
		self.raiseCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.betCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		self.callCountPost = {self.opp1_name : 0, self.opp2_name : 0}
		# How many times opp goes to showdown after the flop
		self.showdownCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.seenFlopCount = {self.opp1_name : 0, self.opp2_name : 0}
		# Continuation bet count
		self.cbCount = {self.opp1_name : 0, self.opp2_name : 0}
		# How often opponent makes another cont. bet after first one
		self.twocbCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldcbBets = {self.opp1_name : 0, self.opp2_name : 0}
		self.fold2cbBets = {self.opp1_name : 0, self.opp2_name : 0}
		self.foldCount = {self.opp1_name : 0, self.opp2_name : 0}
		self.checkCount = {self.opp1_name : 0, self.opp2_name : 0}

	# opponent_name is the name of the opponent
	# opponent_stats is a hash table containing the opponent's stats
	def getOpponentStatistics(self, opponent_name, opponent_stats):
		self.numHandsPlayed = opponent_stats['numHandsPlayed']
		self.winCount = opponent_stats['winCount']
		self.pfrCount = opponent_stats['pfrCount']

	def processPreflopStatistics(self, opponent_name, hand_statistics):
		for last_action in hand_statistics:
			split_action = last_action.split(":")

			if split_action[0] == RAISE and split_action[-1] == opponent_name:
				self.pfrCount[opponent_name] += 1

			elif split_action[0] == RAISE and split_action[-1] == self.player_name:
				self.myRaiseCount += 1

			elif split_action[0] == CALL and split_action[-1] == opponent_name and self.myRaiseCount > 0:
				self.callRaiseCount[opponent_name] += 1

		if self.myRaiseCount > 0 and self.callRaiseCount < self.myRaiseCount:
			self.pfrFoldCount += 1


	def processPostFlopStatistics(self, opponent_name, hand_statistics):
		pass


	# Update opponent statistics after each hand
	def updateOpponentStatistics(self, received_packet):
		self.player_name = received_packet['player_name']
		self.opp1_name = received_packet['opponent_1_name']
		self.opp2_name = received_packet['opponent_2_name']

		if received_packet['packet_name'] == "GETACTION":

			if received_packet['num_boardcards'] == 0:
				self.processPreflopStatistics(received_packet['last_action'])

			else:
				self.processPostFlopStatistics(received_packet['last_action'])


		else:







