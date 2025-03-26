import pandas as pd
from risk_score_algos import *
import json
from transformers import LlamaTokenizer, LlamaForCausalLM, pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from sec_edgar import *

def prompToLLAMA(prompt):    

    pipe = pipeline("text-generation", model="baffo32/decapoda-research-llama-7B-hf")

    tokenizer = AutoTokenizer.from_pretrained("baffo32/decapoda-research-llama-7B-hf")
    model = AutoModelForCausalLM.from_pretrained("baffo32/decapoda-research-llama-7B-hf")
    
    # Tokenize the prompt
    inputs = tokenizer(prompt, return_tensors="pt")

    # Generate a response from the model
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=200, num_return_sequences=1)

    # Decode the generated response
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return str(generated_text)


def getOutputJson():

    #change the paths to relative
    input_df = pd.read_csv('C:/Users/melod/OneDrive/Ramya/Wells Fargo/Global Tech Hackathon 2025/aidel-ai-thena/code/src/uploads/input.csv')
    no_of_txns = len(input_df)

    entity_df = pd.read_csv('C:/Users/melod/OneDrive/Ramya/Wells Fargo/Global Tech Hackathon 2025/aidel-ai-thena/code/src/entity_info.csv')
    
    reputation_df = pd.read_csv('C:/Users/melod/OneDrive/Ramya/Wells Fargo/Global Tech Hackathon 2025/aidel-ai-thena/code/src/reputation_risk_summary.csv')

    start_row = 0
    resList = []

    for i in range(no_of_txns):

        txn_amount = input_df['Amount'][i]
        payer = input_df['PayerName'][i]
        rcvr = input_df['Receiver Name'][i]
        txn_id = input_df['Transaction ID'][i]

        ofac_party1 = entity_df['Sanction'][start_row]
        ofac_party2 = entity_df['Sanction'][start_row+1]

        sec_edgar_score = 1 - min(compute_sec_edgar_score(payer, dataframes, years),compute_sec_edgar_score(rcvr, dataframes, years))
        sec_edgar_filings = get_unique_form_types(payer, dataframes, years)

        rep_risk_party1 = reputation_df['reputation_risk_score'][start_row]
        rep_risk_party2 = reputation_df['reputation_risk_score'][start_row+1]

        base_risk = (rep_risk_party1+rep_risk_party2)/2

        ekata_score = ekata_risk_score(base_risk,txn_amount,ofac_party1,ofac_party2) #3 Accuracy 0.87
        plaid_score = plaid_risk_score(base_risk,ofac_party1,ofac_party2) #1 Accuracy 0.95
        maxmind_score = maxmind_risk_score(base_risk,payer,txn_amount) #2 Accuracy 0.92
        flagright_score = flagright_risk_score(base_risk,txn_amount,ofac_party1,ofac_party2) #4 Accuracy 0.83
        model_confidence_score = 0.4*0.95 + 0.3*0.92 + 0.2*0.87 + 0.1*0.83

        cumulative_risk_score = (sec_edgar_score*0.3) + (0.3*max(rep_risk_party1,rep_risk_party2)) + (0.2 if (ofac_party1=="Yes" or ofac_party2=="Yes") else 0) + (0.4*plaid_score + 0.3*maxmind_score + 0.2*ekata_score + 0.1*flagright_score)

        start_row+=2
        # print(reputation_df.iloc[1:3,:])

        
        base_prompt = f"""

            You are an AI Analyst who is asked to compute the risk in a transation whose details are given in the below csv data:

            {input_df.iloc[i]}

            The details on the extracted entities(payer and receiver) and sanction information is present in the below csv data:

            {entity_df.iloc[start_row:start_row+2,:]}

            The details on the reputational information of the payer and reveiver is present in the below csv data:

            {reputation_df.iloc[start_row:start_row+2,:]}

            The payer company is sanctioned in OFAC List: {ofac_party1}
            The receiver company is sanctioned in OFAC List: {ofac_party2}

            SEC EDGAR score is {sec_edgar_score}

            The risk scores computed by a few algos for the transaction are {ekata_score}, {plaid_score}, {maxmind_score}, {flagright_score}


        """

        prompt_evi_payer = base_prompt + f"Take the payer company {payer} and give a set of comma separated evidences based on the reputational information, OFAC mentions and other evidences to justify the transactional risk"

        prompt_evi_rcvr = base_prompt + f"Take the receiver company {rcvr} and give a set of comma separated evidences based on the reputational information, OFAC mentions and other evidences to justify the transactional risk"

        prompt_reason = base_prompt + f"Consider a transaction from the payer company {payer} to the receiver company {rcvr}. Based on supporting eveidences from reputational information, OFAC mentions and other evidences give a reason to justify the transactional risk score. Give a concise answer considering the elements of confidence and risk in the entities to do so"

        result = dict()
        result["Transaction ID"]=txn_id
        result["Extracted Entity"]=[payer,rcvr]
        result["Risk Score"] = cumulative_risk_score
        result["Supporting Evidence"] = [prompToLLAMA(prompt_evi_payer),prompToLLAMA(prompt_evi_rcvr)]
        result["Confidence Score"]=model_confidence_score
        result["Reason"] = prompToLLAMA(prompt_reason)
        resList.append(result)


    with open("output1.json", "w", encoding="utf-8") as json_file:
        json.dump(resList, json_file, indent=4, ensure_ascii=False)



        
       

getOutputJson()


