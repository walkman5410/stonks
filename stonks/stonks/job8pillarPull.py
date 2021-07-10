import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pidjango.settings") 
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from django.conf import settings
import yahoo_fin.stock_info as si
import urllib.request, json 
from CompanyAnalyzer import getEightPillars
from eightpillars.models import EightPillarData, failedTickers

from django.utils import timezone

def updateData(data, name):
    x = 1
    countOfData = len(data)    
    for i in data:
        try:
            pillar_data = json.loads(getEightPillars(i))

            ticker, created = EightPillarData.objects.get_or_create(ticker=i)

            ticker.company_name = pillar_data['company_name']
            ticker.market_cap = pillar_data['market_cap']
            ticker.Eps = pillar_data['Eps']
            ticker.Pe = pillar_data['Pe']
            ticker.is_pe_acceptable = pillar_data['is_pe_acceptable']
            ticker.profit_margin = pillar_data['profit_margin']
            ticker.is_profit_margin_acceptable = pillar_data['is_profit_margin_acceptable']
            ticker.latest_revenue = pillar_data['latest_revenue']
            ticker.earliest_revenue = pillar_data['earliest_revenue']
            ticker.is_revenue_growing = pillar_data['is_revenue_growing']
            ticker.latest_net_income = pillar_data['latest_net_income']
            ticker.earliest_net_income = pillar_data['earliest_net_income']
            ticker.is_net_income_growing = pillar_data['is_net_income_growing']
            ticker.latest_shares_outstanding = pillar_data['latest_shares_outstanding']
            ticker.earliest_shares_outstanding = pillar_data['earliest_shares_outstanding']
            ticker.shares_outstanding = pillar_data['shares_outstanding']
            ticker.are_shares_outstanding_shrinking = pillar_data['are_shares_outstanding_shrinking']
            ticker.quick_ratio = pillar_data['quick_ratio']
            ticker.is_quick_ratio_positive = pillar_data['is_quick_ratio_positive']
            ticker.is_cash_flow_growing = pillar_data['is_cash_flow_growing']
            ticker.latest_free_cash_flow = pillar_data['latest_free_cash_flow']
            ticker.earliest_free_cash_flow = pillar_data['earliest_free_cash_flow']
            ticker.average_cash_flow = pillar_data['average_cash_flow']
            ticker.is_dividend_yield_affordable = pillar_data['is_dividend_yield_affordable']
            ticker.cash_flow_value = pillar_data['cash_flow_value']
            ticker.is_market_price_worth = pillar_data['is_market_price_worth']
            ticker.last_updated = timezone.now()

            ticker.save()
        except Exception as e:
            print(i, ' failed due to: ',e)
            ticker, created = failedTickers.objects.get_or_create(ticker=i)
            ticker.errorDesc = e
            ticker.save()
        print(name, ': ', x, ' of ', countOfData) 
        x = x+1
updateData(si.tickers_dow(), 'DOW')
updateData(si.tickers_nasdaq(), 'NASDAQ')
updateData(si.tickers_other(), 'OTHER')
updateData(si.tickers_sp500(), 'S&P500')