#lo pongo aqui arriba para que no se vea de la verguenza que da: las horas en yfinance son de españa y la sec lo pone en horarios usa crac
import requests
import urllib
from bs4 import BeautifulSoup
import xmltodict
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from tkinter import *
import statistics

import inputs_management
import solapas

def open_json(dict_name):
    with open(dict_name, 'r') as fp:
        data = json.load(fp)
    return data

def save_json(dict, dict_name):
    with open('{}.json'.format(dict_name), 'w') as fp: 
        json.dump(dict, fp)
    return 1

def json_to_df(tr):
    tr_df =  pd.DataFrame.from_dict({(i, j, k, l, m): tr[i][j][k][l][m]
                                    for i in tr.keys()
                                    for j in tr[i].keys()
                                    for k in tr[i][j].keys()
                                    for l in tr[i][j][k].keys()
                                    for m in tr[i][j][k][l].keys()})
    tr_df.index = pd.to_datetime(tr_df.index)
    return tr_df.sort_index()

def group_by_tr_type(transactions):
	transactions = transactions.apply(pd.to_numeric)
	return  transactions.groupby(level=[0,1,2,3,4], axis=1).sum()

def insider_transactions_scores(insider_transactions,  prices):
	insider_transactions_scores = []
	max_loss_pct = 0.3

	for transaction_date in list(insider_transactions.index.values):
		stop_loss = prices['Open'][transaction_date] - prices['Open'][transaction_date]*0.3
		stop_loss_hit = False
		for price in prices['Open'][transaction_date:]:
			if price <= stop_loss:
				final_price = price
				stop_loss_hit = True
				break
			elif price - price*max_loss_pct > stop_loss:
				stop_loss = price - price*max_loss_pct
		if stop_loss_hit == False:
			final_price = prices['Close'][-1]
		print(final_price, prices['Open'][transaction_date])
		transaction_score = (final_price-prices['Open'][transaction_date])/prices['Open'][transaction_date]
		insider_transactions_scores.append(transaction_score)
	return insider_transactions_scores

def cik_insiders_scores(insiders_transactions, prices, total_shares):
	insiders_scores = {}
	for insider in insiders_transactions:
		try:
			insider_transactions = pd.DataFrame(insiders_transactions[insider].loc[insiders_transactions[insider].ne(0)])
			insider_transactions['PURCHASE PRICES'] = [prices['Open'][date] for date in list(insider_transactions.index.values)]
			insider_transactions['COSTS'] = insider_transactions[insider] * insider_transactions['PURCHASE PRICES']
			insider_transactions['COMPANY %'] = insider_transactions[insider] / total_shares * 100
			insider_transactions['POLLA SCORES'] = [min(50, 50*insider_transactions['COMPANY %'][date]) + min(50, insider_transactions['COSTS'][date]/20000) for date in list(insider_transactions.index.values)]
			insider_transactions['TRANSACTIONS SCORES'] = insider_transactions_scores(insider_transactions, prices)
			print(insider_transactions)
			insider_transactions['FINAL SCORES'] = insider_transactions['POLLA SCORES']*insider_transactions['TRANSACTIONS SCORES']
			insiders_scores[insider] = (statistics.mean(insider_transactions['FINAL SCORES'].tolist()),len(list(insider_transactions.index.values)))
		except:
			pass
	return insiders_scores

def track_scores():
	insiders_scores = {}
	for cik in set(transactions.columns.get_level_values(0)):
		ticker = complements[cik]['ticker']
		stock = yf.Ticker(ticker)
		prices = stock.history(period='max')
		if prices['Open']['2010-01-01':].any() == False or 'P' not in transactions[cik]['nonDerivative']['A'] or 'marketCap' not in stock.info:
			continue
		try:
			total_shares = int(stock.info['marketCap']/prices['Close'][-1])
		except:
			continue
		insiders_scores[cik] = cik_insiders_scores(transactions[cik]['nonDerivative']['A']['P'], prices, total_shares)
	print(insiders_scores)
	return insiders_scores

def plot_all_graphs():
	for cik in set(transactions.columns.get_level_values(0)):
		ticker = complements[cik]['ticker']
		stock = yf.Ticker(ticker)
		prices = stock.history(period='max')
		if prices['Open']['2010-01-01':].any() == False:
			continue
		if 'nonDerivative' in transactions[cik] and 'P' not in transactions[cik]['nonDerivative']['A']:
			if 'derivative' in transactions[cik] and 'P' not in transactions[cik]['derivative']['A']:
				continue
		
		fig, ax_left = plt.subplots()
		ax_right = ax_left.twinx()
		for table in ['nonDerivative','derivative']:
			try:
				ax_left.plot(transactions[cik][table]['A']['P'], label = table)
			except:
				pass

		plt.plot(prices['Open']['2010-01-01':], color='darkgreen')
		ax_right.plot(prices['Open']['2010-01-01':], color='darkgreen')
		ax_left.set_yscale('log')
		ax_right.set_yscale('log')
		ax_left.legend()
		plt.title(ticker + ' ' + cik)
		plt.show()
	return 1

def analyse_form_4_main(textBox1, textBox2, textBox3, textBox4):
	global complements, transactions
	if (inputs := inputs_management.retrieve_analysis_inputs(textBox1, textBox2, textBox3, textBox4, run = True))['keep_downloading'] == False:
		transactions = group_by_tr_type(json_to_df(solapas.merge_solapas_in_df(inputs)))
		complements = open_json('.gitignore/data/complements.json')
		print(transactions)
		print(track_scores())
		#plot_all_graphs()
	return 1

#de momento lo unico bueno:
#gold: RGLD