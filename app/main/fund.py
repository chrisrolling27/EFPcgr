import Adyen
import json
import uuid
import requests
from main.config import get_basic_lem_auth, get_lem_user, get_lem_pass, get_bp_user, get_bp_pass, get_adyen_api_key, get_adyen_merchant_account
from flask import Flask, render_template, url_for, redirect, session
from flask_session import Session
from main import database

'''
Add funds to the account
'''

def funding(balance_account, amount, currency):
  url = "https://balanceplatform-api-test.adyen.com/btl/v4/transfers"

  user = get_bp_user()
  password = get_bp_pass()

  basic = (user, password)
  platform = "test" # change to live for production

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
    "amount": {
        "value": amount,
        "currency": currency
    },
    "balanceAccountId": "BA3227C223222B5GGM9D6DJW8",
    "category": "internal",
    "counterparty": {
        "balanceAccountId": balance_account
    },
    "referenceForBeneficiary": "Top-up",
    "reference": "Top-up",
    "description": "Top-up"
    }

  print("/transfers request:\n" + str(payload))
  session['txReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data = json.dumps(payload), headers = headers, auth=basic)

  print("/transfers response:\n" + response.text, response.status_code, response.reason)

  node = json.loads(response.text)
  transfer_id = node['id']
  status = node['status']
  reason = node['reason']
  date = node['creationDate']
  data = response.text

  
  print(response.headers)
  if response.status_code == 422:
    node = json.loads(response.text)
    reason = node['invalidFields'][0]['message']
    print(reason)
    return reason
  if response.status_code == 200:
    session['txRes'] = json.dumps(node, indent=2)
    database.insert_tx(transfer_id, amount, date, balance_account)
    tx_result = status
    print(tx_result)
    return tx_result
  else:
    return response.text



