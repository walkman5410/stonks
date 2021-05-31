import urllib.request, json 
from CompanyAnalyzer import getEightPillars
from eightpillars.models import EightPillarData

from django.utils import timezone

def importData():
    with urllib.request.urlopen("https://pkgstore.datahub.io/core/nyse-other-listings/nyse-listed_json/data/e8ad01974d4110e790b227dc1541b193/nyse-listed_json.json") as url:
        data = json.loads(url.read().decode())
        x = 1
        countOfData = len(data)
        for i in data:
            try:
                pillar_data = json.loads(getEightPillars(i['ACT Symbol']))

                ticker, created = EightPillarData.objects.get_or_create(ticker=i['ACT Symbol'])

                ticker.market_cap = pillar_data['market_cap']
                ticker.Eps = pillar_data['Eps']
                ticker.Pe = pillar_data['Pe']
                ticker.is_pe_acceptable = pillar_data['is_pe_acceptable']
                ticker.profit_margin = pillar_data['profit_margin']
                ticker.is_profit_margin_acceptable = pillar_data['is_profit_margin_acceptable']
                ticker.latest_revenue = pillar_data['latest_revenue']
                ticker.is_revenue_growing = pillar_data['is_revenue_growing']
                ticker.latest_net_income = pillar_data['latest_net_income']
                ticker.is_net_income_growing = pillar_data['is_net_income_growing']
                ticker.latest_shares_outstanding = pillar_data['latest_shares_outstanding']
                ticker.shares_outstanding = pillar_data['shares_outstanding']
                ticker.are_shares_outstanding_shrinking = pillar_data['are_shares_outstanding_shrinking']
                ticker.is_quick_ratio_positive = pillar_data['is_quick_ratio_positive']
                ticker.is_cash_flow_growing = pillar_data['is_cash_flow_growing']
                ticker.average_cash_flow = pillar_data['average_cash_flow']
                ticker.is_dividend_yield_affordable = pillar_data['is_dividend_yield_affordable']
                ticker.cash_flow_value = pillar_data['cash_flow_value']
                ticker.is_market_price_worth = pillar_data['is_market_price_worth']
                ticker.last_updated = timezone.now()

                ticker.save()
            except:
                print(i['ACT Symbol'], ' failed')
            print(x, ' of ', countOfData) 
            x = x+1