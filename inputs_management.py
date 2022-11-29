from tkinter import messagebox
from datetime import datetime, timedelta

import solapas

def popup(message,title='Error'):
    messagebox.showinfo(title, message)

def select_companies(inputs):
    l = []
    f = open('pres/cik-lookup-data.txt', 'r')
    f = f.readlines()
    for i in f:
        if inputs['input_search_key'] in i:
            l.append(i[-12:-2])
    return l

def gestion_cik_range(inputs):
    if inputs['cik_ini'] >= inputs['cik_fin'] + 1:
        popup('El cik inicial tiene que ser inferior o igual a {}'.format(str(inputs['cik_fin'])))
        return False
    if inputs['cik_ini'] <= 0:
        popup('El cik inicial tiene que ser superior o igual a 1')
        return False
    if inputs['cik_fin'] >= len(inputs['cik_nums']) + 1: 
        popup('El cik final tiene que ser inferior o igual a {}'.format(str(len(inputs['cik_nums']))))
        return False
    return inputs['keep_downloading']

def gestion_date_range(inputs):
    if inputs['ini_date'] >= datetime.today():
        popup('pon una fecha inicial inferior a hoy (descagamos dias enteros, por eso no se puede coger hoy)')
        return False
    elif inputs['ini_date'] < inputs['fin_date']:
        popup('pon un rango de fechas decente gilipollas')
        return False
    else:
        return True

def verify_inputs_syntaxis(textBox1, textBox2, textBox3, textBox4, run = False):
    inputs = {}
    inputs['keep_downloading'] = True
    inputs['input_search_key'] = textBox1.get("1.0","end-1c").upper()
    inputs['cik_nums'] = select_companies(inputs)
    if len(inputs['cik_nums']) == 0:
        popup('No hay empresas con {} en el nombre'.format(inputs['input_search_key']))
        inputs['keep_downloading'] = False
        return inputs
    try:
        inputValue2=textBox2.get("1.0","end-1c").split('-')
        if inputValue2[1] == '':
            inputs['cik_ini'], inputs['cik_fin'] = int(inputValue2[0]), int(len(inputs['cik_nums']))
        else:
            inputs['cik_ini'], inputs['cik_fin'] = int(inputValue2[0]), int(inputValue2[1])
        inputs['keep_downloading'] = gestion_cik_range(inputs)
    except:
        popup('Escribe Bien la sintaxis del cik range')
        inputs['keep_downloading'] = False
        return inputs
    
    try:
        inputs['ini_date'] = datetime.strptime(textBox3.get("1.0","end-1c"), '%Y-%m-%d')
    except:
        popup('Escribe bien la primera fecha')
        inputs['keep_downloading'] = False
        return inputs
    try:
        inputs['fin_date'] = datetime.strptime(textBox4.get("1.0","end-1c"), '%Y-%m-%d')
    except:
        popup('Escribe bien la segunda fecha')
        inputs['keep_downloading'] = False
        return inputs
    #aqui te tienes que salir de esta funcion para separar entre retrieve y analisis
    #de hecho si solapas.mod_paramenters==False quiere decir que esta listo para el analisis
    if inputs['keep_downloading'] == True:
        inputs['keep_downloading'] = gestion_date_range(inputs)
    return inputs

def retrieve_download_inputs(textBox1, textBox2, textBox3, textBox4, run = False):
    if (inputs := verify_inputs_syntaxis(textBox1, textBox2, textBox3, textBox4, run))['keep_downloading'] == True:
        inputs['cik_ini'], inputs['cik_fin'], inputs['ini_date'], inputs['fin_date'], inputs['keep_downloading'] = solapas.mod_parameters(inputs)
        print('No hay errores: vas a coger de la empresa {} a la empresa {} de {} que incluyen {}, de {} a {}'.format(str(inputs['cik_ini']) , str(inputs['cik_fin']), str(len(inputs['cik_nums'])), inputs['input_search_key'], str(inputs['ini_date']+timedelta(days=1)-timedelta(seconds=1)), str(inputs['fin_date'])))
        #esto va diferente si pones fechas a hechas o no
        if inputs['keep_downloading'] == False:
            if run == True:
                popup('Hecho!', title='Status')
    return inputs

def retrieve_analysis_inputs(textBox1, textBox2, textBox3, textBox4, run = False):
    if (inputs := verify_inputs_syntaxis(textBox1, textBox2, textBox3, textBox4, run))['keep_downloading'] == True:
        #esto en esta funcion en vd solo sirve para saber si faltan datos o no, lo otro suda
        inputs['cik_ini'], inputs['cik_fin'], inputs['ini_date'], inputs['fin_date'], inputs['keep_downloading'] = solapas.mod_parameters(inputs)
        if inputs['keep_downloading'] == False:
            if run == False:
                print('listo para analizar')
        else:
            popup('Faltan datos para analizar este red cik-date')
    return inputs