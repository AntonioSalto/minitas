import requests
import xmltodict
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time
from tkinter import messagebox
from tkinter import * #creo que no lo uso
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import patches

import solapas
import inputs_management

def ndd():
    return defaultdict(ndd)

def popup(message,title='Error'):
    messagebox.showinfo(title, message)
    return 1

def save_json(dict, dict_name):
    with open('{}.json'.format(dict_name), 'w') as fp: 
        json.dump(dict, fp)
    return 1

def save_txt(txt, txt_name):
    with open("{}.txt".format(txt_name), "w") as output:  
        output.write(str(txt))
    return 1
    
def open_json(dict_name):
    with open(dict_name, 'r') as fp:
        data = json.load(fp)
    return data

def open_txt(txt_name):
    f = open(txt_name, "r")
    return f.read()

def add_pb_file(cik_num, filing_number, pb):
    if cik_num not in problematic_files:
        problematic_files[cik_num] = {}
    if filing_number not in problematic_files[cik_num]:
        problematic_files[cik_num][filing_number] = []
    problematic_files[cik_num][filing_number].append(pb)
    print(pb)
    return problematic_files

def fill_cik_complements(cik_num, data): 
    company = data['ownershipDocument']['issuer']['issuerName']
    ticker = data['ownershipDocument']['issuer']['issuerTradingSymbol']
    complements[cik_num] = {'company':company, 'ticker':ticker, 'owner':{}}
    return complements

def change_complement(complement, cik_num, filing_number):
    if complement == 'true' or complement == 'True' or complement == 'I' or complement == '1':
        return '1'
    elif complement == 'false' or complement == 'False' or complement == '0':
        return '0'
    else:
        problematic_files = add_pb_file(cik_num, filing_number, complement)
        return complement

def fill_owner_complements(cik_num, owner_cik, data, filing_number):
    if type(data['ownershipDocument']['reportingOwner']) == list:
        name = data['ownershipDocument']['reportingOwner'][0]['reportingOwnerId']['rptOwnerName']
        relationship = data['ownershipDocument']['reportingOwner'][0]['reportingOwnerRelationship']
    else:
        name = data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerName']
        relationship = data['ownershipDocument']['reportingOwner']['reportingOwnerRelationship']
    #A VECES EN EL XML SOLO HAY ALGUNO DE LOS 3, NISIQUIERA PONEN EL <></>
    if 'isDirector' in relationship:
        is_director = change_complement(relationship['isDirector'],cik_num, filing_number)
    else:
        is_director = '0'
    if 'isOfficer' in relationship:
        is_officer = change_complement(relationship['isOfficer'],cik_num, filing_number)
    else:
        is_officer = '0'
    if 'isTenPercentOwner' in relationship:
        is_ten_pct = change_complement(relationship['isTenPercentOwner'],cik_num, filing_number)
    else:
        is_ten_pct = '0'
    #aqui deberia poner lo de other text que pone si es ceo pero ya luego
    complements[cik_num]['owner'][owner_cik] = {'name':name, 'director':is_director, 'officer':is_officer, 'ten_pct':is_ten_pct}
    return complements

def control_requests_rate(request_count):
    if request_count % 10 == 0:
        time.sleep(1)
    return request_count + 1

def save_files(inputs):
    file_cik_ini, file_cik_fin = str(inputs['cik_ini']), str(inputs['cik_fin'])
    file_ini_date, file_fin_date = str(inputs['ini_date'])[:10], str(inputs['fin_date'])[:10]
    full_full_name = '{}_{}_{}_{}_{}'.format(inputs['input_search_key'], file_cik_ini, file_cik_fin, file_ini_date, file_fin_date)
    isExist = os.path.exists('.gitignore/data/transactions/{}'.format(inputs['input_search_key']))
    if not isExist:
        os.makedirs('.gitignore/data/transactions/{}'.format(inputs['input_search_key']))
        os.makedirs('.gitignore/data/transactions/{}/problematic_files'.format(inputs['input_search_key']))
    save_json(transactions, '.gitignore/data/transactions/{}/{}'.format(inputs['input_search_key'], full_full_name))
    #SI NO HA HABIDO NINGUN PB EN LA RED CIKDATE NO QUIERO TENER EL PB FILES MOLESTANDO
    if len(problematic_files) != 0:
        save_json(problematic_files, '.gitignore/data/transactions/{}/problematic_files/{}'.format(inputs['input_search_key'], full_full_name))
    save_json(complements, '.gitignore/data/complements')
    save_json(parentings, '.gitignore/data/parentings')
    print('Files saved: {} de {} a {} de {} a {}'.format(inputs['input_search_key'], str(inputs['cik_ini']), str(inputs['cik_fin']), str(inputs['ini_date']), str(inputs['fin_date'])))
    
def find_quarters_init(inputs):
    ini_months_and_days = ['03-31', '06-30', '09-30', '12-31']
    fin_months_and_days = ['10-01', '07-01', '04-01', '01-01']
    for i in range(4):
        #puedeque en elcodigo de vdnecesite %h%m%s
        found_ini_quarter, found_fin_quarter = False, False
        if inputs['ini_date'] <= datetime.strptime('{}-{} 23:59:59'.format(str(inputs['ini_date'])[:4], ini_months_and_days[i]), '%Y-%m-%d %H:%M:%S') and found_ini_quarter == False:
            ini_quarter = 'QTR{}'.format(i+1)
            found_ini_quarter = True
        if inputs['fin_date'] >= datetime.strptime('{}-{} 00:00:00'.format(str(inputs['fin_date'])[:4], fin_months_and_days[i]), '%Y-%m-%d %H:%M:%S') and found_fin_quarter == False:
            fin_quarter = 'QTR{}'.format(4-i)
            found_fin_quarter = True
    return ini_quarter, fin_quarter

def find_next_quarter(quarter, year):
    quarter_list = ['QTR4','QTR3','QTR2','QTR1']
    idx = quarter_list.index(quarter)
    thiselem = quarter_list[idx]
    idx = (idx + 1) % len(quarter_list)
    quarter = quarter_list[idx]
    if quarter == 'QTR4':
        year = str(int(year)-1)
    return quarter, year

def fill_transactions(data, filing_number, publi_date, cik_num): 
    global complements
    #CHECAMOS SI NOS RENTA EL FORM QUE HEMOS ABIERTO
    print(f'{cik_num}/{filing_number}', publi_date)
    #CHECKAMOS QUE TIENE LA INPUT KEY A QUIEN SE COMPRA NO QUIEN COMPRA (evita meter a goldman cuando compra paquito mineria y duplicar goldman y goldmining pq entraria dos veces sino)
    if data['ownershipDocument']['issuer']['issuerCik'] != cik_num:
        print('caso goldman sachs')
        return transactions, complements
    #AHORA PARENTINGS SOLO ES PARA SABER QUE CIERTAS EMPRESAS SON PARTES DE OTRAS O ALGO
    if type(data['ownershipDocument']['reportingOwner']) == list:
        owner_cik = data['ownershipDocument']['reportingOwner'][0]['reportingOwnerId']['rptOwnerCik']
        if owner_cik not in parentings:
            parentings[owner_cik] = []
        for child_company in data['ownershipDocument']['reportingOwner'][1:]:
            parentings[owner_cik].append(child_company['reportingOwnerId']['rptOwnerCik'])
    else:
        owner_cik = data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerCik']
    
    tables = {'nonDerivative':False,'derivative':False}
    for table in tables:
        if f'{table}Table' in data['ownershipDocument'] and data['ownershipDocument'][f'{table}Table'] != None:
            #SOLO TRABAJO CON LAS TRANSACTIONS; NO CON HOLDINGS
            if f'{table}Transaction' in data['ownershipDocument'][f'{table}Table']:
                #CHECAMOS SI NO HAY VARIAS TRANSACCIONES EN LA TABLA
                if type(data['ownershipDocument'][f'{table}Table'][f'{table}Transaction']) != list:
                    data['ownershipDocument'][f'{table}Table'][f'{table}Transaction'] = [data['ownershipDocument'][f'{table}Table'][f'{table}Transaction']]
                for fila in data['ownershipDocument'][f'{table}Table'][f'{table}Transaction']:
                    try:
                        tr_a_or_d = fila['transactionAmounts']['transactionAcquiredDisposedCode']['value']
                        tr_value = fila['transactionAmounts']['transactionShares']['value']
                        tr_code = fila['transactionCoding']['transactionCode']
                        if publi_date in transactions[cik_num][table][tr_a_or_d][tr_code][owner_cik]:
                            transactions[cik_num][table][tr_a_or_d][tr_code][owner_cik][publi_date] = str(int(transactions[cik_num][table][tr_a_or_d][tr_code][owner_cik][publi_date]) + int(float(tr_value)))
                            #solo sumas todos los elementos de la tabla que son de caracterisiticas iguales no tienes en cuenta nada mas
                        else:
                            transactions[cik_num][table][tr_a_or_d][tr_code][owner_cik][publi_date] = tr_value
                        tables[table] = True
                    except:
                        problematic_files = add_pb_file(cik_num, filing_number, f'HA PETAO UNA FILA {table}T')
                if tables[table]:
                    print(f'{table}T *succes*')
        #para la dt NO TENGO EL CUENTA EL TIPO DE SECURITY QUE ES, igual renta para saber si vende porque le expiran opciones o que
        #ademas lo meto todo junto sin distinguir derivative y no derivative de momento,cuando meta mas features ya si eso pero de momento inutil

    if tables['nonDerivative'] == True or tables['derivative'] == True:
        #CHECAMOS QUE TENEMOS LOS DATOS COMPLEMENTARIOS DE EMPRESA Y OWNER
        if cik_num not in complements:
            complements = fill_cik_complements(cik_num, data)     
        if owner_cik not in complements[cik_num]['owner']: 
            complements = fill_owner_complements(cik_num, owner_cik, data, filing_number)
    else:
        problematic_files = add_pb_file(cik_num, filing_number, 'FORM 4 VACIO?, huele a caca')
    return transactions, complements

def download_form_4_main(textBox1, textBox2, textBox3, textBox4):
    global transactions, complements, parentings, problematic_files
    while (inputs := inputs_management.retrieve_download_inputs(textBox1, textBox2, textBox3, textBox4, run = True))['keep_downloading'] == True:
        inputs['ini_date'] = inputs['ini_date'] + timedelta(days=1) - timedelta(seconds=1)
        transactions, problematic_files = ndd(), {}
        #ESTO ES PORSI TE HA DADO POR BORRARLO TODO PARA HACER PRUEBAS O LO QUE SEA
        
        isExist2 = os.path.exists('.gitignore/data/transactions')
        if isExist2:
            complements = open_json('.gitignore/data/complements.json')
            parentings = open_json('.gitignore/data/parentings.json')
        else:
            os.makedirs('.gitignore/data/transactions')
            complements, parentings = {}, {}
        
        request_count = 0
        ini_quarter, fin_quarter = find_quarters_init(inputs)
        quarter, year = ini_quarter, str(inputs['ini_date'])[:4]
        out_of_date = False
        next_is_ood = False
        while out_of_date == False:
            request_count = control_requests_rate(request_count)
            quarter_all_forms_pre = requests.get('https://www.sec.gov/Archives/edgar/full-index/{}/{}/master.idx'.format(year, quarter), headers = {'User-agent': 'Mozilla/5.0'}).content
            quarter_all_forms_pre = quarter_all_forms_pre.decode('latin-1').split('\n')
            quarter_all_forms, seen_ciks = set(), set()
            for filing_info in quarter_all_forms_pre:
                if inputs['input_search_key'] in filing_info.upper():
                    quarter_all_forms.add(filing_info)
            cik_count = inputs['cik_ini'] - 1
            #iria mas rapido si vas cogiendo todo del txt directo en vez del xml pero pereza cambiar tanto
            for cik_num in inputs['cik_nums'][inputs['cik_ini']-1:inputs['cik_fin']]:
                cik_count += 1
                print('------------------------------- {} {} ({}) {} {} -------------------------------'.format(inputs['input_search_key'], cik_count, cik_num, quarter,year))   
                if cik_num in seen_ciks:
                    print('cik repetido')
                    continue
                else:
                    seen_ciks.add(cik_num)
                for filing in quarter_all_forms:
                    filing = filing.split('|')
                    if cik_num == "0000000000{}".format(filing[0])[-10:] and (filing[2] == '4' or filing[2] == '4/A'):
                        publi_date = filing[3]
                        publi_date = datetime.strptime(publi_date, '%Y-%m-%d')
                        if publi_date >= inputs['fin_date'] and publi_date <= inputs['ini_date']:
                    
                            filing_number = filing[4].split('/')[-1][:-4].replace('-', '')
                            request_count = control_requests_rate(request_count)
                            document_content = requests.get(f'https://www.sec.gov/Archives/edgar/data/{cik_num}/{filing_number}/index.json', headers={"User-Agent": "Mozilla/5.0"}).json()
                            for document in document_content['directory']['item']:
                                document_name = document['name']
                                if '.xml' in document_name:

                                    request_count = control_requests_rate(request_count)
                                    try:
                                        data = xmltodict.parse(requests.get(f'https://www.sec.gov/Archives/edgar/data/{cik_num}/{filing_number}/{document_name}', headers={"User-Agent": "Mozilla/5.0"}).content)
                                    except:
                                        problematic_files = add_pb_file(cik_num, filing_number, 'REQUESTS NO HA LEIDO EL CIK')
                                        continue
                                    transactions, complements = fill_transactions(data, filing_number, str(publi_date)[:10], cik_num)
                                       
            #esto para preparar el siguiente quarter
            quarter, year = find_next_quarter(quarter,year)
            if next_is_ood == True:
                out_of_date = True
            elif year == str(inputs['fin_date'])[:4] and quarter == fin_quarter:
                next_is_ood = True

        save_files(inputs)
    return 1

def visualise_downloaded_forms_4(textBox1, textBox2, textBox3, textBox4, run = False):
    if (inputs := inputs_management.verify_inputs_syntaxis(textBox1, textBox2, textBox3, textBox4, run))['keep_downloading'] == True:
        input_search_key_carpetas = solapas.retrieve_key_files_name_elements(inputs)
        nodispo_date_intervals = solapas.spot_nodispo_dates(input_search_key_carpetas, inputs)
        for key in nodispo_date_intervals:
          for i in nodispo_date_intervals[key]:
            ax = plt.subplot()
            # Create rectangle x coordinates
            startTime = i[0]
            endTime = i[1]

            # convert to matplotlib date representation
            start = mdates.date2num(startTime)
            end = mdates.date2num(endTime)
            width = end - start

            # Plot rectangle
            rect = patches.Rectangle((start, key), width, 1, color='g')#no se pueden poner bordes pq va cik por cik poniendo fechas
            ax.add_patch(rect) 
            
            # assign date locator / formatter to the x-axis to get proper labels
            locator = mdates.AutoDateLocator(minticks=3)
            formatter = mdates.AutoDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)

            # set the limits
            plt.xlim([inputs['fin_date'], inputs['ini_date']])
            plt.ylim([inputs['cik_ini'], inputs['cik_fin']])
        plt.show()
    return 1