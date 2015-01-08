
#Parsing the new game packet
def parse_newgame(data):
	parsed_dict = {}
	parsed_dict['packet_name'] = data.split()[0]
	parsed_dict['player_name'] = data.split()[1]
	parsed_dict['opponent_1_name'] = data.split()[2]
	parsed_dict['opponent_2_name'] = data.split()[3]
	parsed_dict['stack_size'] = int(data.split()[4])
	parsed_dict['big_blind'] = int(data.split()[5])
	parsed_dict['num_hands'] = int(data.split()[6])
	parsed_dict['timeBank'] = float(data.split()[7])
	return parsed_dict

#Parsing the new hand packet
def parse_newhand(data):
	parsed_dict = {}
	parsed_dict['packet_name'] = data.split()[0]
	parsed_dict['handID'] = int(data.split()[1])
	parsed_dict['seat'] = int(data.split()[2])
	parsed_dict['hand'] = data.split()[3] + data.split()[4]
	parsed_dict['stack_size'] = [int(data.split()[5]), int(data.split()[6]), int(data.split()[7])]	
	parsed_dict['num_active_players'] = int(data.split()[8])
	parsed_dict['active_players'] = [data.split()[9], data.split()[10], data.split()[11]]
	parsed_dict['timeBank'] = float(data.split()[12])
	return parsed_dict

def parse_getaction(data): #<<<<<< Most important Packet.
	parsed_dict = {}
	parsed_dict['packet_name'] = data.split()[0]
	parsed_dict['potsize'] = int(data.split()[1])
	parsed_dict['num_boardcards'] = int(data.split()[2])
	total_boarcards = int(data.split()[2])
	#Adding cards on the board to the hash table
	boardcards = []
	count = 1
	while count <= total_boarcards:
		boardcards.append(data.split()[2 + count])
		count += 1
	parsed_dict['boardcards'] = boardcards
	index_board = 2 + total_boarcards
	
	#parsing stack sizes for each player 
	parsed_dict['stack_size'] = [data.split()[index_board + 1], data.split()[index_board + 2], data.split()[index_board + 3]]
	index_stackSize = index_board + 3
	parsed_dict['num_active_players'] = data.split()[index_stackSize + 1]
	parsed_dict['active_players'] = [data.split()[index_stackSize + 2], data.split()[index_stackSize + 3], data.split()[index_stackSize + 4]]
	parsed_dict['num_last_action'] = int(data.split()[index_stackSize + 5])
	
	index_last_action = index_stackSize + 5
	last_action_list = []
	count = 1
	while count <= parsed_dict['num_last_action']:
		last_action_list.append(data.split()[count + index_last_action])
		count += 1 
	parsed_dict['last_action'] = last_action_list

	index_legal_action = index_last_action + parsed_dict['num_last_action']
	parsed_dict['num_legal_actions'] = int(data.split()[index_legal_action + 1])
	legal_actions_list = []
	count = 1
	while count <= parsed_dict['num_legal_actions']:
		legal_actions_list.append(data.split()[count + index_legal_action + 1])
		count += 1
	parsed_dict['legal_actions'] = legal_actions_list
	parsed_dict['timeBank'] = float(data.split()[len(data.split()) - 1])
	return parsed_dict

def parse_packet(data):
	parsed_map = {}
	packet_type = data.split()[0]
	if packet_type == "NEWGAME":
		parsed_map = parse_newgame(data)

	return parsed_map
