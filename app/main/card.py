import Adyen
import json
import uuid
import requests
from main.config import get_basic_lem_auth, get_lem_user, get_lem_pass, get_bp_user, get_bp_pass, get_adyen_api_key, get_adyen_merchant_account
from flask import Flask, render_template, url_for, redirect, session
from flask_session import Session
from main import database

'''
Issue a new card
'''

def create_card(balance_account, brand, variant, card_holder, country, factor, lem_id, phone):
  url = "https://balanceplatform-api-test.adyen.com/bcl/v3/paymentInstruments"

  user = get_bp_user()
  password = get_bp_pass()

  basic = (user, password)
  platform = "test" # change to live for production

  headers = {
      'Content-Type': 'application/json'
  }

  payload = {
    "type": "card",
    "balanceAccountId": balance_account,
    "issuingCountryCode": country,
    "card":
        {
        "cardholderName": card_holder,
        "brand": brand,
        "brandVariant": variant,
        "formFactor": factor,
        "authentication":
          {
            "phone": phone
          }
        }
    }

  print("/paymentInstruments request:\n" + str(payload))
  session['piReq'] = json.dumps(payload, indent=2)

  response = requests.post(url, data = json.dumps(payload), headers = headers, auth=basic)

  print("/paymentInstruments response:\n" + response.text, response.status_code, response.reason)

  print(response.headers)

  try:
    node = json.loads(response.text) if response.text else {}
  except json.JSONDecodeError:
    return response.text or "Empty or invalid JSON from paymentInstruments"

  def _error_message():
    if not isinstance(node, dict):
      return response.text or "Unknown error"
    inv = node.get("invalidFields")
    if inv and isinstance(inv, list) and len(inv) > 0:
      first = inv[0]
      if isinstance(first, dict):
        if first.get("message"):
          return first["message"]
        nested = first.get("InvalidField") or first.get("invalidField")
        if isinstance(nested, dict) and nested.get("message"):
          return nested["message"]
    return node.get("message") or node.get("errorCode") or response.text or "Request failed"

  if response.status_code == 422:
    reason = _error_message()
    print(reason)
    return reason

  if response.status_code in (200, 201):
    card_id = node.get("id")
    if not card_id:
      return _error_message()
    session['piRes'] = json.dumps(node, indent=2)
    data = response.text
    database.insert_card(card_id, lem_id, data)
    card_data = database.get_cards(lem_id)
    print(card_data)
    return card_data

  return _error_message()



