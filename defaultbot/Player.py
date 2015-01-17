import argparse
import socket
import sys
# import pbots_calc

from util import packet_parse
"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""

# Actions
RAISE = "RAISE"
BET = "BET"
FOLD = "FOLD"

class Player:

    def __init__ (self):
        self.opponent_1_name = ""
        self.opponent_2_name = ""
        self.hasPlayed_opponent_1 = False
        self.hasPlayed_opponent_2 = False
        self.my_hand = ""
        self.my_stacksize = 0
        self.list_of_stacksizes = []
        self.hand_id = 0
        self.num_active_players = 0
        self.list_of_active_players = []
        self.history_storage = {}

    def makeBet(action, amount, maxBet, minBet, socket):

        if action == RAISE or action == BET:
            playerBet = 0
            
            if action == RAISE:
                playerBet = min(maxBet, max(minBet, amount))

            elif action == BET:
                if amount >= minBet and amount <= maxBet:
                    playerBet = amount
            
            socket.send(action + ':' + str(playerBet) + '\n')

        else:
            socket.send(action + '\n')


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
                self.history_storage[received_packet['key']] = received_packet['value']

            if received_packet['packet_name'] == "NEWGAME":
                self.opponent_1_name = received_packet['opponent_1_name']
                self.opponent_2_name = received_packet['opponent_2_name']

                # If we have already played the opponent before, 
                # we load their statistics from the previous encounter
                # for this game. NOTE that Historian is just an instance of the Statistician/Historian class
                # that is not yet created. 
                if self.opponent_1_name in history_storage:
                    self.hasPlayed_opponent_1 = True
                    #Historian.updateOpponentStatistics(history_storage[opponent_1_name])

                if self.opponent_2_name in history_storage:
                    self.hasPlayed_opponent_2 = True
                    #Historian.updateOpponentStatistics(history_storage[opponent_2_name])

            elif received_packet['packet_name'] == "NEWHAND":
                self.my_hand = received_packet['hand']
                my_seat = received_packet['seat']
                self.list_of_stacksizes = received_packet['stack_size']
                self.my_stacksize = list_of_stacksizes[my_seat - 1]
                self.hand_id = received_packet['handID']
                self.num_active_players = received_packet['num_active_players']
                self.list_of_active_players = received_packet['active_players']

            elif received_packet['packet_name'] == "GETACTION":
                # hand_equity = 

                for action in received_packet['last_action']:
                    split_action = action.split(":")

                    # if split_action[0] == BET or split_action[0] == RAISE:

                #Compute the minimum and maximum possible bets that we can make
                minBet = 0
                maxBet = 0
                
                for response in received_packet['legal_actions']:
                    split_action = response.split(":")

                    if split_action[0] == BET or split_action[0] == RAISE:
                        minBet = int(split_action[1])
                        maxBet = int(split_action[2])

                s.send("CHECK\n")

            elif received_packet['packet_name'] == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                # s.send("PUT quan sucks\n")
                # s.send("PUT samarth best\n")
                s.send("FINISH\n")
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
