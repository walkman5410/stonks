from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from collections import defaultdict

from .forms import TickerForm

import yfinance as yf
import yahoo_fin.stock_info as si
import pandas as pd

class HomePage(generic.TemplateView):
    template_name = 'eightpillars/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tickerform'] = TickerForm()
        return context

def get_the_pillars(request):
    data = {}
    status = 200
    if request.method == 'GET':
        tickerSymbol = request.GET.get('tickerSymbol')
        quoteTbl = si.get_quote_table(tickerSymbol)
        income_statement = si.get_income_statement(tickerSymbol)
        balance_sheet = si.get_balance_sheet(tickerSymbol)
        cash_flow_statement = si.get_cash_flow(tickerSymbol)
        yf_data = yf.Ticker(tickerSymbol)

        currPrice = quoteTbl["Quote Price"]

        sharesOutstanding = yf_data.info['sharesOutstanding'] 
        market_cap = yf_data.info['marketCap'] 

        #EPS missing                                                                
        #                                                                           Formula: (Net Income - Preferred Dividends) / Shares Outstanding
        #Using Trailing (past performance) EPS
        Eps = quoteTbl["EPS (TTM)"]

        #PE Ratio missing                                                           
        #                                                                           Formula: Price / EPS
        #Using Trailing (past performance) PE
        Pe = quoteTbl["PE Ratio (TTM)"]

        #determine what a good profit margin is
        profit_margin = yf_data.info['profitMargins']
        is_profit_margin_good = profit_margin > .1
        dividendYield = yf_data.info['dividendYield'] 
        #                                                                           Formula: (Price * Shares Outstanding) * dividend yield
        dividendsPaid = (currPrice * sharesOutstanding) * dividendYield if dividendYield else None #Ensure the dividends paid is supported by free cash flow

        #4 year income statement comparison

        #Revenue
        latest_revenue = income_statement[income_statement.columns[0]][income_statement.index.get_loc('totalRevenue')]
        earliest_revenue = income_statement[income_statement.columns[3]][income_statement.index.get_loc('totalRevenue')]
        is_revenue_growing = latest_revenue > earliest_revenue

        #Net Income
        latest_net_income = income_statement[income_statement.columns[0]][income_statement.index.get_loc('netIncome')]
        earliest_net_income = income_statement[income_statement.columns[3]][income_statement.index.get_loc('netIncome')]
        is_net_income_growing = latest_net_income > earliest_net_income

        #Shares Outstanding
        latest_shares_outstanding = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('commonStock')]
        earliest_shares_outstanding = balance_sheet[balance_sheet.columns[3]][balance_sheet.index.get_loc('commonStock')]
        is_shares_outstanding_growing = latest_shares_outstanding > earliest_shares_outstanding

        #Current Assets over Current Liabilities
        current_assets = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentAssets')]
        current_liabilities = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentLiabilities')]
        is_quick_ratio_positive = (current_assets / current_liabilities) > 1

        #Free Cash Flow
        #                                                                                       Formula: Cash from Operations - Net Change in Capital Expenditures
        latest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
        latest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('capitalExpenditures')]
        latest_free_cash_flow = latest_cash_from_operations + latest_capital_expenditures
        earliest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
        earliest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('capitalExpenditures')]
        earliest_free_cash_flow = earliest_cash_from_operations + earliest_capital_expenditures
        is_latest_cash_flow_positive = latest_free_cash_flow > 0
        free_cash_flow = 0
        for i in range(0, 4):
            cash_from_operations = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
            capital_expenditures = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('capitalExpenditures')]
            free_cash_flow += (cash_from_operations + capital_expenditures)

        average_cash_flow = free_cash_flow/4
        cash_flow_minus_dividend = average_cash_flow - dividendsPaid if dividendsPaid else average_cash_flow

        cash_flow_value = average_cash_flow * 20

        data['market_cap'] = market_cap
        data['Eps'] = int(Eps)
        data['Pe'] = int(Pe) if pd.notnull(Pe) else int(0)
        data['is_pe_acceptable'] = bool(Pe < 20) if pd.notnull(Pe) else False
        data['profit_margin'] = profit_margin
        data['latest_revenue'] = int(latest_revenue)
        data['is_revenue_growing'] = bool(latest_revenue > earliest_revenue)
        data['latest_net_income'] = int(latest_net_income)
        data['is_net_income_growing'] = bool(latest_net_income > earliest_net_income)
        data['latest_shares_outstanding'] = int(latest_shares_outstanding)
        data['are_shares_outstanding_shrinking'] = bool(latest_shares_outstanding < earliest_shares_outstanding)
        data['is_quick_ratio_positive'] = bool((current_assets / current_liabilities) > 1)
        data['is_cash_flow_growing'] = bool(latest_free_cash_flow > earliest_free_cash_flow)
        data['average_cash_flow'] = int(average_cash_flow)
        data['is_dividend_yield_affordable'] = bool(cash_flow_minus_dividend > 0)
        data['cash_flow_value'] = int(cash_flow_value)
        data['is_market_price_worth'] = bool(market_cap < cash_flow_value)
    else:
        data['message'] = 'You didnt give me the Ticker DUMB DUMB'
        status = 500
    return JsonResponse(data, status=status)

def get_the_pillar_table(request):
    data = {}
    status = 200
    if request.method == 'GET':
        tickerSymbol = request.GET.get('tickerSymbol')
        quoteTbl = si.get_quote_table(tickerSymbol)
        income_statement = si.get_income_statement(tickerSymbol)
        balance_sheet = si.get_balance_sheet(tickerSymbol)
        cash_flow_statement = si.get_cash_flow(tickerSymbol)
        yf_data = yf.Ticker(tickerSymbol)

        currPrice = quoteTbl["Quote Price"]

        sharesOutstanding = yf_data.info['sharesOutstanding'] 
        market_cap = yf_data.info['marketCap'] 

        #EPS missing                                                                
        #                                                                           Formula: (Net Income - Preferred Dividends) / Shares Outstanding
        #Using Trailing (past performance) EPS
        Eps = quoteTbl["EPS (TTM)"]

        #PE Ratio missing                                                           
        #                                                                           Formula: Price / EPS
        #Using Trailing (past performance) PE
        Pe = quoteTbl["PE Ratio (TTM)"]

        #determine what a good profit margin is
        profit_margin = yf_data.info['profitMargins']
        is_profit_margin_good = profit_margin > .1
        dividendYield = yf_data.info['dividendYield'] 
        #                                                                           Formula: (Price * Shares Outstanding) * dividend yield
        dividendsPaid = (currPrice * sharesOutstanding) * dividendYield if dividendYield else None #Ensure the dividends paid is supported by free cash flow

        #4 year income statement comparison

        #Revenue
        latest_revenue = income_statement[income_statement.columns[0]][income_statement.index.get_loc('totalRevenue')]
        earliest_revenue = income_statement[income_statement.columns[3]][income_statement.index.get_loc('totalRevenue')]
        is_revenue_growing = latest_revenue > earliest_revenue

        #Net Income
        latest_net_income = income_statement[income_statement.columns[0]][income_statement.index.get_loc('netIncome')]
        earliest_net_income = income_statement[income_statement.columns[3]][income_statement.index.get_loc('netIncome')]
        is_net_income_growing = latest_net_income > earliest_net_income

        #Shares Outstanding
        latest_shares_outstanding = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('commonStock')]
        earliest_shares_outstanding = balance_sheet[balance_sheet.columns[3]][balance_sheet.index.get_loc('commonStock')]
        is_shares_outstanding_growing = latest_shares_outstanding > earliest_shares_outstanding

        #Current Assets over Current Liabilities
        current_assets = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentAssets')]
        current_liabilities = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentLiabilities')]
        is_quick_ratio_positive = (current_assets / current_liabilities) > 1

        #Free Cash Flow
        #                                                                                       Formula: Cash from Operations - Net Change in Capital Expenditures
        latest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
        latest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('capitalExpenditures')]
        latest_free_cash_flow = latest_cash_from_operations + latest_capital_expenditures
        earliest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
        earliest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('capitalExpenditures')]
        earliest_free_cash_flow = earliest_cash_from_operations + earliest_capital_expenditures
        is_latest_cash_flow_positive = latest_free_cash_flow > 0
        free_cash_flow = 0
        for i in range(0, 4):
            cash_from_operations = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')]
            capital_expenditures = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('capitalExpenditures')]
            free_cash_flow += (cash_from_operations + capital_expenditures)

        average_cash_flow = free_cash_flow/4
        cash_flow_minus_dividend = average_cash_flow - dividendsPaid if dividendsPaid else average_cash_flow

        cash_flow_value = average_cash_flow * 20

        data['market_cap'] = market_cap
        data['Eps'] = int(Eps)
        data['Pe'] = int(Pe) if pd.notnull(Pe) else int(0)
        data['is_pe_acceptable'] = bool(Pe < 20) if pd.notnull(Pe) else False
        data['profit_margin'] = "{:.2%}".format(profit_margin)
        data['is_profit_margin_acceptable'] = bool(profit_margin > .1)
        data['latest_revenue'] = int(latest_revenue)
        data['is_revenue_growing'] = bool(latest_revenue > earliest_revenue)
        data['latest_net_income'] = int(latest_net_income)
        data['is_net_income_growing'] = bool(latest_net_income > earliest_net_income)
        data['latest_shares_outstanding'] = int(latest_shares_outstanding)
        data['shares_outstanding'] = int(sharesOutstanding)
        data['are_shares_outstanding_shrinking'] = bool(latest_shares_outstanding < earliest_shares_outstanding)
        data['is_quick_ratio_positive'] = bool((current_assets / current_liabilities) > 1)
        data['is_cash_flow_growing'] = bool(latest_free_cash_flow > earliest_free_cash_flow)
        data['average_cash_flow'] = int(average_cash_flow)
        data['is_dividend_yield_affordable'] = bool(cash_flow_minus_dividend > 0)
        data['cash_flow_value'] = int(cash_flow_value)
        data['is_market_price_worth'] = bool(market_cap < cash_flow_value)
    else:
        data['message'] = 'You didnt give me the Ticker DUMB DUMB'
        status = 500
    return render(request, 'eightpillars/functions/8pillartable.html', data)