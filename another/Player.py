import argparse
import socket
import sys
import pbots_calc
import random

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


THREE_FOLD_THRES    = 0.35
THREE_RAISE_THRES   = 0.7
THREE_RERAISE_THRES = 0.9
TWO_FOLD_THRES      = 0.2
TWO_RAISE_THRES     = 0.6
TWO_RERAISE_THRES   = 0.8

POWER = 4



ITER_TABLE = {0 : 30000, 3 : 30000, 4 : 30000, 5 : 30000}
BITCH_FACTOR_TABLE = {0 : 0.6, 3 : 0.75, 4 : 9, 5 : 1}


# print pbots_calc.calc("AhKh:xx", "ThJhQh2s7s", "", 1)
# print pbots_calc.calc("AhKh:xx:xx", "JhQh2s7s", "", 100)


FIRST_PRIZE  = 100
SECOND_PRIZE = -20
THIRD_PRIZE  = -80

# ICM Helper function
def calc_icm (a, b, c):

    s = a + b + c

    if a == s:
        return (FIRST_PRIZE, SECOND_PRIZE, THIRD_PRIZE)

    elif b == s:
        return (THIRD_PRIZE, FIRST_PRIZE, SECOND_PRIZE)

    elif c == s:
        return (THIRD_PRIZE, SECOND_PRIZE, FIRST_PRIZE)

    else:
        s = float(s)
    
        pa1 = a/s
        pb1 = b/s
        pc1 = c/s
        
        pa2 = pb1 * (a/(s-b)) + pc1 * (a/(s-c))
        pb2 = pa1 * (b/(s-a)) + pc1 * (b/(s-c))
        pc2 = pa1 * (c/(s-a)) + pb1 * (c/(s-b))
        
        pa3 = 1 - pa1 - pa2
        pb3 = 1 - pb1 - pb2
        pc3 = 1 - pc1 - pc2

        ewa = pa1 * FIRST_PRIZE + pa2 * SECOND_PRIZE + pa3 * THIRD_PRIZE
        ewb = pb1 * FIRST_PRIZE + pb2 * SECOND_PRIZE + pb3 * THIRD_PRIZE
        ewc = pc1 * FIRST_PRIZE + pc2 * SECOND_PRIZE + pc3 * THIRD_PRIZE

        return (ewa, ewb, ewc)




class Opponent:
    def __init__ (self, name):
        self.seat        = 0 # 0, 1, 2
        self.name        = name
        self.stack_size  = 200
        self.status      = ACTIVE
        self.last_action = None




class Player:

    def __init__ (self):
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
        self.fold_thres             = THREE_FOLD_THRES
        self.reraise_thres          = THREE_RERAISE_THRES
        self.raise_thres            = THREE_RAISE_THRES
        self.call_amount            = 0
        self.is_new_round           = True
        self.last_action            = None
        self.num_boardcards         = -1
        self.my_seat                = 1
        self.potsize                = 0
        self.opp_dict               = {}




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
        self.opp_dict[self.opponent_1_name] = Opponent(self.opponent_1_name)
        self.opp_dict[self.opponent_2_name] = Opponent(self.opponent_2_name)

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

        names = received_packet['player_names']
        for i in range(len(names)):
            name = names[i]
            if name != self.my_name:
                self.opp_dict[name].seat = i 
                self.opp_dict[name].stack_size = self.list_of_stacksizes[i]
                # update status
                if self.opp_dict[name].stack_size == 0:
                    self.opp_dict[name].status = OUT
                else:
                    self.opp_dict[name].status = ACTIVE




    def bet_handler(self, winning_factor):
        a = random.random()
        bet_amount = 0

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
        opp_stack_sizes = self.list_of_stacksizes
        del opp_stack_sizes[self.my_seat-1]

        fold_ew      = 0
        call_win_ew  = 0
        call_lose_ew = 0

        # check if one is out
        one_out = False
        guy_active = ""
        guy_inactive = ""
        for name in self.opp_dict:
            if self.opp_dict[name].status == OUT or self.opp_dict[name].status == FOLDED:
                one_out = True
                guy_inactive = name
            else:
                guy_active = name

        if one_out:
            other_guy_stacksize = self.opp_dict[guy_active].stack_size
            inactive_stack = self.opp_dict[guy_inactive].stack_size
            fold_ew      = calc_icm(self.my_stacksize,                  inactive_stack, other_guy_stacksize+self.potsize)[0]
            call_win_ew  = calc_icm(self.my_stacksize+self.potsize,     inactive_stack, other_guy_stacksize)[0]
            call_lose_ew = calc_icm(self.my_stacksize-self.call_amount, inactive_stack, other_guy_stacksize+self.potsize+self.call_amount)[0]

        else: # all three players are active
            fold_ew_a      = calc_icm(self.my_stacksize, opp_stack_sizes[0]+self.potsize, opp_stack_sizes[1])[0]
            fold_ew_b      = calc_icm(self.my_stacksize, opp_stack_sizes[0],              opp_stack_sizes[1]+self.potsize)[0]
            fold_ew        = 0.5*(fold_ew_a+fold_ew_b)
            call_win_ew    = calc_icm(self.my_stacksize+self.potsize,     opp_stack_sizes[0],                               opp_stack_sizes[1])[0]
            call_lose_ew_a = calc_icm(self.my_stacksize-self.call_amount, opp_stack_sizes[0]+self.potsize+self.call_amount, opp_stack_sizes[1])[0]
            call_lose_ew_b = calc_icm(self.my_stacksize-self.call_amount, opp_stack_sizes[0], opp_stack_sizes[1]+self.potsize+self.call_amount)[0]
            call_lose_ew   = 0.5*(call_lose_ew_a+call_lose_ew_b)

        # logic to determine call/fold
        # print 'MY STACK: ' + str(self.my_stacksize)
        # print 'POT     : ' + str(self.potsize)
        # print 'FOLD EW: ' + str(fold_ew) + '\n' + "CALL EW: " + str(equity*call_win_ew + (1-equity)*call_lose_ew) + '\n'
        
        if fold_ew < equity*call_win_ew + (1-equity)*call_lose_ew:
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

        if received_packet['num_active_players'] == 3:
            self.fold_thres = THREE_FOLD_THRES
            self.raise_thres = THREE_RAISE_THRES
            self.reraise_thres = THREE_RERAISE_THRES
            equity = pbots_calc.calc(':'.join([self.my_hand, 'xx', 'xx']), ''.join(received_packet['boardcards']), 
                "", ITER_TABLE[self.num_boardcards])
        else:
            self.fold_thres = TWO_FOLD_THRES
            self.raise_thres = TWO_RAISE_THRES
            self.reraise_thres = TWO_RERAISE_THRES
            equity = pbots_calc.calc(':'.join([self.my_hand, 'xx']), ''.join(received_packet['boardcards']), 
                "", ITER_TABLE[self.num_boardcards])

        equity = equity.ev[0]
        do_reraise = random.random() > self.reraise_thres

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

        # statistician.updateOpponentStatistics(received_packet)
        print repr(received_packet['last_action'])
        self.list_of_stacksizes = received_packet['stack_size']
        self.my_stacksize       = self.list_of_stacksizes[self.my_seat - 1]
        self.potsize            = received_packet['potsize']

        last_actions = received_packet['last_action']
        for act in last_actions:
            sp = act.split(":")
            name = sp[-1]
            if name in self.opp_dict:
                self.opp_dict[name].last_action = sp[0]
                if sp[0] == FOLD:
                    self.opp_dict[name].status = FOLDED

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
        pass
        # statistician.updateOpponentStatistics(received_packet)



    def requestkeyvalue_handler(self, received_packet):
        # At the end, the engine will allow your bot save key/value pairs.
        # Send FINISH to indicate you're done.
        # s.send("PUT quan sucks\n")
        # s.send("PUT samarth best\n")
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
