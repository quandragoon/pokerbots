import argparse
import socket
import sys
import pbots_calc
import random
import Statistician
from Statistician import *


from util import packet_parse
"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""

# Actions
RAISE = "RAISE"
BET   = "BET"
FOLD  = "FOLD"
CALL  = "CALL"
CHECK = "CHECK"
DEAL  = "DEAL"


# Statuses
FOLDED = 0
OUT    = 1
ACTIVE = 2 


# suits
SPADE   = "s"
CLUB    = "c"
DIAMOND = "d"
HEART   = "h"

# Hand Positions
BUTTON = "BUTTON"
SB = "SMALL BLIND"
BB = "BIG BLIND"


SLOW_PLAY_AMOUNT = 5
LOTS_OF_CHIPS    = 400
SUFFICIENT_CHIPS = 50

# equity threshold
THREE_FOLD_THRES_TABLE  = {0 : 0.38, 3 : 0.25, 4 : 0.25, 5 : 0.4}
THREE_RAISE_THRES_TABLE = {0 : 0.45, 3 : 0.7,  4 : 0.7,  5 : 0.7}
TWO_FOLD_THRES_TABLE    = {0 : 0.53, 3 : 0.35, 4 : 0.3,  5 : 0.5}
TWO_RAISE_THRES_TABLE   = {0 : 0.65, 3 : 0.75, 4 : 0.75, 5 : 0.78}

BET_SMALL_LIKELIHOOD = {0 : 150, 3 : 130, 4 : 100, 5 : 80}


POWER = 4

# KEYVALUE Packet Parsing
FOLD_PERCENT = 9
AGGR_PERCENT = 8

MONTE_CARLO_ITER = 30000
MAX_ITER         = 120000
DELTA_ITER       = 5000
# BITCH_FACTOR_TABLE = {0 : 0.75, 3 : 0.8, 4 : 0.9, 5 : 1}
TWO_IN_BITCH_FACTOR_TABLE   = {0 : 0.99, 3 : 1, 4 : 1.1,  5 : 1.2}
THREE_IN_BITCH_FACTOR_TABLE = {0 : 0.99, 3 : 1, 4 : 1.05, 5 : 1.1}

# Hand position table
POSITION_TWO   = {1: SB, 2:BB , 3: OUT}
POSITION_THREE = {1: BUTTON, 2: SB, 3: BB}

TOLERANCE_FOR_LA = 0.1

FIRST_PRIZE  = 180
SECOND_PRIZE = 60
THIRD_PRIZE  = 0

FACE_CARDS = ["A", "K", "Q", "J"]

# ICM Helper function
def calc_icm (a, b, c):

    s = float(a + b + c + 0.01)

    '''
    All cases in which two or more players are all-in 
    are now handled in the should_call() method.

    '''

    pa1 = a/s
    pb1 = b/s
    pc1 = c/s
    
    pa2 = pb1 * (a/(s-b)) + pc1 * (a/(s-c))
    pb2 = pa1 * (b/(s-a)) + pc1 * (b/(s-c))
    pc2 = pa1 * (c/(s-a)) + pb1 * (c/(s-b))

    ewa = pa1 * FIRST_PRIZE + pa2 * SECOND_PRIZE
    ewb = pb1 * FIRST_PRIZE + pb2 * SECOND_PRIZE
    ewc = pc1 * FIRST_PRIZE + pc2 * SECOND_PRIZE

    return (ewa, ewb, ewc)



# class Card:
#     def __init__ (self, string_form):
#         self.denom = string_form[0]
#         self.suit  = string_form[1]
#         self.value = 

# class Hand:
#     def __init__ (self, string_form):
#         self.hand



class Opponent:
    def __init__ (self, name):
        self.seat        = 0 # 0, 1, 2
        self.handPosition = None
        self.playerType  = TYPE_NEU
        self.name        = name
        self.stack_size  = 200
        self.status      = ACTIVE
        self.last_action = None
        self.original_stacksize = 200




class Player:

    def __init__ (self):
        self.time_low_thres         = 0.0
        self.time_bank              = 0.0
        self.time_per_hand          = 0.0
        self.my_name                = ""
        self.opponent_1_name        = ""
        self.opponent_2_name        = ""
        self.hasPlayed_opponent_1   = False
        self.hasPlayed_opponent_2   = False
        self.my_hand                = ""
        self.my_stacksize           = 0
        self.list_of_stacksizes     = []
        self.hand_id                = 0
        self.num_active_players     = 0
        self.list_of_active_players = []
        self.history_storage        = {}
        self.minBet                 = 0
        self.maxBet                 = 0
        self.minRaise               = 0
        self.maxRaise               = 0
        self.my_original_stacksize  = 0
        self.alpha                  = 0.5 # how agressive we are
        self.fold_thres             = 0
        self.opp_fold_thres         = 0
        self.raise_thres            = 0
        self.highestRaiseAmtThisRnd = 0
        self.call_amount            = 0
        self.inc_call_amount        = 0
        self.is_new_round           = True
        self.last_action            = None
        self.num_boardcards         = -1
        self.boardcards             = []
        self.foundFaceCard          = False
        self.my_seat                = 1
        self.potsize                = 0
        self.opp_dict               = {}
        self.STATS                  = None
        self.monte_carlo_iter       = MONTE_CARLO_ITER
        self.one_folded             = False
        self.guy_active             = ""
        self.handPosition           = None
        self.opp1_skill             = 0.5
        self.opp2_skill             = 0.5
        self.isPreflop              = True
        self.bigBlind               = 2
        self.lastRaiser             = None
        self.oppCheckedThisRound    = False
        self.already_set_new_time   = False
        self.hasPlayed              = {}
        # boss-ass hands
        self.boss_class1            = ['AsAh', 'AsAd', 'AsAc', 'AhAs', 
                                       'AhAd', 'AhAc', 'AdAs', 'AdAh', 
                                       'AdAc', 'AcAs', 'AcAh', 'AcAd', 
                                       'KsKh', 'KsKd', 'KsKc', 'KhKs', 
                                       'KhKd', 'KhKc', 'KdKs', 'KdKh', 
                                       'KdKc', 'KcKs', 'KcKh', 'KcKd', 
                                       'QsQh', 'QsQd', 'QsQc', 'QhQs', 
                                       'QhQd', 'QhQc', 'QdQs', 'QdQh', 
                                       'QdQc', 'QcQs', 'QcQh', 'QcQd', 
                                       'JsJh', 'JsJd', 'JsJc', 'JhJs', 
                                       'JhJd', 'JhJc', 'JdJs', 'JdJh', 
                                       'JdJc', 'JcJs', 'JcJh', 'JcJd', 
                                       'TsTh', 'TsTd', 'TsTc', 'ThTs', 
                                       'ThTd', 'ThTc', 'TdTs', 'TdTh', 
                                       'TdTc', 'TcTs', 'TcTh', 'TcTd'] 
                                       

        self.boss_class2            = ['AsKs', 'KsAs', 'AhKh', 'KhAh', 
                                       'AdKd', 'KdAd', 'AcKc', 'KcAc',
                                       'AsQs', 'QsAs', 'AhQh', 'QhAh', 
                                       'AdQd', 'QdAd', 'AcQc', 'QcAc', 
                                       'AsJs', 'JsAs', 'AhJh', 'JhAh', 
                                       'AdJd', 'JdAd', 'AcJc', 'JcAc', 
                                       '9s9h', '9s9d', '9s9c', '9h9s', 
                                       '9h9d', '9h9c', '9d9s', '9d9h', 
                                       '9d9c', '9c9s', '9c9h', '9c9d', 
                                       '8s8h', '8s8d', '8s8c', '8h8s', 
                                       '8h8d', '8h8c', '8d8s', '8d8h', 
                                       '8d8c', '8c8s', '8c8h', '8c8d']



        # precomputed equity tables for pre flop
        self.equity_table_2         = {}
        self.equity_table_3         = {}
        with open("precomputed2.txt") as f:
            for line in f:
                (key, val) = line.split()
                self.equity_table_2[key] = float(val)
        with open("precomputed3.txt") as f:
            for line in f:
                (key, val) = line.split()
                self.equity_table_3[key] = float(val)



    def makeBet(self, amount):
        return int(max(self.minBet, min(amount, self.maxBet)))


    def makeRaise(self, amount):
        return int(max(self.minRaise, min(amount, self.maxRaise)))


    def faceCardOnTable(self, boardcards):
        if len(boardcards) > 0:
            for card in boardcards:
                if card[0] in FACE_CARDS:
                    self.foundFaceCard = True
        return self.foundFaceCard


    def keyval_handler(self, received_packet):
        self.history_storage[received_packet['key']] = eval(received_packet['value'])

    def newgame_handler(self, received_packet):

        self.opponent_1_name = received_packet['opponent_1_name']
        self.opponent_2_name = received_packet['opponent_2_name']

        self.my_name = received_packet['player_name']

        self.bigBlind = received_packet['big_blind']


        self.opp_dict[self.opponent_1_name] = Opponent(self.opponent_1_name)
        self.opp_dict[self.opponent_2_name] = Opponent(self.opponent_2_name)

        self.time_bank       = float(received_packet['timeBank'])
        self.time_low_thres  = 0.05 * self.time_bank
        self.time_per_hand   = self.time_bank / received_packet['num_hands']  


        # If we have already played the opponent before, 
        # we load their statistics from the previous encounter
        # for this game. NOTE that Historian is just an instance of the Statistician/Historian class
        # that is not yet created. 
        self.hasPlayed = {self.opponent_1_name: False, self.opponent_2_name: False}       
        for opponent_name in [self.opponent_1_name, self.opponent_2_name]:
            if opponent_name in self.history_storage:
                self.hasPlayed[opponent_name] = True




    def newhand_handler(self, received_packet):
        
        self.my_hand = received_packet['hand']
        self.my_seat = received_packet['seat']
        self.list_of_stacksizes = received_packet['stack_size']
        self.my_original_stacksize = self.list_of_stacksizes[self.my_seat - 1]
        self.hand_id = received_packet['handID']
        self.num_active_players = received_packet['num_active_players']
        if self.num_active_players == 2:
            self.handPosition = POSITION_TWO[self.my_seat]
        else:
            self.handPosition = POSITION_THREE[self.my_seat]

        ###############################################################################################
        # see if we STATS has been initialized
        if self.STATS == None:
            self.STATS = Statistician(self.my_name, self.opponent_1_name, self.opponent_2_name)
            self.STATS.getPrecomputedHashtables(self.equity_table_2, self.equity_table_3) 
            for opponent_name in [self.opponent_1_name, self.opponent_2_name]:
                if self.hasPlayed[opponent_name]:
                    self.STATS.loadDataFromHistoryStorage(self.history_storage, opponent_name)
            # self.STATS.loadDataFromHistoryStorage(self.history_storage)
            self.STATS.setBigBlind(self.bigBlind)
            print "===> STORAGE: " + str (self.history_storage)

        self.STATS.getNumActivePlayers(self.num_active_players)
        ###############################################################################################

        self.list_of_active_players = received_packet['active_players']

        # adjust iterations
        new_time_bank = float(received_packet['timeBank'])
        if new_time_bank < self.time_low_thres and self.already_set_new_time == False:
            self.time_per_hand = self.time_per_hand / 2
            self.already_set_new_time = True
        delta_time = self.time_bank - new_time_bank 
        if delta_time > self.time_per_hand:
            self.monte_carlo_iter = max(self.monte_carlo_iter - DELTA_ITER, DELTA_ITER)
        else:
            self.monte_carlo_iter = min(self.monte_carlo_iter + DELTA_ITER, MAX_ITER)

        self.time_bank = new_time_bank

        # print "ITER : " + str(self.monte_carlo_iter)
        # print "DELTA: " + str(delta_time)

        self.one_folded = False

        names = received_packet['player_names']
        for i in range(len(names)):
            name = names[i]
            if name != self.my_name:
                self.opp_dict[name].playerType = self.STATS.getPlayerType(name)
                self.opp_dict[name].seat = i 
                if self.num_active_players == 2:
                    self.opp_dict[name].handPosition = POSITION_TWO[i+1]
                else:
                    self.opp_dict[name].handPosition = POSITION_THREE[i+1]
                self.opp_dict[name].stack_size = self.list_of_stacksizes[i]
                self.opp_dict[name].original_stacksize = self.list_of_stacksizes[i]
                # update status
                if (self.opp_dict[name].stack_size == 0 and self.opp_dict[name].status != OUT):
                    self.opp_dict[name].status = OUT
                    ###############################################################################################
                    # self.STATS.updateHandCount(name, self.hand_id - 1)
                    ###############################################################################################
                else:
                    self.opp_dict[name].status = ACTIVE

        winPercA = self.STATS.getPostFlopWinPct(self.opponent_1_name)
        winPercB = self.STATS.getPostFlopWinPct(self.opponent_2_name)

        self.opp1_skill = winPercA / (winPercA + winPercB)
        self.opp2_skill = 1 - self.opp1_skill


    def bet_handler(self, winning_factor):
        a = random.random()
        bet_amount = 0

        # slow play
        if self.num_boardcards == 0:
            winning_factor = min(1, winning_factor)
        elif self.num_boardcards == 3:
            winning_factor = min(0.5, 0.75*winning_factor)
        elif self.num_boardcards == 4:
            winning_factor = min(0.5, winning_factor)

        if self.alpha > a: # YOLO
            r = random.random()
            if winning_factor > r:
                bet_amount = self.my_stacksize 

        else: # EBOLO
            bet_amount = self.my_stacksize * winning_factor  

        amountBet = self.makeBet(bet_amount)
        self.highestRaiseAmtThisRnd = amountBet
        return amountBet
        # s.send(BET + ':' + str(self.makeBet(bet_amount)) + '\n')





    def raise_handler(self, winning_factor):
        a = random.random()
        raise_amount = 0

        if self.alpha > a: # YOLO
            r = random.random()
            if winning_factor > r:
                raise_amount = self.my_stacksize 

        else: # EBOLO
            raise_amount = self.my_stacksize * winning_factor  

        amountRaise = self.makeRaise(raise_amount)
        self.highestRaiseAmtThisRnd = amountRaise
        return amountRaise
        # s.send(RAISE + ':' + str(self.makeRaise(raise_amount)) + '\n')






    def should_call_no_stats (self, equity):
        fold_ew      = 0
        call_win_ew  = 0
        call_lose_ew = 0

        if self.call_amount < SLOW_PLAY_AMOUNT:
            return True 

        # should call before the flop
        if self.num_boardcards == 0 and self.potsize <= 6:
            return True

        bitch_factor = 1    

        # check if one is out
        guy_active = ""
        guy_folded = ""

        if self.num_active_players == 2: #heads-up
            guy_active = self.guy_active

            other_guy_stacksize = self.opp_dict[guy_active].original_stacksize

            # if other_guy_stacksize <= 0.05*self.my_original_stacksize:
            #     "$$$ THIS IS PROB NEVER TRUE"
            #     return True

            # else:
            bitch_factor = TWO_IN_BITCH_FACTOR_TABLE[self.num_boardcards]
            fold_chips = self.my_stacksize
            call_lose_chips = self.my_stacksize - self.inc_call_amount
            call_win_chips = self.my_stacksize + self.potsize
            # print "FOLD CHIPS: " + str(fold_chips * bitch_factor)
            # print "EXP CHIPS : " + str(call_lose_chips*(1-equity) + call_win_chips*equity)
            lhs = fold_chips * bitch_factor
            rhs = call_lose_chips*(1-equity) + call_win_chips*equity
            return lhs < rhs

        else: # all three players have chips
            opp_names = self.opp_dict.keys()

            one_folded = False

            for name in self.opp_dict:
                if self.opp_dict[name].status == FOLDED:
                    one_folded = True
                    guy_folded = name
                else:
                    guy_active = name

            if one_folded: # one person folded
                fold_ew = calc_icm(self.my_stacksize, self.opp_dict[guy_active].stack_size+self.potsize, self.opp_dict[guy_folded].stack_size)[0]
                call_win_ew = calc_icm(self.my_stacksize+self.potsize, self.opp_dict[guy_active].stack_size, self.opp_dict[guy_folded].stack_size)[0]
                call_lose_ew = calc_icm(self.my_stacksize-self.inc_call_amount, self.opp_dict[guy_active].stack_size+self.potsize+self.inc_call_amount, self.opp_dict[guy_folded].stack_size)[0]

            else: # all three are still in hand
                winPercA = self.STATS.getPostFlopWinPct(opp_names[0])
                winPercB = self.STATS.getPostFlopWinPct(opp_names[1])

                skill_a = winPercA / (winPercA + winPercB)
                skill_b = 1 - skill_a

                # if min(self.STATS.postFlopCount.values()) > 10 and not self.STATS.postFlopWinPct[opp_names[0]] == 0 and self.STATS.postFlopWinPct[opp_names[1]] == 0:
                #     skill_a = self.STATS.postFlopWinPct[opp_names[0]] / (self.STATS.postFlopWinPct[opp_names[0]] + self.STATS.postFlopWinPct[opp_names[1]])
                #     skill_b = self.STATS.postFlopWinPct[opp_names[1]] / (self.STATS.postFlopWinPct[opp_names[0]] + self.STATS.postFlopWinPct[opp_names[1]])

                fold_ew_a      = calc_icm(self.my_stacksize, self.opp_dict[opp_names[0]].stack_size+self.potsize, self.opp_dict[opp_names[1]].stack_size)[0]
                fold_ew_b      = calc_icm(self.my_stacksize, self.opp_dict[opp_names[0]].stack_size             , self.opp_dict[opp_names[1]].stack_size+self.potsize)[0]
                fold_ew        = skill_a*fold_ew_a + skill_b*fold_ew_b

                if self.opp_dict[opp_names[0]].stack_size == 0 and self.opp_dict[opp_names[1]].stack_size == 0:
                    call_win_ew = FIRST_PRIZE
                else:
                    call_win_ew = calc_icm(self.my_stacksize+self.potsize, self.opp_dict[opp_names[0]].stack_size, self.opp_dict[opp_names[1]].stack_size)[0]

                if self.my_stacksize == self.inc_call_amount: # we are all-in
                    if self.opp_dict[opp_names[0]].stack_size == 0:
                        if self.opp_dict[opp_names[1]].stack_size != 0: # only first opponent and us all-in
                            if self.my_original_stacksize > self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = SECOND_PRIZE # all-in opponent loses (and us)
                            elif self.my_original_stacksize < self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = THIRD_PRIZE # all-in opponent loses (and us)
                            else:
                                call_lose_ew_b = SECOND_PRIZE / 2 # all-in opponent loses (and us)
                            call_lose_ew_a = 0 # all-in opponent wins and we lose

                        else: # both opponents all-in
                            if self.my_original_stacksize > self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = SECOND_PRIZE
                            elif self.my_original_stacksize < self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 0
                            elif self.my_original_stacksize == self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = SECOND_PRIZE / 2
                            if self.my_original_stacksize > self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = SECOND_PRIZE
                            elif self.my_original_stacksize < self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 0
                            elif self.my_original_stacksize == self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = SECOND_PRIZE / 2

                    elif self.opp_dict[opp_names[1]].stack_size == 0: # only second opponent and us all-in
                        if self.my_original_stacksize > self.opp_dict[opp_names[1]].original_stacksize:
                            call_lose_ew_a = SECOND_PRIZE
                        elif self.my_original_stacksize < self.opp_dict[opp_names[1]].original_stacksize:
                            call_lose_ew_a = 0
                        else:
                            call_lose_ew_a = SECOND_PRIZE / 2
                        call_lose_ew_b = 0 # all-in opponent wins and we lose

                    else: # only we are all-in
                        call_lose_ew_a = 0
                        call_lose_ew_b = 0

                else: # we are not all-in
                    call_lose_ew_a = calc_icm(self.my_stacksize-self.inc_call_amount, self.opp_dict[opp_names[0]].stack_size+self.potsize+self.inc_call_amount, self.opp_dict[opp_names[1]].stack_size)[0]
                    call_lose_ew_b = calc_icm(self.my_stacksize-self.inc_call_amount, self.opp_dict[opp_names[0]].stack_size, self.opp_dict[opp_names[1]].stack_size+self.potsize+self.inc_call_amount)[0]
                
                call_lose_ew = skill_a*call_lose_ew_a + skill_b*call_lose_ew_b

        # logic to determine call/fold
        if self.one_folded:
            bitch_factor = TWO_IN_BITCH_FACTOR_TABLE[self.num_boardcards]
        else:
            bitch_factor = THREE_IN_BITCH_FACTOR_TABLE[self.num_boardcards]
        lhs = fold_ew * bitch_factor
        rhs = equity*call_win_ew + (1-equity)*call_lose_ew

        print 'HAND ID : ' + str(self.hand_id)
        print 'MY HAND : ' + self.my_hand
        print 'MY STACK: ' + str(self.my_stacksize)
        print 'POT     : ' + str(self.potsize)
        print 'EQUITY  : ' + str(equity)
        print 'FOLD EW : ' + str(fold_ew) 
        print "CALL EW : " + str(rhs)
        print 'BITCH F : ' + str(bitch_factor)
        if lhs < rhs:
            return True
        return False





    def should_call(self, equity):
        should = self.should_call_no_stats(equity)
        # minEquity = 0
        # avgEquity = 0

        # if self.num_active_players == 2 or self.one_folded:
        #     guy_active = ""
        #     for name in self.opp_dict:
        #         if self.opp_dict[name].status == ACTIVE:
        #             guy_active = name
        #         # DEBUG
        #         print "PLAYER_TYPE : " + self.opp_dict[name].playerType
        #     minEquity = self.STATS.minEquityTwo[guy_active][self.num_boardcards]
        #     avgEquity = self.STATS.averageEquityTwo[guy_active][self.num_boardcards]
        # else:
        #     minEquity = max([i[self.num_boardcards] for i in self.STATS.minEquityThree.values()])
        #     avgEquity = max([i[self.num_boardcards] for i in self.STATS.averageEquityThree.values()])

        if should:
            # print "$$$ SHOULD"
            # print "INC CALL: " + str(self.inc_call_amount)
            # print "POT SIZE: " + str(self.potsize)

            # if relatively smalll:
            if self.inc_call_amount <= 2 * self.bigBlind:
                return True

            # # aggressive raise
            # if self.inc_call_amount > 10 and self.inc_call_amount > 0.24 * self.potsize:
            #     if self.opp_dict[self.lastRaiser].playerType in [TYPE_TA, TYPE_STA]:
            #         print "FOLDED BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
            #         return False
            #     elif self.opp_dict[self.lastRaiser].playerType != TYPE_LA and equity < 1.15 * self.raise_thres:
            #         print "FOLDED BECAUSE DID NOT MEET THRES: " + str(self.raise_thres * 1.15)
            #         return False 
            #     elif equity < self.raise_thres:
            #         print "FOLDED BECAUSE DID NOT MEET THRES"
            #         return False

            # new aggressive raise logic

            if self.my_stacksize < SUFFICIENT_CHIPS / 2:
                return True 

            if self.my_stacksize < SUFFICIENT_CHIPS and equity > self.raise_thres:
                return True

            raiseToMaxRaise = float(self.inc_call_amount) / (self.potsize - self.call_amount + self.highestRaiseAmtThisRnd + 0.01)
            print "AGGRESSIVENESS : " + str(raiseToMaxRaise)

            if self.num_active_players == 2:
                return True

            if self.inc_call_amount >= 6 * self.bigBlind:
                if raiseToMaxRaise > 0.75: # very aggressive
                    if self.opp_dict[self.lastRaiser].playerType in [TYPE_TA, TYPE_STA] and equity < 0.96:
                        print "FOLDED 1 BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
                        return False
                    elif self.opp_dict[self.lastRaiser].playerType != TYPE_LA and equity < 1.12 * self.raise_thres:
                        print "FOLDED 2 BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
                        return False
                    elif equity < self.raise_thres:
                        return False
                elif raiseToMaxRaise > 0.45: # medium aggressive
                    if self.opp_dict[self.lastRaiser].playerType in [TYPE_TA, TYPE_STA] and equity < 0.92:
                        print "FOLDED 3 BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
                        return False
                    elif self.opp_dict[self.lastRaiser].playerType != TYPE_LA and equity < 1.12 * self.raise_thres:
                        print "FOLDED 4 BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
                        return False
                    elif equity < self.raise_thres:
                        return False
                elif raiseToMaxRaise > 0.3: # mildly aggressive
                    if self.opp_dict[self.lastRaiser].playerType in [TYPE_TA, TYPE_STA]:
                        if equity < 1.12 * self.raise_thres:
                            print "FOLDED 5 BECAUSE PLAYER TYPE: " + self.opp_dict[self.lastRaiser].playerType 
                            return False                    
                    elif self.opp_dict[self.lastRaiser].playerType != TYPE_LA:
                        if equity < self.raise_thres:
                            return False



            return True
            # if self.num_boardcards != 0 and equity < avgEquity:
            #     print "$$$ BUT NO"
            #     return False
            # else:
            #     return True

        return False


        # else:
        #     print "$$$ SHOULD NOT"
        #     if equity > avgEquity:
        #         print "$$$ BUT YES"
        #         return True
        #     else:
        #         return False






    def get_best_action(self, received_packet, avail_actions = []):
        equity = None

        # set thresholds
        # if not self.one_out:
        #     self.fold_thres = THREE_FOLD_THRES_TABLE[self.num_boardcards]
        #     self.raise_thres = THREE_RAISE_THRES_TABLE[self.num_boardcards]
        #     self.opp_fold_thres = THREE_opp_fold_thres
        # else:
        #     self.fold_thres = TWO_FOLD_THRES_TABLE[self.num_boardcards]
        #     self.raise_thres = TWO_RAISE_THRES_TABLE[self.num_boardcards]
        #     self.opp_fold_thres = TWO_opp_fold_thres

        # see if we could use precomputed equity

        if self.num_active_players == 2 or self.one_folded == True:
            self.fold_thres = TWO_FOLD_THRES_TABLE[self.num_boardcards]
            self.raise_thres = TWO_RAISE_THRES_TABLE[self.num_boardcards]
            self.opp_fold_thres = self.STATS.getFoldPercent(self.guy_active)
            if self.num_boardcards == 0:
                equity = self.equity_table_2[self.my_hand]
            else:
                equity = pbots_calc.calc(':'.join([self.my_hand, 'xx']), ''.join(received_packet['boardcards']), 
                    "", self.monte_carlo_iter)
                equity = equity.ev[0]
        else:
            self.fold_thres = THREE_FOLD_THRES_TABLE[self.num_boardcards]
            self.raise_thres = THREE_RAISE_THRES_TABLE[self.num_boardcards]
            self.opp_fold_thres = self.opp1_skill * self.STATS.getFoldPercent(self.opponent_1_name) + self.opp2_skill * self.STATS.getFoldPercent(self.opponent_2_name) 
            if self.num_boardcards == 0:
                equity = self.equity_table_3[self.my_hand]
            else:
                equity = pbots_calc.calc(':'.join([self.my_hand, 'xx', 'xx']), ''.join(received_packet['boardcards']), 
                    "", self.monte_carlo_iter)
                equity = equity.ev[0]



        do_reraise = random.random() < self.opp_fold_thres

        # print 'FOLD T: ' + str(self.opp_fold_thres) 
        # print 'EQUITY: ' + str(equity)

        own_a_lot_of_chips = self.my_stacksize > LOTS_OF_CHIPS
        winning_factor = ((equity - self.fold_thres) / (1 - self.fold_thres))**POWER

        # TODO: Raise a little if they checked last turn

        # if equity < self.fold_thres and ((own_a_lot_of_chips != True) or (self.num_boardcards != 0)):
        #     # TODO: Implement bluffing / call here
        #     if CHECK in avail_actions:
        #         # bet a little bit if possible to exploit bots who fold to small raises: (but dont do this all the time)
        #         # if BET in avail_actions and self.my_stacksize > BET_SMALL_LIKELIHOOD[self.num_boardcards]:
        #         if False:
        #             random_nig = random.random()
        #             # foldPerc = 0.0
        #             # for name in self.opp_dict:
        #             #     if self.opp_dict[name].status == ACTIVE:
        #             #         foldPerc += self.STATS.foldPercentage[name]
        #             # if not self.one_folded:
        #             #     foldPerc = foldPerc / 2
        #             if random_nig < self.opp_fold_thres:
        #                 print "MINBET: " + str(self.minBet)
        #                 return BET + ":" + str(self.minBet)
        #         return CHECK
        #     return FOLD


        # Subroutines we use to make our lives easier:
        #####################################################################################################
        def do_call ():
            if self.should_call(equity):
                self.highestRaiseAmtThisRnd = self.call_amount
                return CALL + ":" + str(self.call_amount)
            else:
                return FOLD

        def do_raise_preflop ():
            if self.my_hand in self.boss_class1:
                if self.lastRaiser in [TYPE_STA] and self.my_stacksize > SUFFICIENT_CHIPS:
                    return CALL + ":" + str(self.call_amount)
                # raise a lot
                self.highestRaiseAmtThisRnd = self.maxRaise
                return RAISE + ":" + str(self.maxRaise)
            elif self.my_hand in self.boss_class2:
                if self.num_active_players == 3 and self.one_folded == False:
                    if (self.opp_dict[self.opponent_1_name].playerType not in [TYPE_STA, TYPE_TA, TYPE_LP]) and \
                        (self.opp_dict[self.opponent_2_name].playerType not in [TYPE_STA, TYPE_TA, TYPE_LP]):
                        # raise a lot
                        self.highestRaiseAmtThisRnd = self.maxRaise
                        return RAISE + ":" + str(self.maxRaise)
                    else:
                        self.highestRaiseAmtThisRnd = self.maxRaise
                        return RAISE + ":" + str(self.minRaise)
                elif self.opp_dict[self.guy_active].playerType not in [TYPE_STA, TYPE_TA, TYPE_LP]:
                    # raise a lot
                    self.highestRaiseAmtThisRnd = self.maxRaise
                    return RAISE + ":" + str(self.maxRaise)
                else:
                    self.highestRaiseAmtThisRnd = self.minRaise
                    return RAISE + ":" + str(self.minRaise)
            # bet a little in general
            self.highestRaiseAmtThisRnd = self.minRaise
            return RAISE + ":" + str(self.minRaise)

        def do_call_preflop ():
            raiserType = self.opp_dict[self.lastRaiser].playerType
            if raiserType in [TYPE_STA, TYPE_TA, TYPE_LP]:
                if self.my_hand in self.boss_class1:
                    return do_call()
                else:
                    # do not engage
                    return FOLD
            elif raiserType != TYPE_LA:
                if self.my_hand in self.boss_class1 or self.my_hand in self.boss_class2:
                    return do_call()
                else:
                    return FOLD
            else:
                return do_call()
        #####################################################################################################



        if equity < self.fold_thres:
            if self.isPreflop:
                if self.handPosition == BUTTON:
                    if self.opp_dict[self.opponent_1_name].playerType == TYPE_LA or self.opp_dict[self.opponent_2_name].playerType == TYPE_LA:
                        if (self.fold_thres - equity) < TOLERANCE_FOR_LA:
                            if CALL in avail_actions:
                                if self.call_amount == self.bigBlind and RAISE in avail_actions:
                                    self.highestRaiseAmtThisRnd = self.minRaise
                                    return RAISE + ":" + str(self.minRaise)
                return FOLD

            if BET in avail_actions and self.minBet <= self.bigBlind:
                if self.oppCheckedThisRound:
                    random_nig = random.random()
                    if random_nig < self.opp_fold_thres:
                        # print "MINBET: " + str(self.minBet)
                        self.highestRaiseAmtThisRnd = self.minBet
                        return BET + ":" + str(self.minBet)
            if CHECK in avail_actions:
                return CHECK
            if CALL in avail_actions:
                # if relatively smalll:
                if self.inc_call_amount <= self.bigBlind or \
                    (self.isPreflop == False and (self.inc_call_amount < 2 * self.bigBlind or self.inc_call_amount < 0.07 * self.potsize)):
                    return do_call()
            return FOLD



        # elif equity > self.raise_thres and (self.is_new_round or do_reraise): 
        elif equity > self.raise_thres:
            if self.isPreflop: # fun time!
                if self.handPosition == BUTTON:
                    if self.opp_dict[self.opponent_1_name].playerType == TYPE_LA or self.opp_dict[self.opponent_2_name].playerType == TYPE_LA:
                        if self.num_active_players == 2 or self.one_folded:
                            if self.opp_dict[self.guy_active].playerType == TYPE_LA:
                                # nigga will handle raising
                                return do_call()
                        else:
                            # niggas will handle the raising for us
                            return do_call()
                    if CALL in avail_actions:
                        if self.potsize > 5 * self.bigBlind:
                            return do_call_preflop()
                        else:
                            if RAISE in avail_actions:
                                return do_raise_preflop()
                            else:
                                return do_call_preflop()

                elif self.handPosition == BB:
                    if CALL in avail_actions: # someone raised
                        return do_call_preflop()
                    elif RAISE in avail_actions and self.potsize < 7:
                        return do_raise_preflop()
                    return CHECK

                elif self.handPosition == SB:
                    if CALL in avail_actions: 
                        if self.call_amount == self.bigBlind and RAISE in avail_actions:
                            return do_raise_preflop()
                        else: # someone raised
                            return do_call_preflop()

            else: 
                if BET in avail_actions:
                    amount = self.bet_handler(winning_factor)
                    return BET + ":" + str(amount)
                elif RAISE in avail_actions and do_reraise:
                    # if they raise a little, either counter raise or call
                    if self.should_call(equity):
                        amount = self.raise_handler(winning_factor)
                        return RAISE + ":" + str(amount)
                    else:
                        return FOLD


        # not in very good equity range
        if CHECK in avail_actions or BET in avail_actions:
            if self.oppCheckedThisRound:
                random_nig = random.random()
                if random_nig < self.opp_fold_thres:
                    # print "MINBET: " + str(self.minBet * 4)
                    self.highestRaiseAmtThisRnd = self.minBet * 4
                    return BET + ":" + str(self.minBet * 4)




        if CALL in avail_actions:
            # TODO: do preflop logic here
            if self.isPreflop:
                if self.handPosition == BUTTON or (self.handPosition == SB and self.num_active_players == 2):
                    if self.opp_dict[self.guy_active].playerType == TYPE_LA:
                        # nigga will handle raising
                        return do_call()
                    if self.potsize > 5 * self.bigBlind:
                        return do_call_preflop()
                    else:
                        if RAISE in avail_actions:
                            return do_raise_preflop()
                        else:
                            return do_call_preflop()
                elif self.handPosition == SB:
                    if self.call_amount == self.bigBlind:
                        return do_call()
                    else: # someone raised
                        return FOLD
                elif self.handPosition == BB:
                    # someone raised
                    if self.potsize <= 3 * self.bigBlind:
                        return do_call_preflop()
                    return FOLD

            else:
                return do_call ()

            # return do_call()

        # if CHECK in avail_actions:
        #     random_nig = random.random()
        #     if random_nig < self.opp_fold_thres:
        #         print "MINBET: " + str(self.minBet)
        #         return BET + ":" + str(self.minBet)

        return CHECK







    def getaction_handler(self, received_packet):

        # for action in received_packet['last_action']:
        #     split_action = action.split(":")

        self.list_of_stacksizes = received_packet['stack_size']
        self.my_stacksize       = self.list_of_stacksizes[self.my_seat - 1]
        self.potsize            = received_packet['potsize']
        self.num_active_players = received_packet['num_active_players']
        self.boardcards         = received_packet['boardcards']
        self.foundFaceCard      = self.faceCardOnTable(self.boardcards)
        # print "FACE CARD CHECK", self.foundFaceCard

        last_actions = received_packet['last_action']

        #################################################################
        self.STATS.recordActions(last_actions)
        #################################################################

        self.lastRaiser = None
        self.oppCheckedThisRound = False
        for act in last_actions:
            sp = act.split(":")
            name = sp[-1]
            if sp[0] == DEAL:
                self.oppCheckedThisRound = False
            if name in self.opp_dict:
                self.opp_dict[name].last_action = sp[0]
                if sp[0] == FOLD:
                    self.opp_dict[name].status = FOLDED
                    self.one_folded = True
                if sp[0] == BET or sp[0] == RAISE:
                    self.lastRaiser = name
                if sp[0] == CHECK:
                    self.oppCheckedThisRound = True
                

        for name in self.opp_dict:
            self.opp_dict[name].stack_size = self.list_of_stacksizes[self.opp_dict[name].seat]
            if self.opp_dict[name].status == ACTIVE:
                    self.guy_active = name

        # print '###################################'
        # for shit in self.opp_dict:    
        #     print shit
        #     print self.opp_dict[shit].stack_size
        #     print self.opp_dict[shit].status
        #     print self.opp_dict[shit].last_action
        # print '###################################'
        # determine if we are still in the same betting round to prevent raising to infinity problem
        
        if received_packet['num_boardcards'] == self.num_boardcards:
            self.is_new_round = False
        else: 
            self.is_new_round = True
            self.highestRaiseAmtThisRnd = 0
        self.num_boardcards = received_packet['num_boardcards']
        self.isPreflop = (self.num_boardcards == 0) 

        for action in received_packet['legal_actions']:
            split_action = action.split(":")

            if split_action[0] == BET:
                self.minBet = int(split_action[1])
                self.maxBet = int(split_action[2])
            elif split_action[0] == RAISE:
                self.minRaise = int(split_action[1])
                self.maxRaise = int(split_action[2])
            elif split_action[0] == CALL:
                self.call_amount = int(split_action[1])
                self.inc_call_amount = self.call_amount - self.highestRaiseAmtThisRnd

        avail_actions = [(e.split(":"))[0] for e in received_packet['legal_actions']]
        action = self.get_best_action (received_packet, avail_actions)
        ###############################################################################################
        # self.STATS.updateOpponentStatistics(received_packet, self.hand_id, action)
        ###############################################################################################
        s.send(action + "\n")



    def handover_handler(self, received_packet):
        ###############################################################################################
        self.foundFaceCard = False
        self.STATS.updateOpponentStatistics(received_packet, self.num_active_players, self.monte_carlo_iter / 5)
        ###############################################################################################

    def requestkeyvalue_handler(self, received_packet):
        # At the end, the engine will allow your bot save key/value pairs.
        # Send FINISH to indicate you're done.
        ###############################################################################################
        self.STATS.compileMatchStatistics(self.history_storage, s, int(received_packet['bytesLeft']))
        ###############################################################################################
        s.send("FINISH\n")


    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()



        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            received_packet = packet_parse.parse_given_packet(data)

            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!            

            # this print statement is so that the stupid piece of shit Batman won't run into an error
            print data
            
            if received_packet['packet_name'] == "KEYVALUE":
                self.keyval_handler(received_packet)

            elif received_packet['packet_name'] == "NEWGAME":
                self.newgame_handler(received_packet)

            elif received_packet['packet_name'] == "NEWHAND":
                self.newhand_handler(received_packet)

            elif received_packet['packet_name'] == "GETACTION":
                self.getaction_handler(received_packet)

            elif received_packet['packet_name'] == "HANDOVER":
                self.handover_handler(received_packet)

            elif received_packet['packet_name'] == "REQUESTKEYVALUES":
                self.requestkeyvalue_handler(received_packet)

        # Clean up the socket.

        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)