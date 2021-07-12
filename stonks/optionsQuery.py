from yahoo_fin import options
import pandas as pd
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
).values('ticker', 'cash_flow_value', 'shares_outstanding')
finalList = pd.DataFrame()
for tickerSymbol in tickerList:
    try:
        #get the options from a specific ticker
        expiration_date = 'January 21, 2022'
        putsList = options.get_puts(tickerSymbol['ticker'], expiration_date)
        
        #get current price
        acceptablePrice = tickerSymbol['cash_flow_value'] / tickerSymbol['shares_outstanding']

        putsList['putsReturn'] = putsList['Last Price'] / putsList['Strike']
        reslt = putsList[(putsList['Strike'] < acceptablePrice) & (putsList['putsReturn'] > .08) & (putsList['Ask'] > 0) & (pd.to_datetime(putsList['Last Trade Date']) > pd.Timestamp('now').floor('D') + pd.Timedelta(-8, unit='D'))]

        if not reslt.empty:
            frames = [finalList, reslt]
            finalList = pd.concat(frames)
            print('found another 1')
        else:
            print('Empty')

    except Exception as e:
        print("Error: ",e)

finalList.to_csv('putsWith12PercReturn.csv')        