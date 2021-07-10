import pandas as pd
import json
import requests
from lxml import etree 

def getEightPillars(tickerSymbol):   
    site = 'https://finance.yahoo.com/quote/'+tickerSymbol+'/balance-sheet?p='+tickerSymbol
    headers = {'User-agent': 'Mozilla/5.0'}
    html = requests.get(url=site, headers=headers).text
    json_str = html.split('root.App.main =')[1].split('(this)')[0].split(';\n}')[0].strip()
    json_data = json.loads(json_str)  

    site2 = 'https://www.sharesoutstandinghistory.com/?symbol='+tickerSymbol
    html2 = requests.get(url=site2, headers=headers).text
    tree = etree.HTML(html2)

    company_name = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['quoteType']['longName']

    currPrice = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['price']['regularMarketPrice']['raw']

    sharesOutstanding = json_data['context']['dispatcher']['stores']['StreamDataStore']['quoteData'][tickerSymbol]['sharesOutstanding']['raw']
    market_cap = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']['marketCap']['raw']

    #PE Ratio missing                                                           
    #                                                                           Formula: Price / EPS
    #Using Trailing (past performance) PE
    Pe = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']['trailingPE']['raw'] if 'trailingPE' in json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']  else None

    #                                                                           Formula: (Price * Shares Outstanding) * dividend yield
    dividendsPaid = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['dividendsPaid']['raw'] if 'dividendsPaid' in json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0] else 0 #Ensure the dividends paid is supported by free cash flow

    #4 year income statement comparison

    #Revenue
    latest_revenue = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['totalRevenue']['raw']
    earliest_revenue = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][3]['totalRevenue']['raw']

    #Net Income
    latest_net_income = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['netIncome']['raw']
    earliest_net_income = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][3]['netIncome']['raw']
    
    #profit margin calc
    profit_margin = latest_net_income / latest_revenue # netincome/revenue

    #Using Trailing (past performance) EPS
    Eps = latest_net_income / sharesOutstanding #Formula: (Net Income - Preferred Dividends) / Shares Outstanding

    #Shares Outstanding    
    tbl = {}
    for i in tree.cssselect('td.tstyle'):
        if i.text == None:
            key = i[0].text
        else:
            tbl[key] = i.text
    df = pd.DataFrame.from_dict(tbl, orient='index',columns=['sharesOutstanding']) 
    df1 = df['sharesOutstanding'].str.strip('$').str.extract(r'(\d+\.\d+)([BMK]+)')
    df['sharesOutstanding'] = df1[0].astype(float) * df1[1].map({'B': 1000000000, 'M':1000000, 'K':1000})                
    latest_shares_outstanding = int(df.iloc[[-1]]['sharesOutstanding']) 
    try:
        earliest_shares_outstanding = int(df.iloc[[-21]]['sharesOutstanding'])    
    except IndexError:
        earliest_shares_outstanding = 0

    #Current Assets over Current Liabilities
    current_assets = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][0]['totalCurrentAssets']['raw']
    current_liabilities = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][0]['totalCurrentLiabilities']['raw']

    try:
        #Free Cash Flow
        #                                                                                       Formula: Cash from Operations - Net Change in Capital Expenditures
        latest_cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['totalCashFromOperatingActivities']['raw']
        latest_capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['capitalExpenditures']['raw']
        latest_free_cash_flow = latest_cash_from_operations + latest_capital_expenditures
        earliest_cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][3]['totalCashFromOperatingActivities']['raw']
        earliest_capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][3]['capitalExpenditures']['raw']
        earliest_free_cash_flow = earliest_cash_from_operations + earliest_capital_expenditures


        free_cash_flow = 0
        for i in range(0, 4):
            cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][i]['totalCashFromOperatingActivities']['raw']
            capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][i]['capitalExpenditures']['raw']
            free_cash_flow += (cash_from_operations + capital_expenditures)
        average_cash_flow = free_cash_flow/4
        cash_flow_minus_dividend = average_cash_flow - dividendsPaid if dividendsPaid else average_cash_flow
        cash_flow_value = average_cash_flow * 20
    except:
        latest_free_cash_flow = None
        earliest_free_cash_flow = None
        average_cash_flow = None
        cash_flow_minus_dividend = None
        cash_flow_value = None

    data = {}

    data['company_name'] = company_name
    data['market_cap'] = market_cap
    data['Eps'] = int(Eps) if pd.notnull(Eps) else int(0)
    data['Pe'] = int(Pe)
    data['is_pe_acceptable'] = bool(Pe < 20) if pd.notnull(Pe) and Pe != 0 else False
    data['profit_margin'] = profit_margin
    data['is_profit_margin_acceptable'] = bool(profit_margin > .1)
    data['latest_revenue'] = int(latest_revenue)
    data['earliest_revenue'] = int(earliest_revenue)
    data['is_revenue_growing'] = bool(latest_revenue > earliest_revenue)
    data['latest_net_income'] = int(latest_net_income)
    data['earliest_net_income'] = int(earliest_net_income)
    data['is_net_income_growing'] = bool(latest_net_income > earliest_net_income)
    data['earliest_shares_outstanding'] = int(earliest_shares_outstanding) if earliest_shares_outstanding else None
    data['latest_shares_outstanding'] = int(latest_shares_outstanding) if latest_shares_outstanding else None
    data['shares_outstanding'] = int(sharesOutstanding)
    data['are_shares_outstanding_shrinking'] = bool(latest_shares_outstanding < earliest_shares_outstanding) if earliest_shares_outstanding and latest_shares_outstanding else None
    data['quick_ratio'] = (current_assets / current_liabilities)
    data['is_quick_ratio_positive'] = bool((current_assets / current_liabilities) > 1)
    data['latest_free_cash_flow'] = int(latest_free_cash_flow) if latest_free_cash_flow else None
    data['earliest_free_cash_flow'] = int(earliest_free_cash_flow) if earliest_free_cash_flow else None
    data['is_cash_flow_growing'] = bool(latest_free_cash_flow > earliest_free_cash_flow) if latest_free_cash_flow else None
    data['average_cash_flow'] = int(average_cash_flow) if average_cash_flow else None
    data['is_dividend_yield_affordable'] = bool(cash_flow_minus_dividend > 0) if cash_flow_minus_dividend else None
    data['cash_flow_value'] = int(cash_flow_value) if cash_flow_value else None
    data['is_market_price_worth'] = bool(market_cap < cash_flow_value) if cash_flow_value else None

    data = json.dumps(data)

    return data