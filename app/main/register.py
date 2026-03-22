import Adyen
import json
import requests
from main.config import get_basic_lem_auth, get_lem_user, get_lem_pass, get_bp_user, get_bp_pass
from flask import Flask, render_template, url_for, redirect, session
from flask_session import Session
from main import database

'''
MoR onboarding Flow
'''

def issuing_business_line(LEMid):
  """LEM v4 business line for issuing (required for Balance Platform card flows)."""
  url = "https://kyc-test.adyen.com/lem/v4/businessLines"

  user = get_lem_user()
  password = get_lem_pass()
  basic = (user, password)

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
      "legalEntityId": LEMid,
      "service": "issuing",
      "industryCode": "45391",
      "sourceOfFunds": {
          "adyenProcessedFunds": False,
          "type": "assetSale",
          "dateOfSourceEvent": "2024-12-03",
          "description": "Sale of my property at 123 45th St, Chicago, 60613.",
          "amount": {
              "currency": "USD",
              "value": 600000
          }
      },
      "webData": [
          {
              "webAddress": "https://adyen.com/"
          }
      ]
  }

  print("/businessLines (v4 issuing) request:\n" + str(payload))
  session['blReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data=json.dumps(payload), headers=headers, auth=basic)

  print("/businessLines (v4 issuing) response:\n" + response.text, response.status_code, response.reason)
  print(response.headers)

  if response.status_code == 200:
    node = json.loads(response.text)
    session['blRes'] = json.dumps(node, indent=2)
    return None
  return response.text


def payment_processing_business_line(LEMid):
  """LEM v4 business line for payment processing (eCommerce)."""
  url = "https://kyc-test.adyen.com/lem/v4/businessLines"

  user = get_lem_user()
  password = get_lem_pass()
  basic = (user, password)

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
      "service": "paymentProcessing",
      "industryCode": "4431A",
      "salesChannels": [
          "eCommerce"
      ],
      "legalEntityId": LEMid,
      "webData": [
          {
              "webAddress": "https://theonion.com/"
          }
      ]
  }

  print("/businessLines (v4 paymentProcessing) request:\n" + str(payload))
  session['blPaymentReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data=json.dumps(payload), headers=headers, auth=basic)

  print("/businessLines (v4 paymentProcessing) response:\n" + response.text, response.status_code, response.reason)
  print(response.headers)

  if response.status_code == 200:
    node = json.loads(response.text)
    session['blPaymentRes'] = json.dumps(node, indent=2)
    return None
  return response.text


def legal_entity(legalName, currency, country):
  url = "https://kyc-test.adyen.com/lem/v2/legalEntities"

  user = get_lem_user()
  password = get_lem_pass()

  basic = (user, password)
  platform = "test" # change to live for production

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
  "type": "organization",
    "organization": {
      "legalName": legalName,
      "type": "privateCompany",
      "registeredAddress": {
        "country": country
      }
    }
  }

  print("/legalEntities request:\n" + str(payload))
  session['leReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data = json.dumps(payload), headers = headers, auth=basic)

  print("/legalEntities response:\n" + response.text, response.status_code, response.reason)
  
  node = json.loads(response.text)
  LEMid = node['id']
  print(LEMid)
  print(response.headers)
  if response.status_code == 200:
    session['leRes'] = json.dumps(node, indent=2)
    bl_error = issuing_business_line(LEMid)
    if bl_error is not None:
      return bl_error
    bl_error_pp = payment_processing_business_line(LEMid)
    if bl_error_pp is not None:
      return bl_error_pp
    account_holder(LEMid, legalName, currency)
    return redirect(url_for('onboard_success', LEMid=LEMid))
  else:
    return response.text

def account_holder(LEMid, legalName, currency):
  url = "https://balanceplatform-api-test.adyen.com/bcl/v2/accountHolders"

  user = get_bp_user()
  password = get_bp_pass()

  basic = (user, password)
  platform = "test" # change to live for production

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
    "description": LEMid,
    "reference": f"{legalName} Company Account Holder",
    "legalEntityId": LEMid
  }

  print("/accountHolders request:\n" + str(payload))
  session['ahReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data = json.dumps(payload), headers = headers, auth=basic)

  print("/accountHolders response:\n" + response.text, response.status_code, response.reason)
  
  node = json.loads(response.text)
  AHid = node['id']
  print(AHid)
  print(response.headers)
  if response.status_code == 200:
    session['ahRes'] = json.dumps(node, indent=2)
    balance_account(AHid, currency, legalName, LEMid)
    return response.text
  else:
    return response.text


def balance_account(AHid, currency, legalName, LEMid):
  url = "https://balanceplatform-api-test.adyen.com/bcl/v2/balanceAccounts"

  user = get_bp_user()
  password = get_bp_pass()

  basic = (user, password)
  platform = "test" # change to live for production

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
    "description": f"{legalName} Balance Account",
    "accountHolderId": AHid,
    "defaultCurrencyCode": currency
  }

  print("/balanceAccounts request:\n" + str(payload))
  session['baReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data = json.dumps(payload), headers = headers, auth=basic)

  print("/balanceAccounts response:\n" + response.text, response.status_code, response.reason)
  
  LEMid = LEMid
  node = json.loads(response.text)
  BAid = node['id']
  print(BAid)
  print(response.headers)
  if response.status_code == 200:
    session['baRes'] = json.dumps(node, indent=2)
    print(LEMid)
    database.insert_ba(LEMid, BAid)
    return response.text
  else:
    return response.text

#adyen_payment_links()
