import pbots_calc

NUM_ITER_2 = 10000
NUM_ITER_3 = 10000


cards = ["Ah", "Ad", "Ac", "As",
		"Kh", "Kd", "Kc", "Ks",
		"Qh", "Qd", "Qc", "Qs",
		"Jh", "Jd", "Jc", "Js",
		"Th", "Td", "Tc", "Ts",
		"9h", "9d", "9c", "9s",
		"8h", "8d", "8c", "8s",
		"7h", "7d", "7c", "7s",
		"6h", "6d", "6c", "6s",
		"5h", "5d", "5c", "5s",
		"4h", "4d", "4c", "4s",
		"3h", "3d", "3c", "3s",
		"2h", "2d", "2c", "2s"]


f2 = open('precomputed2.txt', 'w')
f3 = open('precomputed3.txt', 'w')

for c1 in cards:
	for c2 in cards:
		if c1 != c2:
			hand = c1+c2
			equity2 = pbots_calc.calc(hand + ":xx", "", "", NUM_ITER_2)
			equity3 = pbots_calc.calc(hand + ":xx:xx", "", "", NUM_ITER_3)
			f2.write(hand + ' ' + str(equity2.ev[0]) + '\n')
			f3.write(hand + ' ' + str(equity3.ev[0]) + '\n')
			hand = c2+c1
			f2.write(hand + ' ' + str(equity2.ev[0]) + '\n')
			f3.write(hand + ' ' + str(equity3.ev[0]) + '\n')

f2.close()
f3.close()


