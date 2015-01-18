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

FOLD_THRES = 0.3
POWER = 4



ITER_TABLE = {0 : 100000, 3:10000, 4:1000, 5:100}

# print pbots_calc.calc("AhKh:xx", "ThJhQh2s7s", "", 1)
# print pbots_calc.calc("AhKh:xx:xx", "JhQh2s7s", "", 100)

class Player:

    def __init__ (self):
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
        my_seat = received_packet['seat']
        self.list_of_stacksizes = received_packet['stack_size']
        self.my_original_stacksize = self.list_of_stacksizes[my_seat - 1]
        self.hand_id = received_packet['handID']
        self.num_active_players = received_packet['num_active_players']
        self.list_of_active_players = received_packet['active_players']


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


    def get_best_action(self, received_packet, avail_actions = []):
        equity = None
        if received_packet['num_active_players'] == 3:
            equity = pbots_calc.calc(':'.join([self.my_hand, 'xx', 'xx']), ''.join(received_packet['boardcards']), 
                "", ITER_TABLE[received_packet['num_boardcards']])
        else:
            equity = pbots_calc.calc(':'.join([self.my_hand, 'xx']), ''.join(received_packet['boardcards']), 
                "", ITER_TABLE[received_packet['num_boardcards']])

        equity = equity.ev[0]
        if equity < FOLD_THRES:
            if CHECK in avail_actions:
                return CHECK
            return FOLD

        else: 
            winning_factor = ((equity - FOLD_THRES) / (1 - FOLD_THRES))**POWER
            if BET in avail_actions:
                amount = self.bet_handler(winning_factor)
                return BET + ":" + str(amount)
            elif RAISE in avail_actions:
                amount = self.raise_handler(winning_factor)
                return RAISE + ":" + str(amount)

        return CHECK

    def getaction_handler(self, received_packet):
        # hand_equity = 

        # for action in received_packet['last_action']:
        #     split_action = action.split(":")

        # statistician.updateOpponentStatistics(received_packet)

        for action in received_packet['legal_actions']:
            split_action = action.split(":")

            if split_action[0] == BET:
                self.minBet = int(split_action[1])
                self.maxBet = int(split_action[2])
            elif split_action[0] == RAISE:
                self.minRaise = int(split_action[1])
                self.maxRaise = int(split_action[2])
        
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
