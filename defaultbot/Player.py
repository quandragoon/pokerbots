import argparse
import socket
import sys

from util import packet_parse
"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""
class Player:
    lastRaised = 0

    def makeBet(action, amount, maxBet, minBet, socket):

        if action == "RAISE" or action == "BET":
            playerBet = 0
            
            if action == "RAISE":
                amount += lastRaised
                playerBet = min(maxBet, max(minBet, amountRaised))

            elif action == "BET":
                if amount >= minBet and amount <= maxBet:
                    playerBet = amount
            
            socket.send(action + ':' + str(playerBet) + '\n')

        else:
            socket.send(action + '\n')


    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()

        opponent_1_name = ""
        opponent_2_name = ""
        my_hand = ""
        my_stacksize = 0
        list_of_stacksizes = []
        hand_id = 0
        num_active_players = 0
        list_of_active_players = []

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

            # print received_packet

            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!            
            if received_packet['packet_name'] == "NEWGAME":
                opponent_1_name = received_packet['opponent_1_name']
                opponent_2_name = received_packet['opponent_2_name']

            elif received_packet['packet_name'] == "NEWHAND":
                my_hand = received_packet['hand']
                my_seat = received_packet['seat']
                list_of_stacksizes = received_packet['stack_size']
                my_stacksize = list_of_stacksizes[my_seat - 1]
                hand_id = received_packet['handID']
                num_active_players = received_packet['num_active_players']
                list_of_active_players = received_packet['active_players']

            elif received_packet['packet_name'] == "GETACTION":
                # hand_equity = 

                for action in received_packet['last_action']:
                    split_action = action.split(":")

                    if split_action[0] == "BET" or split_action[0] == "RAISE":
                        lastRaised = split_action[1]

                
                #Compute the minimum and maximum possible bets that we can make
                minBet = 0
                maxBet = 0
                
                for response in received_packet['legal_actions']:
                    split_action = response.split(":")

                    if split_action[0] == "BET" or split_action[0] == "RAISE":
                        minBet = int(split_action[1])
                        maxBet = int(split_action[2])

                print "Minimum possible bet is: " + str(minBet)
                print "Maximum possible bet is: " + str(maxBet)

                s.send("CHECK\n")

            elif received_packet['packet_name'] == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
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