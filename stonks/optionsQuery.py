from yahoo_fin import options
import pandas as pd
import numpy as np
import json
import requests
from lxml import etree
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stonks.settings") 
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from eightpillars.models import EightPillarData
from django.utils import timezone

tickerList = EightPillarData.objects.filter(
    is_pe_acceptable = False,
    is_profit_margin_acceptable = True,
    is_revenue_growing = True,
    is_net_income_growing = True,
    is_quick_ratio_positive = True,
    is_cash_flow_growing = True,
    is_dividend_yield_affordable = True,
    is_market_price_worth = False,
    last_updated__gte = timezone.now() - timezone.timedelta(days=10)        
).values('ticker')
for i, tickerSymbol in enumerate(tickerList):
    try:
        site = 'https://finance.yahoo.com/quote/'+tickerSymbol['ticker']+'/balance-sheet?p='+tickerSymbol['ticker']
        headers = {'User-agent': 'Mozilla/5.0'}
        html = requests.get(url=site, headers=headers).text
        json_str = html.split('root.App.main =')[1].split('(this)')[0].split(';\n}')[0].strip()
        json_data = json.loads(json_str)  

        #get the options from a specific ticker
        expiration_date = 'January 21, 2022'
        putsList = options.get_puts(tickerSymbol['ticker'], expiration_date)
        
        #get current price
        currPrice = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['price']['regularMarketPrice']['raw']
        putsList['putsReturn'] = putsList['Last Price'] / putsList['Strike']
        reslt = putsList[(putsList['Strike'] < currPrice) & (putsList['putsReturn'] > .12)]
        if i == 0:
                finalList = reslt
        if not reslt.empty:
            frames = [finalList, reslt]
            finalList = pd.concat(frames)
            print('found another 1')
        else:
            print('Empty')
    except Exception as e:
        print(e)
finalList.to_csv('putsWith12PercReturn.csv')