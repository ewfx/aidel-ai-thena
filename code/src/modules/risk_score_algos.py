import random

def ekata_risk_score(base_risk,txn_amount,ofac_party1,ofac_party2):
    
    if txn_amount > 10000:
        base_risk += 0.2
    if ofac_party1=="Yes" or ofac_party2=="Yes":
        base_risk += 0.3
    
    risk_score = base_risk * 100 + random.uniform(-5, 5)    
    return risk_score

def plaid_risk_score(base_risk,ofac_party1,ofac_party2):
    
    if ofac_party1=="Yes" or ofac_party2=="Yes":
        base_risk += 0.15

    risk_score = (1 - base_risk) * 100 + random.uniform(-5, 5)
    return risk_score

def maxmind_risk_score(base_risk,payer,txn_amount):
    
    if payer=="" or payer is None:
        base_risk += 0.2
    if txn_amount > 5000:
        base_risk += 0.1
    
    risk_score = base_risk * 120
    return risk_score

def flagright_risk_score(base_risk,txn_amount,ofac_party1,ofac_party2):
    
    if ofac_party1=="Yes" or ofac_party2=="Yes":
        base_risk += 0.25
    if txn_amount > 20000:
        base_risk += 0.2
    
    risk_score = base_risk * 100
    return risk_score
