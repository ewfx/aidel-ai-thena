import pandas as pd
import numpy as np
import random
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

np.random.seed(42)

def generate_transaction_data(n=1000):
    data = {
        "transaction_id": range(1, n + 1),
        "amount": np.random.uniform(5, 5000, n),
        "merchant_category": np.random.choice(["Retail", "Food", "Travel", "Entertainment", "Electronics"], n),
        "location": np.random.choice(["US", "UK", "EU", "Asia", "Others"], n),
        "device_type": np.random.choice(["Mobile", "Desktop", "POS"], n),
        "is_fraud": np.random.choice([0, 1], n, p=[0.95, 0.05])
    }
    return pd.DataFrame(data)

def visa_risk_score(transaction):
    return transaction["amount"] * 0.3 + (transaction["is_fraud"] * 50)

def plaid_risk_score(transaction):
    return transaction["amount"] * 0.25 + (transaction["is_fraud"] * 40)

def maxmind_risk_score(transaction):
    return transaction["amount"] * 0.2 + (transaction["is_fraud"] * 30)

def ekata_risk_score(transaction):
    return transaction["amount"] * 0.15 + (transaction["is_fraud"] * 20)

def flagright_risk_score(transaction):
    return transaction["amount"] * 0.1 + (transaction["is_fraud"] * 10)

df = generate_transaction_data()
df["visa_score"] = df.apply(visa_risk_score, axis=1)
df["plaid_score"] = df.apply(plaid_risk_score, axis=1)
df["maxmind_score"] = df.apply(maxmind_risk_score, axis=1)
df["ekata_score"] = df.apply(ekata_risk_score, axis=1)
df["flagright_score"] = df.apply(flagright_risk_score, axis=1)

def train_model(feature_col):
    X_train, X_test, y_train, y_test = train_test_split(df[[feature_col]], df["is_fraud"], test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)

accuracy_results = {
    "Visa": train_model("visa_score"),
    "Plaid": train_model("plaid_score"),
    "MaxMind": train_model("maxmind_score"),
    "Ekata": train_model("ekata_score"),
    "Flagright": train_model("flagright_score")
}

print(accuracy_results)
