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
import inputs_management
import solapas
import numpy as np

def open_json(dict_name):
    with open(dict_name, 'r') as fp:
        data = json.load(fp)
    return data

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
	return  transactions.groupby(level=[0,1,2,3], axis=1).sum()

def insider_score():
	for cik in set(transactions.columns.get_level_values(0)):
		ticker = complements[cik]['ticker']
		stock = yf.Ticker(ticker)
		prices = stock.history(period='max')
		if prices['Open']['2010-01-01':].any() == False or 'P' not in transactions[cik]['nonDerivative']['A']:
			continue
		#p se refiere obviamente a purchase
		cik_ins_p = transactions[cik]['nonDerivative']['A']['P']
		cik_ins_p = pd.DataFrame(cik_ins_p.loc[cik_ins_p.ne(0)])
		cik_ins_p.rename(columns={'P': complements[cik]['ticker']}, inplace=True)
		try:
			cik_ins_p['PURCHASE PRICE'] = [prices['Open'][date] for date in list(cik_ins_p.index.values)]
			cik_ins_p['COST'] = cik_ins_p[complements[cik]['ticker']] * cik_ins_p['PURCHASE PRICE']
			print(cik_ins_p)
		except:
			print(cik_ins_p)
			print('CAGO EN LA HOSTIA YA')
			pass
	return 1

def plot_all_graphs():
	for cik in set(transactions.columns.get_level_values(0)):
		ticker = complements[cik]['ticker']
		stock = yf.Ticker(ticker)
		prices = stock.history(period='max')
		if prices['Open']['2010-01-01':].any() == False:
			continue
		if 'P' in transactions[cik]['nonDerivative']['A']:
			fig, ax_left = plt.subplots()
			ax_right = ax_left.twinx()
			ax_left.plot(transactions[cik]['nonDerivative']['A']['P'], label = 'buy')
		else:
			continue
		plt.plot(prices['Open']['2010-01-01':], color='darkgreen')
		ax_right.plot(prices['Open']['2010-01-01':], color='darkgreen')
		ax_left.set_yscale('log')
		ax_right.set_yscale('log')
		ax_left.legend()
		plt.title(ticker + ' ' + cik)
		plt.show()

def analyse_form_4_main(textBox1, textBox2, textBox3, textBox4):
	global complements, transactions
	if (inputs := inputs_management.retrieve_analysis_inputs(textBox1, textBox2, textBox3, textBox4, run = True))['keep_downloading'] == False:
		transactions = group_by_tr_type(json_to_df(solapas.merge_solapas_in_df(inputs)))
		complements = open_json('.gitignore/data/complements.json')
		insider_score()
		#plot_all_graphs()
	return 1