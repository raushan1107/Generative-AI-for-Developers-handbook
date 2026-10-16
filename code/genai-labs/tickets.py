"""Synthetic RR Finance Bank contact-centre tickets (fictional bank, no real customer data).
Shared by drills in Module 01 and Module 03."""

CATEGORIES = ["card", "dispute", "fraud", "fees", "transfers", "loans", "account", "other"]

# RR Finance Bank house rules the model can't know unless you tell it:
#   - a charge the customer recognises but is wrong (twice, wrong amount, never delivered) is "dispute";
#     a charge they don't recognise at all is "fraud"
#   - asking for a fee to be refunded is "fees", even when it mentions a card or a transfer
TEST_TICKETS = [
    ("I was charged twice for the same flight on my credit card.", "dispute"),
    ("My debit card is missing, I think I left it in a taxi.", "card"),
    ("There's a $640 payment to a shop in another country I've never been to.", "fraud"),
    ("Why did you charge me $29? I was only overdrawn for one night.", "fees"),
    ("My transfer to my sister has been pending since Monday.", "transfers"),
    ("Can I take a payment holiday on my personal loan?", "loans"),
    ("I can't log in, the one-time code never arrives.", "account"),
    ("Do you have a branch open on Sundays?", "other"),
    ("Please refund the $45 fee you took for my international wire.", "fees"),
    ("Quiero bloquear mi tarjeta, me la robaron ayer.", "card"),
    ("The online shop charged me $89 but the order was cancelled.", "dispute"),
    ("Someone texted me a link and now money is missing from my savings.", "fraud"),
]

# Few-shot examples: different from the test tickets, covering the house rules.
FEW_SHOT_EXAMPLES = [
    ("The supermarket charged me twice for one shop.", "dispute"),
    ("I don't recognise a payment to an online casino.", "fraud"),
    ("Can you give me back the overdraft fee on my card account?", "fees"),
    ("My card was stolen at the gym.", "card"),
    ("How long does a wire to Canada take?", "transfers"),
]
