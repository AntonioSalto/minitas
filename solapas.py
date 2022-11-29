import os
from datetime import datetime, timedelta
import json
import pandas as pd
from collections import defaultdict

def ndd():
    return defaultdict(ndd)

def open_json(dict_name):
    with open(dict_name, 'r') as fp:
        data = json.load(fp)
    return data

def spot_nodispo_dates(input_search_key_transaction_files_elements, inputs):
    nodispo_cik_dates = {}
    nodispo_date_intervals = {}
    for cik in range(inputs['cik_ini'],inputs['cik_fin'] + 1):
        nodispo_cik_dates[cik] = {'recent':[], 'past':[]}
        nodispo_date_intervals[cik] = []
        for carpeta in input_search_key_transaction_files_elements:
            if cik >= carpeta[1] and cik <= carpeta[2]:
                nodispo_cik_dates[cik]['recent'].append(carpeta[3])
                nodispo_cik_dates[cik]['past'].append(carpeta[4])
        recent_dates_copy = nodispo_cik_dates[cik]['recent'].copy()
        for recent_date in recent_dates_copy:
            if recent_date + timedelta(days=1) in nodispo_cik_dates[cik]['past']:
                nodispo_cik_dates[cik]['recent'].remove(recent_date)
                nodispo_cik_dates[cik]['past'].remove(recent_date + timedelta(days=1))
        nodispo_cik_dates[cik]['past'].sort()
        nodispo_cik_dates[cik]['recent'].sort()
        nodispo_cik_dates[cik]['past'].reverse()
        nodispo_cik_dates[cik]['recent'].reverse()
        for i in range(len(nodispo_cik_dates[cik]['recent'])):
            nodispo_date_intervals[cik].append((nodispo_cik_dates[cik]['recent'][i],nodispo_cik_dates[cik]['past'][i]))
    return nodispo_date_intervals

def spot_work_dates(nodispo_date_intervals, inputs):
    for cik in range(inputs['cik_ini'],inputs['cik_fin'] + 1):
        day_count = (inputs['ini_date'] - inputs['fin_date']).days + 1
        for date in (inputs['ini_date'] - timedelta(n) for n in range(day_count)):
            keep_downloading = True
            for nodispo_date_interval in nodispo_date_intervals[cik]:
                if date <= nodispo_date_interval[0] and date >= nodispo_date_interval[1]:
                    keep_downloading = False
                    break
            if keep_downloading == True:
                bloque_ini_date = date
                break

        if keep_downloading == True:
            day_count2 = (bloque_ini_date - inputs['fin_date']).days + 1
            for date in (bloque_ini_date - timedelta(n) for n in range(day_count2)):
                nodispo_date = False
                for nodispo_date_interval in nodispo_date_intervals[cik]:
                    if date <= nodispo_date_interval[0] and date >= nodispo_date_interval[1]:
                        nodispo_date = True
                        break
                if nodispo_date == True:
                    bloque_fin_date = date + timedelta(days=1)
                    break

            if nodispo_date == True:
                day_count3 = (bloque_ini_date - bloque_fin_date).days + 1
                for cik_spot_fin in range(cik + 1, inputs['cik_fin'] + 1):
                    for date in (bloque_ini_date - timedelta(n) for n in range(day_count3)):
                        for nodispo_date_interval in nodispo_date_intervals[cik_spot_fin]:
                            if date <= nodispo_date_interval[0] and date >= nodispo_date_interval[1]: 
                                bloque_cik_fin = cik_spot_fin - 1
                                #caso normal, un cuadrado delimitado
                                return cik, bloque_cik_fin, bloque_ini_date, bloque_fin_date, keep_downloading
                #limitan las fechas pero se hacen todos los ciks
                return cik, inputs['cik_fin'], bloque_ini_date, bloque_fin_date, keep_downloading
            else:
                day_count3 = (bloque_ini_date - inputs['fin_date']).days + 1
                for cik_spot_fin in range(cik + 1, inputs['cik_fin'] + 1):
                    for date in (bloque_ini_date - timedelta(n) for n in range(day_count3)):
                        for nodispo_date_interval in nodispo_date_intervals[cik_spot_fin]:
                            if date <= nodispo_date_interval[0] and date >= nodispo_date_interval[1]: 
                                bloque_cik_fin = cik_spot_fin - 1
                                #las fechas no estan limitadas pero los ciks si
                                return cik, bloque_cik_fin, bloque_ini_date, inputs['fin_date'], keep_downloading
                #casos no estaba nada incluido o a partir de un cierto punto todo dispo hasta el final
                return cik, inputs['cik_fin'], bloque_ini_date, inputs['fin_date'], keep_downloading
    #caso estaba incluido entero ya
    return inputs['cik_ini'], inputs['cik_fin'], inputs['ini_date'], inputs['fin_date'], keep_downloading

def retrieve_key_files_name_elements(inputs):
    input_search_key_transaction_files = [name for name in os.listdir("C:/Users/Usuario/OneDrive/Documentos/proyectos/minas/EDGAR_SEC/data/transactions/{}".format(inputs['input_search_key']))]
    input_search_key_transaction_files_elements = []
    for i in range(len(input_search_key_transaction_files)):
        if input_search_key_transaction_files[i] != 'problematic_files':
            input_search_key_transaction_files[i] = input_search_key_transaction_files[i].replace(".json", '')
            input_search_key_transaction_files_elements.append(input_search_key_transaction_files[i].split('_'))
            input_search_key_transaction_files_elements[-1][1], input_search_key_transaction_files_elements[-1][2] = int(input_search_key_transaction_files_elements[-1][1]), int(input_search_key_transaction_files_elements[-1][2])
            input_search_key_transaction_files_elements[-1][3], input_search_key_transaction_files_elements[-1][4] = datetime.strptime(input_search_key_transaction_files_elements[-1][3], '%Y-%m-%d'), datetime.strptime(input_search_key_transaction_files_elements[-1][4], '%Y-%m-%d')
    return input_search_key_transaction_files_elements

def mod_parameters(inputs):
    isExist = os.path.exists('data/transactions/{}'.format(inputs['input_search_key']))
    if not isExist:
        keep_downloading = True
        return inputs['cik_ini'], inputs['cik_fin'], inputs['ini_date'], inputs['fin_date'], keep_downloading
    else:
        input_search_key_transaction_files_elements = retrieve_key_files_name_elements(inputs)
        nodispo_date_intervals = spot_nodispo_dates(input_search_key_transaction_files_elements, inputs) 
        bloque_cik_ini, bloque_cik_fin, bloque_ini_date, bloque_fin_date, keep_downloading = spot_work_dates(nodispo_date_intervals, inputs)
        return bloque_cik_ini, bloque_cik_fin, bloque_ini_date, bloque_fin_date, keep_downloading
        
def merge_solapas_in_df(inputs):
    #LOADEO TODAS LAS TRANSACCIONES QUE TENGO DE LA INPUT SEARCH KEY Y MERGE DE TODO NO SOLO DE LO ESTRICTAMENTE NECESARIO
    transactions = ndd()
    carpetas = [name for name in os.listdir("C:/Users/Usuario/OneDrive/Documentos/proyectos/minas/EDGAR_SEC/data/transactions/{}".format(inputs['input_search_key']))]
    for carpeta in carpetas:
        print(carpeta)
        transactions_file = 'data/transactions/{}/'.format(inputs['input_search_key']) + carpeta
        print(transactions_file)
        if inputs['input_search_key']+'/'+inputs['input_search_key'] in transactions_file:
            transactions_file_content = open_json(transactions_file)
            for cik_num in transactions_file_content:
                for a_or_d in transactions_file_content[cik_num]:
                    for tr_code in transactions_file_content[cik_num][a_or_d]:
                        for owner_cik in transactions_file_content[cik_num][a_or_d][tr_code]:
                            for publi_date in transactions_file_content[cik_num][a_or_d][tr_code][owner_cik]:
                                transactions[cik_num][a_or_d][tr_code][owner_cik][publi_date] = transactions_file_content[cik_num][a_or_d][tr_code][owner_cik][publi_date]
    return transactions