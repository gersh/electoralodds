import requests
import json

def get_prices(url):
    r = requests.get(url)
    j = json.loads(str(r.content, 'utf-8'))
    contracts = j['contracts']

    ps = {}
    for contract in contracts:
        bid = contract['bestSellYesCost']
        ask = contract['bestBuyYesCost']
        last = contract['lastTradePrice']
        if bid and ask: 
            if last and last >= bid and last <= ask:
                price = last
            else:
                price = (bid+ask)/2.0
            ps[contract['name']] = [bid,ask,price]
    return ps

def get_odds():
    demPrices = get_prices('https://www.predictit.org/api/marketdata/markets/3633')
    presidentialPrices = get_prices('https://www.predictit.org/api/marketdata/markets/3698')

    electabilityPctLow = {}
    electabilityPctHigh = {}
    electabilityPct = {}
    for k in demPrices:
        if k in presidentialPrices and demPrices[k][2] > 0.02 and presidentialPrices[k][2] > 0.02:
            electabilityPctLow[k] = presidentialPrices[k][0]/demPrices[k][1]
            electabilityPctHigh[k] = presidentialPrices[k][1]/demPrices[k][0]
            electabilityPct[k] = presidentialPrices[k][2]/demPrices[k][2]

    return electabilityPctLow,electabilityPctHigh,electabilityPct

