"""Synthetic TrainCrest learner-support tickets (fictional, no real data).
Shared by drills in Module 01 and Module 03."""

CATEGORIES = ["scheduling", "billing", "exam_voucher", "certificate", "lab_access", "account", "other"]

# TrainCrest house rules the model can't know unless you tell it:
#   - a refund request is "billing", even when it mentions dates or batches
#   - asking for more lab time is "lab_access", not "scheduling"
TEST_TICKETS = [
    ("I paid for the AZ-305 batch but my card was charged twice.", "billing"),
    ("Can I move my Generative AI course from the March batch to April?", "scheduling"),
    ("I finished the course two weeks ago and still have no exam voucher.", "exam_voucher"),
    ("My certificate says 'Asha Kumari' but my name is 'Asha Kumar'.", "certificate"),
    ("The lab VM says my subscription has expired, I can't start the exercise.", "lab_access"),
    ("I can't log in, the password reset email never arrives.", "account"),
    ("Do you offer corporate discounts for a team of 20 engineers?", "other"),
    ("My lab ran out yesterday, can I get one more week to finish?", "lab_access"),
    ("Quiero cambiar mi curso al grupo del próximo mes.", "scheduling"),
    ("I want a refund, the course starts in 3 days and I can't attend.", "billing"),
    ("The voucher code you sent shows as already used.", "exam_voucher"),
    ("Please update the email on my account to my new work address.", "account"),
]

# Few-shot examples: different from the test tickets, covering the house rules.
FEW_SHOT_EXAMPLES = [
    ("I can't attend next week, please refund my fee.", "billing"),
    ("I need 5 more days of lab access to finish module 6.", "lab_access"),
    ("I was charged in EUR instead of USD.", "billing"),
    ("My voucher expired before I could book the exam.", "exam_voucher"),
    ("Please shift me to the weekend batch.", "scheduling"),
]
