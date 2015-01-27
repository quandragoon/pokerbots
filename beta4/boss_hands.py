# Select cards
ACES   = ["As", "Ah", "Ad", "Ac"]
KINGS  = ["Ks", "Kh", "Kd", "Kc"]
QUEENS = ["Qs", "Qh", "Qd", "Qc"]
JACKS  = ["Js", "Jh", "Jd", "Jc"]
TENS   = ["Ts", "Th", "Td", "Tc"]
NINES  = ["9s", "9h", "9d", "9c"]
EIGHTS = ["8s", "8h", "8d", "8c"]

# boss-ass hands
boss_class1 = []
boss_class2 = []

# POCKET ROCKETS
for card1 in ACES:
    for card2 in ACES:
        if card1 != card2:
            boss_class1.append(card1+card2)

# POCKET KINGS
for card1 in KINGS:
    for card2 in KINGS:
        if card1 != card2:
            boss_class1.append(card1+card2)

# POCKET QUEENS
for card1 in QUEENS:
    for card2 in QUEENS:
        if card1 != card2:
            boss_class1.append(card1+card2)

# POCKET JACKS
for card1 in JACKS:
    for card2 in JACKS:
        if card1 != card2:
            boss_class1.append(card1+card2)

# POCKET TENS
for card1 in TENS:
    for card2 in TENS:
        if card1 != card2:
            boss_class1.append(card1+card2)

# ANNA KOURNIKOVA SUITED
for card1 in ACES:
    for card2 in KINGS:
        if card1[-1] == card2[-1]:
            boss_class1.append(card1+card2)
            boss_class1.append(card2+card1)

# ACE QUEEN SUITED
for card1 in ACES:
    for card2 in QUEENS:
        if card1[-1] == card2[-1]:
            boss_class2.append(card1+card2)
            boss_class2.append(card2+card1)

# ACE JACK SUITED
for card1 in ACES:
    for card2 in JACKS:
        if card1[-1] == card2[-1]:
            boss_class2.append(card1+card2)
            boss_class2.append(card2+card1)

# POCKET NINES
for card1 in NINES:
    for card2 in NINES:
        if card1 != card2:
            boss_class2.append(card1+card2)

# POCKET EIGHTS
for card1 in EIGHTS:
    for card2 in EIGHTS:
        if card1 != card2:
            boss_class2.append(card1+card2)

print boss_class1
print boss_class2

# # ROYAL COUPLE SUITED
# for card1 in KINGS:
#     for card2 in QUEENS:
#         if card1[-1] == card2[-1]:
#             boss_class1.append(card1+card2)
#             boss_class1.append(card2+card1)

# # ANNA KOURNIKOVA NOT-SUITED
# for card1 in ACES:
#     for card2 in KINGS:
#         if card1[-1] != card2[-1]:
#             boss_class2.append(card1+card2)
#             boss_class2.append(card2+card1)

# # ACE QUEEN NOT-SUITED
# for card1 in ACES:
#     for card2 in QUEENS:
#         if card1[-1] != card2[-1]:
#             boss_class2.append(card1+card2)
#             boss_class2.append(card2+card1)

# # ACE TEN
# for card1 in ACES:
#     for card2 in TEN:
#         boss_class2.append(card1+card2)
#         boss_class2.append(card2+card1)

# # KING QUEEN NOT-SUITED
# for card1 in KINGS:
#     for card2 in QUEENS:
#         if card1[-1] != card2[-1]:
#             boss_class2.append(card1+card2)
#             boss_class2.append(card2+card1)

# # KING JACK
# for card1 in KINGS:
#     for card2 in JACKS:
#         boss_class2.append(card1+card2)
#         boss_class2.append(card2+card1)

# # KING TEN
# for card1 in KINGS:
#     for card2 in TENS:
#         boss_class2.append(card1+card2)
#         boss_class2.append(card2+card1)

# # QUEEN JACK
# for card1 in QUEENS:
#     for card2 in JACKS:
#         boss_class2.append(card1+card2)
#         boss_class2.append(card2+card1)

# # QUEEN TEN
# for card1 in QUEENS:
#     for card2 in TENS:
#         boss_class2.append(card1+card2)
#         boss_class2.append(card2+card1)

