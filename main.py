#~/OneDrive/Documentos/GitHub/minitas
import datetime
from tkinter import *

import downloads
import analysis
import inputs_management

def ask_input(feature, by_defect):
    label = Label(root, text=feature)
    label.pack()
    textBox = Text(root, height=1, width=30)
    textBox.insert(INSERT, by_defect)
    textBox.pack()
    return textBox

def gui():
    global root
    root=Tk()

    textBox1 = ask_input('search key:', 'silica')
    textBox2 = ask_input('cik range (int-{int, ""}):', '1-')
    textBox3 = ask_input('first date (YYYY-MM-DD 00:00:00):', str(datetime.datetime.today()-datetime.timedelta(days=1))[:10])
    textBox4 = ask_input('last date (YYYY-MM-DD 23:59:59):', '2010-01-01')

    label1 = Label(root, text="Retrieve insider transactions")
    label1.pack()
    button1 = Button(root, text='submit', width = 12, command=lambda: inputs_management.retrieve_download_inputs(textBox1, textBox2, textBox3, textBox4))
    button1.pack()
    button2 = Button(root, text='submit + run', width = 12, command=lambda: downloads.download_form_4_main(textBox1, textBox2, textBox3, textBox4))
    button2.pack()

    label3 = Label(root, text="Analyse insider transactions")
    label3.pack()
    button3 = Button(root, text='submit', width = 12, command=lambda: inputs_management.retrieve_analysis_inputs(textBox1, textBox2, textBox3, textBox4))
    button3.pack()
    button4 = Button(root, text='submit + run', width = 12, command=lambda: analysis.analyse_form_4_main(textBox1, textBox2, textBox3, textBox4))
    button4.pack()

    label4 = Label(root, text="Visualise red cik-date")
    label4.pack()
    button5 = Button(root, text='visualise', width = 12, command=lambda: downloads.visualise_downloaded_forms_4(textBox1, textBox2, textBox3, textBox4))
    button5.pack()

    mainloop()
    return 1
gui()
#------------------------------------------------------------------------------
#voy a venir necesitando las shares totales que tiene cada persona para el insider score, y el puesto de la persona

#esta roto solapas o algo porque cojas la red que cojas te salen los mismo graficos

#no se porque cada vez que descargo un dia me mira todo el año (todos los quarter all forms filings)

#claramente en este sector tienes que tener en cuenta la volatilidad hstorica de la accion para saber en que %loss poner el stoploss

#igual tendrias que cik_nums convertirla a diccionario

#printea una cosa cuando le doy a analisis
#------------------------------------------------------------------------------
#hay veces que en derivative ponen dinero en vez de shares osea el value en vez de las shares, no se de que depende

#tienes que arreglar la barra de progreso y que cuando ua acabe un programa no escriba nada en pantalla antes del hecho
#   como hacerlo (dia muerto):
#       calculas todos los puntos de la red total con los textbox
#       le restas todos las partes de cuadrados que ya estan y caigan dentro de la red total (el % no empieza en 0)
#       cada vez que pases de cik dentro del QRT sumas porcentage correspondiente a todos los puntos (fechas) que han pasado

#parece que cuando apuestan mas fuerte les da mas igual que caiga la accion porque miran muy a largo plazo con *10
#cuando apuestan mas flojo son mas minitendencias