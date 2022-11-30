ticker = complements[cik]['ticker']
		stock = yf.Ticker(ticker)
		prices = stock.history(period='max')
		if prices['Open']['2010-01-01':].any() == False or 'P' not in transactions[cik]['nonDerivative']['A']:
			continue
		#p se refiere obviamente a purchase
		cik_ins_p = transactions[cik]['nonDerivative']['A']['P']
		cik_ins_p = pd.DataFrame(cik_ins_p.loc[cik_ins_p.ne(0)])
		cik_ins_p.rename(columns={'P': complements[cik]['ticker']}, inplace=True)
		print()
		print(type(cik_ins_p.index.values.tolist()[0]))
		p_prices = [prices[date] for date in cik_ins_p.index.values.tolist()]
		df.loc[:, [complements[cik]['ticker']]] *= np.array(p_prices)