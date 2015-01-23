import argparse
import socket
import sys
import pbots_calc
import random
import Statistician

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


# Statuses
FOLDED = 0
OUT    = 1
ACTIVE = 2 


# suits
SPADE   = "s"
CLUB    = "c"
DIAMOND = "d"
HEART   = "h"


# equity threshold
THREE_FOLD_THRES_TABLE  = {0 : 0.25, 3 : 0.25, 4 : 0.25, 5 : 0.25}
THREE_RAISE_THRES_TABLE = {0 : 0.36, 3 : 0.6,  4 : 0.75, 5 : 0.8}
TWO_FOLD_THRES_TABLE    = {0 : 0.4,  3 : 0.4,  4 : 0.4,  5 : 0.4}
TWO_RAISE_THRES_TABLE   = {0 : 0.6,  3 : 0.75, 4 : 0.85, 5 : 0.9}


# randomness threshold
THREE_RERAISE_THRES = 0.8
TWO_RERAISE_THRES   = 0.6

POWER = 4



# ITER_TABLE = {0 : 30000, 3 : 30000, 4 : 30000, 5 : 30000}
MONTE_CARLO_ITER = 30000
DELTA_ITER       = 5000
# BITCH_FACTOR_TABLE = {0 : 0.75, 3 : 0.8, 4 : 0.9, 5 : 1}
BITCH_FACTOR_TABLE = {0 : 1, 3 : 2, 4 : 2.5, 5 : 3.5}


# print pbots_calc.calc("AhKh:xx", "ThJhQh2s7s", "", 1)
# print pbots_calc.calc("AhKh:xx:xx", "JhQh2s7s", "", 100)


FIRST_PRIZE  = 180
SECOND_PRIZE = 60
THIRD_PRIZE  = 0

# ICM Helper function
def calc_icm (a, b, c):

    s = float(a + b + c)

    # if a == s:
    #     return (FIRST_PRIZE, SECOND_PRIZE, THIRD_PRIZE)

    # elif b == s:
    #     return (THIRD_PRIZE, FIRST_PRIZE, SECOND_PRIZE)

    # elif c == s:
    #     return (THIRD_PRIZE, SECOND_PRIZE, FIRST_PRIZE)

    # else:

    #   s = float(s)

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
        self.reraise_thres          = 0
        self.raise_thres            = 0
        self.call_amount            = 0
        self.is_new_round           = True
        self.last_action            = None
        self.num_boardcards         = -1
        self.my_seat                = 1
        self.potsize                = 0
        self.opp_dict               = {}
        self.stats                  = None
        self.monte_carlo_iter       = MONTE_CARLO_ITER
        self.one_folded             = False

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


    # def makeAction(self, action, amount, minBet, maxBet, minRaise, maxRaise):
    #     if action == BET:
    #         amount = self.makeBet(minBet, maxBet)
    #         s.send(action + ':' + str(amount) + '\n')
    #     elif action == RAISE:
    #         amount = self.makeRaise(minRaise, maxRaise)
    #         s.send(action + ':' + str(amount) + '\n')
    #     else:
    #         s.send(action + '\n')


    def keyval_handler(self, received_packet):
        self.history_storage[received_packet['key']] = received_packet['value']




    def newgame_handler(self, received_packet):

        self.opponent_1_name = received_packet['opponent_1_name']
        self.opponent_2_name = received_packet['opponent_2_name']

        self.my_name = received_packet['player_name']

        self.stats = Statistician.Statistician(self.my_name, self.opponent_1_name, self.opponent_2_name)

        self.opp_dict[self.opponent_1_name] = Opponent(self.opponent_1_name)
        self.opp_dict[self.opponent_2_name] = Opponent(self.opponent_2_name)

        self.time_bank       = float(received_packet['timeBank'])
        self.time_low_thres  = 0.3 * self.time_bank
        self.time_per_hand   = 2 * self.time_bank / received_packet['num_hands']  

        # If we have already played the opponent before, 
        # we load their statistics from the previous encounter
        # for this game. NOTE that Historian is just an instance of the Statistician/Historian class
        # that is not yet created. 
        if self.opponent_1_name in self.history_storage:
            self.hasPlayed_opponent_1 = True
            # statistician.getOpponentStatistics(opponent_1_name, history_storage[opponent_1_name])

        if self.opponent_2_name in self.history_storage:
            self.hasPlayed_opponent_2 = True
            #statistician.getOpponentStatistics(opponent_2_name, history_storage[opponent_2_name])




    def newhand_handler(self, received_packet):
        
        self.my_hand = received_packet['hand']
        self.my_seat = received_packet['seat']
        self.list_of_stacksizes = received_packet['stack_size']
        self.my_original_stacksize = self.list_of_stacksizes[self.my_seat - 1]
        self.hand_id = received_packet['handID']
        self.num_active_players = received_packet['num_active_players']
        self.list_of_active_players = received_packet['active_players']

        # adjust iterations
        new_time_bank = float(received_packet['timeBank'])
        if new_time_bank < self.time_low_thres:
            self.time_per_hand = self.time_per_hand / 4
        delta_time = self.time_bank - new_time_bank 
        if delta_time > self.time_per_hand:
            self.monte_carlo_iter = max(self.monte_carlo_iter - DELTA_ITER, DELTA_ITER)
        else:
            self.monte_carlo_iter = self.monte_carlo_iter + DELTA_ITER

        self.time_bank = new_time_bank

        # print "ITER : " + str(self.monte_carlo_iter)
        # print "DELTA: " + str(delta_time)

        self.one_folded = False

        names = received_packet['player_names']
        for i in range(len(names)):
            name = names[i]
            if name != self.my_name:
                self.opp_dict[name].seat = i 
                self.opp_dict[name].stack_size = self.list_of_stacksizes[i]
                self.opp_dict[name].original_stacksize = self.list_of_stacksizes[i]
                # update status
                if self.opp_dict[name].stack_size == 0:
                    self.opp_dict[name].status = OUT
                else:
                    self.opp_dict[name].status = ACTIVE



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

        return self.makeBet(bet_amount)
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

        return self.makeRaise(raise_amount)
        # s.send(RAISE + ':' + str(self.makeRaise(raise_amount)) + '\n')






    def should_call (self, equity):
        fold_ew      = 0
        call_win_ew  = 0
        call_lose_ew = 0

        # should call before the flop
        if self.num_boardcards == 0 and self.potsize <= 6:
            return True

        bitch_factor = BITCH_FACTOR_TABLE[self.num_boardcards]

        # check if one is out
        guy_active = ""
        guy_folded = ""

        if self.num_active_players == 2: #heads-up
            for name in self.opp_dict:
                if self.opp_dict[name].status == ACTIVE:
                    guy_active = name

            other_guy_stacksize = self.opp_dict[guy_active].original_stacksize

            if other_guy_stacksize <= 0.05*self.my_original_stacksize:
                return True

            else:
                fold_chips = self.my_stacksize
                call_lose_chips = self.my_stacksize - self.call_amount
                call_win_chips = self.my_stacksize + self.potsize
                print "FOLD CHIPS: " + str(fold_chips * bitch_factor)
                print "EXP CHIPS : " + str(call_lose_chips*(1-equity) + call_win_chips*equity)
                lhs = fold_chips * bitch_factor
                rhs = call_lose_chips*(1-equity) + call_win_chips*equity
                return lhs < rhs

        else: # all three players have chips
            self.stats.getPostFlopWinPct()
            opp_names = self.opp_dict.keys()

            skill_a = 0.5
            skill_b = 0.5

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
                call_lose_ew = calc_icm(self.my_stacksize-self.call_amount, self.opp_dict[guy_active].stack_size+self.potsize+self.call_amount, self.opp_dict[guy_folded].stack_size)[0]

            else: # all three are still in hand
                if self.stats.postFlopCount > 10 and not self.stats.postFlopWinPct[opp_names[0]] == 0 and self.stats.postFlopWinPct[opp_names[1]] == 0:
                    skill_a = self.stats.postFlopWinPct[opp_names[0]] / (self.stats.postFlopWinPct[opp_names[0]] + self.stats.postFlopWinPct[opp_names[1]])
                    skill_b = self.stats.postFlopWinPct[opp_names[1]] / (self.stats.postFlopWinPct[opp_names[0]] + self.stats.postFlopWinPct[opp_names[1]])

                fold_ew_a      = calc_icm(self.my_stacksize, self.opp_dict[opp_names[0]].stack_size+self.potsize, self.opp_dict[opp_names[1]].stack_size)[0]
                fold_ew_b      = calc_icm(self.my_stacksize, self.opp_dict[opp_names[0]].stack_size             , self.opp_dict[opp_names[1]].stack_size+self.potsize)[0]
                fold_ew        = skill_a*fold_ew_a + skill_b*fold_ew_b

                if self.opp_dict[opp_names[0]].stack_size == 0 and self.opp_dict[opp_names[1]].stack_size == 0:
                    call_win_ew = 180
                else:
                    call_win_ew = calc_icm(self.my_stacksize+self.potsize, self.opp_dict[opp_names[0]].stack_size, self.opp_dict[opp_names[1]].stack_size)[0]

                if self.my_stacksize == self.call_amount: # we are all-in
                    if self.opp_dict[opp_names[0]].stack_size == 0:
                        if self.opp_dict[opp_names[1]].stack_size != 0: # only first opponent and us all-in
                            if self.my_original_stacksize > self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 60 # all-in opponent loses (and us)
                            elif self.my_original_stacksize < self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 0 # all-in opponent loses (and us)
                            else:
                                call_lose_ew_b = 30 # all-in opponent loses (and us)
                            call_lose_ew_a = 0 # all-in opponent wins and we lose

                        else: # both opponents all-in
                            if self.my_original_stacksize > self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 60
                            elif self.my_original_stacksize < self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 0
                            elif self.my_original_stacksize == self.opp_dict[opp_names[0]].original_stacksize:
                                call_lose_ew_b = 30
                            if self.my_original_stacksize > self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 60
                            elif self.my_original_stacksize < self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 0
                            elif self.my_original_stacksize == self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 30

                    else: 
                        if self.opp_dict[opp_names[1]].stack_size == 0: # only second opponent and us all-in
                            if self.my_original_stacksize > self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 60
                            elif self.my_original_stacksize < self.opp_dict[opp_names[1]].original_stacksize:
                                call_lose_ew_a = 0
                            else:
                                call_lose_ew_a = 30
                            call_lose_ew_b = 0 # all-in opponent wins and we lose

                        else: # only we are all-in
                            call_lose_ew_a = 0
                            call_lose_ew_b = 0

                else: # we are not all-in
                    call_lose_ew_a = calc_icm(self.my_stacksize-self.call_amount, self.opp_dict[opp_names[0]].stack_size+self.potsize+self.call_amount, self.opp_dict[opp_names[1]].stack_size)[0]
                    call_lose_ew_b = calc_icm(self.my_stacksize-self.call_amount, self.opp_dict[opp_names[0]].stack_size, self.opp_dict[opp_names[1]].stack_size+self.potsize+self.call_amount)[0]
                
                call_lose_ew   = skill_a*call_lose_ew_a + skill_b*call_lose_ew_b

        # logic to determine call/fold
        bitch_factor = BITCH_FACTOR_TABLE[self.num_boardcards]
        lhs = fold_ew * bitch_factor
        rhs = equity*call_win_ew + (1-equity)*call_lose_ew

        # print 'HAND ID : ' + str(self.hand_id)
        # print 'MY HAND : ' + self.my_hand
        # print 'MY STACK: ' + str(self.my_stacksize)
        # print 'POT     : ' + str(self.potsize)
        # print 'EQUITY  : ' + str(equity)
        # print 'FOLD EW : ' + str(fold_ew) 
        # print "CALL EW : " + str(rhs)
        # print 'BITCH F : ' + str(bitch_factor)
        if lhs < rhs:
            return True
        return False






    def get_best_action(self, received_packet, avail_actions = []):
        equity = None

        # determine if we are still in the same betting round to prevent raising to infinity problem
        if received_packet['num_boardcards'] == self.num_boardcards:
            self.is_new_round = False
        else: 
            self.is_new_round = True
        self.num_boardcards = received_packet['num_boardcards'] 

        # set thresholds
        # if not self.one_out:
        #     self.fold_thres = THREE_FOLD_THRES_TABLE[self.num_boardcards]
        #     self.raise_thres = THREE_RAISE_THRES_TABLE[self.num_boardcards]
        #     self.reraise_thres = THREE_RERAISE_THRES
        # else:
        #     self.fold_thres = TWO_FOLD_THRES_TABLE[self.num_boardcards]
        #     self.raise_thres = TWO_RAISE_THRES_TABLE[self.num_boardcards]
        #     self.reraise_thres = TWO_RERAISE_THRES

        # see if we could use precomputed equity

        if self.num_active_players == 2 or self.one_folded == True:
            self.fold_thres = TWO_FOLD_THRES_TABLE[self.num_boardcards]
            self.raise_thres = TWO_RAISE_THRES_TABLE[self.num_boardcards]
            self.reraise_thres = TWO_RERAISE_THRES
            if self.num_boardcards == 0:
                equity = self.equity_table_2[self.my_hand]
            else:
                equity = pbots_calc.calc(':'.join([self.my_hand, 'xx']), ''.join(received_packet['boardcards']), 
                    "", self.monte_carlo_iter)
                equity = equity.ev[0]
        else:
            self.fold_thres = THREE_FOLD_THRES_TABLE[self.num_boardcards]
            self.raise_thres = THREE_RAISE_THRES_TABLE[self.num_boardcards]
            self.reraise_thres = THREE_RERAISE_THRES
            if self.num_boardcards == 0:
                equity = self.equity_table_3[self.my_hand]
            else:
                equity = pbots_calc.calc(':'.join([self.my_hand, 'xx', 'xx']), ''.join(received_packet['boardcards']), 
                    "", self.monte_carlo_iter)
                equity = equity.ev[0]



        do_reraise = random.random() > self.reraise_thres

        print 'EQUITY: ' + str(equity)

        if equity < self.fold_thres:
            # TODO: Implement bluffing / call here
            if CHECK in avail_actions:
                return CHECK
            return FOLD

        elif equity > self.raise_thres and (self.is_new_round or do_reraise): 
            winning_factor = ((equity - self.fold_thres) / (1 - self.fold_thres))**POWER
            if BET in avail_actions:
                amount = self.bet_handler(winning_factor)
                return BET + ":" + str(amount)
            elif RAISE in avail_actions:
                amount = self.raise_handler(winning_factor)
                return RAISE + ":" + str(amount)
        
        if CALL in avail_actions: 
            if self.should_call(equity):
                return CALL + ":" + str(self.call_amount)
            else:
                return FOLD

        return CHECK







    def getaction_handler(self, received_packet):

        # for action in received_packet['last_action']:
        #     split_action = action.split(":")

        self.list_of_stacksizes = received_packet['stack_size']
        self.my_stacksize       = self.list_of_stacksizes[self.my_seat - 1]
        self.potsize            = received_packet['potsize']
        self.num_active_players = received_packet['num_active_players']

        last_actions = received_packet['last_action']
        for act in last_actions:
            sp = act.split(":")
            name = sp[-1]
            if name in self.opp_dict:
                self.opp_dict[name].last_action = sp[0]
                if sp[0] == FOLD:
                    self.opp_dict[name].status = FOLDED
                    self.one_folded = True

        for name in self.opp_dict:
            self.opp_dict[name].stack_size = self.list_of_stacksizes[self.opp_dict[name].seat]

        # print '###################################'
        # for shit in self.opp_dict:    
        #     print shit
        #     print self.opp_dict[shit].stack_size
        #     print self.opp_dict[shit].status
        #     print self.opp_dict[shit].last_action
        # print '###################################'

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

        avail_actions = [(e.split(":"))[0] for e in received_packet['legal_actions']]
        action = self.get_best_action (received_packet, avail_actions)
        self.stats.updateOpponentStatistics(received_packet, self.hand_id, action)
        s.send(action + "\n")


        # for action in received_packet['legal_actions']:
        #     split_action = action.split(":")

        #     if split_action[0] == BET:
        #         made_bet = self.bet_handler()
        #         if made_bet:
        #             return
        #     elif split_action[0] == RAISE:
        #         made_raise = self.raise_handler()
        #         if made_raise:
        #             return
        #     elif split_action[0] == CALL:

            # if split_action[0] == BET or split_action[0] == RAISE:
            #     self.minBet = int(split_action[1])
            #     self.maxBet = int(split_action[2])

            #     s.send(split_action[0]+":"+str(self.maxBet) + "\n")  



    def handover_handler(self, received_packet):
        self.stats.updateOpponentStatistics(received_packet, self.hand_id, "")

    def requestkeyvalue_handler(self, received_packet):
        # At the end, the engine will allow your bot save key/value pairs.
        # Send FINISH to indicate you're done.
        self.stats.compileMatchStatistics(self.hand_id)
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