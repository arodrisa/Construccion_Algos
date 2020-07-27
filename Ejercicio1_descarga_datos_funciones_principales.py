# %%
# Libraries
from urllib.request import Request, urlopen
import urllib
from bs4 import BeautifulSoup as bs
from pandas.tseries.offsets import BDay
from functools import partial
import itertools
import multiprocessing as mp
import requests
import datetime
import os
import investpy
import re
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from random import sample
from tqdm import tqdm, tqdm_notebook
import random


# import sys
# import seaborn as sns

# %%
# Variables
nombres_indices = ["Euro Stoxx 50", "IBEX 35", "S&P 500", "DAX", "Bovespa", "Nikkei 225", "Reino Unido 100",
                   "Dow Jones Industrial Average", "IBEX Medium Cap", "IBEX Small Cap", "Hang Seng"]
tickers_indices = ["STOXX50E", "IBEX", "SPX", "GDAXI",
                   "BVSP", "N225", "invuk100", "DJI", "IBEXC", "IBEXS", "HSI"]
urls_indices = ["https://es.investing.com/indices/eu-stoxx50-components", "https://es.investing.com/indices/spain-35-components",
                "https://es.investing.com/indices/us-spx-500-components", "https://es.investing.com/indices/germany-30-components",
                "https://es.investing.com/indices/bovespa-components", "https://es.investing.com/indices/japan-ni225-components",
                "https://es.investing.com/indices/investing.com-uk-100-components", "https://es.investing.com/indices/us-30-components",
                "https://es.investing.com/indices/ibex-medium-cap-components", "https://es.investing.com/indices/ibex-small-cap-components",
                "https://es.investing.com/indices/hang-sen-40-components"]

tabla_indices = pd.DataFrame(
    list(zip(nombres_indices, tickers_indices, urls_indices)), columns=['nombres_indices', 'tickers_indices', 'urls_indices'])
tabla_indices
ventana = 30
# date_time_str = "01/01/2018"
fecha_inicio = "01/01/2018"
fecha_fin = "31/12/2018"
ventana = 30
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%d/%m/%Y')
fecha_fin = datetime.datetime.strptime(fecha_fin, '%d/%m/%Y')

indice = tabla_indices.loc[1, 'urls_indices']
url = indice


def encontrar_fecha_anterior_inicio(fecha_inicio, ventana):
    fecha_anterior_inicio = fecha_inicio - BDay(ventana*2)
    return fecha_anterior_inicio


def composicion_indice(url):

    html_requested_data = requests.get(
        url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = bs(html_requested_data.content, 'html.parser')
# Write html to csv
# html = webpage.prettify("utf-8")
# with open("output1.html", "wb") as file:
#     file.write(html)

    data = []

    table = webpage.find("table", {'id': 'cr1'})
    rows = table.find_all('tr')
    for row in rows[1:len(rows)]:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        temp_data = [ele for ele in cols if ele]
        temp_data.append('https://es.investing.com' +
                         row.find('a')['href']+'-historical-data')

        data.append(temp_data)
        # data.append([ele for ele in cols if ele],cols.find('a')['href'])

    temp = rows[0].find_all('th')
    temp = [ele.text.strip() for ele in temp]
    temp = temp[1:(len(temp)-1)]
    temp.append('link')

    index_components = pd.DataFrame(data, columns=temp)

    return index_components.loc[:, ['Nombre', 'link']]


def construimos_tabla_activos(item_link):
    time.sleep(random.randint(1, 2))
    html_requested_data = requests.get(
        item_link, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = bs(html_requested_data.content, 'html.parser')

    temp_ticker = str(webpage.find_all(
        'h1', {'class': 'float_lang_base_1 relativeAttr'}))
    ticker = temp_ticker[temp_ticker.find("(")+1:temp_ticker.find(")")]
    stock_data = webpage.find('div', {'class': 'instrumentDataFlex'})
    currency = stock_data.find_all('span', {'class': 'bold'})[-1].text

    ISIN = stock_data.find_all(
        'span', {'class': 'elp'}, text=True)[2].text.replace(u'\xa0', u'')
    temp_market = stock_data.find_all('span', {'class': 'elp'})[1]
    temp_market = temp_market.find('a')['href']

    market = temp_market.replace('/markets/', '').replace(u'-', u' ')

    return([ticker, currency, ISIN, market])


def obtener_info_activos(indice):
    # Obtenemos los activos que componen cada índice.
    info_activos = composicion_indice(indice)
    info_activos["ticker"] = ""
    info_activos["currency"] = ""
    info_activos["ISIN"] = ""
    info_activos["market"] = ""
    # item_link = nombre_activos.iloc[1,1]
    # item = construimos_tabla_activos(item_link)

    info_activos[["ticker", "currency", "ISIN", "market"]] = info_activos.apply(
        lambda x: construimos_tabla_activos(x['link']), axis=1, result_type='expand')
    return info_activos


def descargar_cotizaciones_diarias_investing(url_activo, fecha_inicio, fecha_fin):
    # url_activo = url_activo['link']
    # Es el endpoint con la información a la que atacar (PHPSESSID y StickySession)
    uri = "https://es.investing.com/instruments/HistoricalDataAjax"
    data = []
    headers = {
        'Origin': "https://es.investing.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "text/plain, */*;",
        'Referer': url_activo,
        'X-Requested-With': "XMLHttpRequest"
    }
    # Obtenemos las coockies
    try:
        r = requests.get(url_activo, headers={'User-Agent': 'Mozilla/5.0'})
        PHPSESSID = r.cookies.get_dict()['PHPSESSID']
        StickySession = r.cookies.get_dict()['StickySession']

        html_requested_data = requests.get(
            url_activo, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = bs(html_requested_data.content, 'html.parser')

        wepage_str = webpage.prettify()
        posicion = wepage_str.find('smlId')
        smlId = re.findall('[0-9]+', wepage_str[posicion:(posicion+18)])[0]
        pairId = re.findall('[0-9]+', wepage_str[posicion-28:(posicion-1)])[0]

        payload = "curr_id="+pairId+"&smlID="+smlId+"&st_date=" + \
            fecha_inicio.strftime('%d') + '%2F'+fecha_inicio.strftime('%m') + \
            "%2F"+fecha_inicio.strftime('%Y')+"&end_date=" + \
            fecha_fin.strftime('%d')+"%2F"+fecha_fin.strftime('%m')+"%2F" + \
            fecha_fin.strftime('%Y') + \
            "&interval_sec=Daily&action=historical_data"
        response = requests.post(uri, data=payload, headers=headers)

        # SCRAPPING TABLE

        data_requested = bs(response.content, 'html.parser')
        table = data_requested.find("table", {'id': 'curr_table'})
        rows = table.find_all('tr')
        for row in rows[1:len(rows)]:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            temp_data = [ele for ele in cols if ele]

            data.append(temp_data)

            temp = rows[0].find_all('th')
            temp = [ele.text.strip() for ele in temp]
            temp = temp[0:(len(temp))]
            cotizaciones = pd.DataFrame(data, columns=temp)

        cotizaciones = cotizaciones.iloc[:, :-1]

        # ERROR HANDLING
    except Exception:
        print("could not scrap data for url " + url_activo)
        emptylist = []
        cotizaciones = pd.DataFrame(emptylist)
        pass
    return cotizaciones


def get_cookie_value(r):
    return {'B': r.cookies['B']}


def descargar_cotizaciones_diarias_investing_api(info_activos, fecha_inicio, fecha_fin):

    data = investpy.get_stock_historical_data(
        'ACS', 'spain', '01/01/2019', '31/12/2019')

    data = investpy.get_stock_historical_data(
        stock=info_activos['ticker'], country=info_activos['market'], from_date=fecha_inicio.strftime('%d/%m/%Y'), to_date=fecha_fin.strftime('%d/%m/%Y'), order='descending')
    data['Fecha'] = data.index
    cols = ['Fecha', 'Close', 'Open', 'High', 'Low', 'Volume']
    data = data[cols]
    data.reset_index(drop=True, inplace=True)
    data.columns = ['Fecha', 'Último', 'Apertura', 'Máximo', 'Mínimo', 'Vol.']
    return data


def limpiar(cotizaciones):
    cols = cotizaciones.columns[1:]
    cotizaciones[cols] = cotizaciones[cols].astype(str)
    # Localizamos los volúmenes en miles "K"
    indice_miles = [bool(re.search('K', i)) for i in cotizaciones.iloc[:, -1]]
    cotizaciones.iloc[:, -1] = cotizaciones.iloc[:, -1].str.replace('K', '')

    # Localizamos los volúmenes en millones "M"
    indice_millones = [bool(re.search('M', i))
                       for i in cotizaciones.iloc[:, -1]]
    cotizaciones.iloc[:, -1] = cotizaciones.iloc[:, -1].str.replace('M', '')

    # Convert to DateTime
    cotizaciones.iloc[:, 0] = pd.to_datetime(
        cotizaciones.iloc[:, 0], format='%d.%m.%Y')

    # Si el activo cotiza por encima de 1.000, hay que quitar los puntos.
    cotizaciones.iloc[:, 1:] = cotizaciones.iloc[:,
                                                 1:].stack().str.replace('.', '').unstack()
    cotizaciones.iloc[:, 1:] = cotizaciones.iloc[:,
                                                 1:].stack().str.replace(',', '.').unstack()

    cotizaciones[cols] = cotizaciones[cols].apply(
        pd.to_numeric, errors='coerce')
    cotizaciones.iloc[:, -1][indice_miles] *= 1000
    cotizaciones.iloc[:, -1][indice_millones] *= 1000000
    return cotizaciones


def homogeneizar(cotizaciones, fecha_inicio, fecha_fin):
    # Creamos un vector con todas las fechas entre el día inicial y el final entre weekdays
    fechas = pd.bdate_range(start=fecha_inicio, end=fecha_fin).tolist()
    fechas = pd.DataFrame(fechas, columns=['Fecha'])

  # Volcamos los datos en un DF homogeneizado, utilizando la columna de fechas como índice.
    datos_homogeneizados = fechas.merge(
        cotizaciones, 'left', left_on='Fecha', right_on='Fecha', suffixes=(False, False))

  # Ordenamos los datos por fecha (al hacer el merge se ha invertido el orden)
    datos_homogeneizados.sort_values(by='Fecha', ascending=False, inplace=True)
  # Localizamos los datos con NULL y los transformamos a NA
    datos_homogeneizados.fillna(method='ffill', inplace=True)
  # Completamos los datos con NA (días en los que no hay registrada una cotización, pero que otras empresas sí cotizaron)
    datos_homogeneizados.sort_values(by='Fecha', ascending=True, inplace=True)
    datos_homogeneizados.fillna(method='ffill', inplace=True)
    datos_homogeneizados.sort_values(by='Fecha', ascending=False, inplace=True)

    return datos_homogeneizados


def split_contrasplit(cotizaciones):
    cols = cotizaciones.columns[1:]
    cotizaciones[cols] = cotizaciones[cols].apply(
        pd.to_numeric, errors='coerce')
    volumen = (np.log(cotizaciones['Vol.']).diff()).fillna(0)
    rentabilidades = (np.log(cotizaciones['Último']).diff()).fillna(0)

    indice_booleano = (((rentabilidades > 0.615) & (
        volumen < (-0.615))) | ((rentabilidades < (-0.615)) & (volumen > 0.615)))

    rentabilidades_excesivas = rentabilidades[indice_booleano]

    if(rentabilidades_excesivas.size > 0):
        multiplicador = [1]*len(cotizaciones.index)
        for idia in cotizaciones.index[:-1].sort_values():
            # Los split o contra split se hacen por la noche. Para eliminarlos debemos
            # comparar el precio de cierre con el de apertura. Ambos deben coincidir exáctamente.
            if((rentabilidades[idia-1] > 0.615) & (volumen[idia-1] < (-0.615))):
                # Comprobamos la rentabilidad y el volumen. Han hecho un contra split. Ajustamos el multiplicador.
                multiplicador[idia] = multiplicador[idia-1] * \
                    (cotizaciones.loc[idia-1, 'Último'] /
                        cotizaciones.loc[idia, 'Apertura'])
            # Comprobamos la rentabilidad y el volumen. Han hecho un split. Ajustamos el multiplicador.
            elif ((rentabilidades[idia-1] < (-0.615)) & (volumen[idia-1] > (0.615))):
                # Calculamos la relación entre el precio de cierre de ayer y la apertura de hoy.
                multiplicador[idia] < -multiplicador[idia-1] * \
                    (cotizaciones.loc[idia-1, 'Último'] /
                        cotizaciones.loc[idia, 'Apertura'])
            # No han hecho nada, el multiplicador no varía.
            else:
                multiplicador[idia] < -multiplicador[idia-1]

        cotizaciones.sort_index(inplace=True)
        cotizaciones.iloc[:, 1:-1] = cotizaciones.iloc[:, 1:-
                                                       1].multiply(multiplicador, axis="index")
        cotizaciones.iloc[:, -1] = cotizaciones.iloc[:, -
                                                     1].div(multiplicador, axis="index")

    return cotizaciones


def generar_df_activos(info_activos, fecha_inicio, fecha_fin):
    print("Iniciando el proceso de descarga de datos")
    # url_activo = "https://es.investing.com/equities/pharma-mar-sau-historical-data"
    activo = 1
    firsttime = True
    # for activo in info_activos.index:
    for activo in info_activos.index:
        time.sleep(random.randint(1, 5))
    # Descargamos las cotizaciones de los activos.
        print(activo)
        # cotizaciones = descargar_cotizaciones_diarias_investing(
        #     url_activo=info_activos.loc[activo], fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        cotizaciones = descargar_cotizaciones_diarias_investing(
            url_activo=info_activos.loc[activo]['link'], fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # cotizaciones.to_csv(info_activos.loc[0]['Nombre']+'.csv', sep=';')
        if(cotizaciones.empty):
            cotizaciones = descargar_cotizaciones_diarias_investing_api(
                info_activos.loc[activo], fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Limpiamos los datos descargados.
        #   cotizaciones<-limpiar(cotizaciones)
        cotizaciones = limpiar(cotizaciones)
        # Homogeneizamos los datos descargados.
        #   cotizaciones<-homogeneizar(cotizaciones, fecha_inicio, fecha_fin)
        cotizaciones = homogeneizar(cotizaciones, fecha_inicio, fecha_fin)
        # Eliminamos los split y contrasplit.
        cotizaciones = split_contrasplit(cotizaciones)
        if firsttime:
            firsttime = False
            apertura = pd.DataFrame(cotizaciones[['Apertura']])
            apertura.columns = [info_activos.loc[activo]['Nombre']]
            cierre = pd.DataFrame(cotizaciones[['Último']])
            cierre.columns = [info_activos.loc[activo]['Nombre']]
            maximo = pd.DataFrame(cotizaciones[['Máximo']])
            maximo.columns = [info_activos.loc[activo]['Nombre']]
            minimo = pd.DataFrame(cotizaciones[['Mínimo']])
            minimo.columns = [info_activos.loc[activo]['Nombre']]
            volumen = pd.DataFrame(cotizaciones[['Vol.']])
            volumen.columns = [info_activos.loc[activo]['Nombre']]
            apertura.set_index(pd.to_datetime(
                cotizaciones['Fecha']), inplace=True)
            cierre.set_index(pd.to_datetime(
                cotizaciones['Fecha']), inplace=True)
            maximo.set_index(pd.to_datetime(
                cotizaciones['Fecha']), inplace=True)
            minimo.set_index(pd.to_datetime(
                cotizaciones['Fecha']), inplace=True)
            volumen.set_index(pd.to_datetime(
                cotizaciones['Fecha']), inplace=True)

        else:
            cotizaciones.set_index(cotizaciones['Fecha'], inplace=True)
            apertura[info_activos.loc[activo]
                     ['Nombre']] = cotizaciones['Apertura']
            cierre[info_activos.loc[activo]['Nombre']] = cotizaciones['Último']
            maximo[info_activos.loc[activo]['Nombre']] = cotizaciones['Máximo']
            minimo[info_activos.loc[activo]['Nombre']] = cotizaciones['Mínimo']
            volumen[info_activos.loc[activo]['Nombre']] = cotizaciones['Vol.']

    return [apertura, cierre, maximo, minimo, volumen]


def obtener_info_indice(indice, fecha_inicio, fecha_fin):

    url_indice = indice.replace(
        '-components', '-historical-data')
    cotizaciones_indice = descargar_cotizaciones_diarias_investing(
        url_activo=url_indice, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    cotizaciones_indice = limpiar(cotizaciones_indice)
    cotizaciones_indice = homogeneizar(
        cotizaciones_indice, fecha_inicio, fecha_fin)
    cot_index = pd.DataFrame(cotizaciones_indice.iloc[:, 1:])
    cot_index.set_index(pd.to_datetime(
        cotizaciones_indice['Fecha']), inplace=True)
    return cot_index


def otener_info_divisa(divisa, fecha_inicio, fecha_fin):

    curr_cols = ["Fecha", "Último", "Apertura", "Máximo", "Mínimo", "X..var."]
    fechas = pd.bdate_range(start=fecha_inicio, end=fecha_fin).tolist()

    if(divisa == 'eur'):
        cotizaciones_divisa = pd.DataFrame(
            1,  columns=curr_cols, index=fechas)
        cotizaciones_divisa.loc[:, 'Fecha'] = fechas
    else:
        url_divisa = 'https://es.investing.com/currencies/eur-' + divisa+'-historical-data'
        cotizaciones_divisa = descargar_cotizaciones_diarias_investing(
            url_divisa, fecha_inicio, fecha_fin)

    # Limpiamos los datos descargados.
    cotizaciones_divisa = limpiar(cotizaciones_divisa)
    # Homogeneizamos los datos descargados.
    cotizaciones_divisa = homogeneizar(
        cotizaciones_divisa, fecha_inicio, fecha_fin)

    return cotizaciones_divisa.iloc[:, 1:-1]


def obtener_info_renta_fija(fecha_inicio, fecha_fin):
curvas_list = [
    'Fecha', 'ECONOMIA MUNDIAL. TIPO DE INTERES DIA A DIA . MERCADOS UEM-11. INTERBANCARIO. EONIA. ']
curvas_colnames = ['Fecha', 'Eonia']
monthdic = {
    "ENE": "01 ",
    "FEB": "02 ",
    "MAR": "03 ",
    "ABR": "04 ",
    "MAY": "05 ",
    "JUN": "06 ",
    "JUL": "07 ",
    "AGO": "08 ",
    "SEP": "09 ",
    "OCT": "10 ",
    "NOV": "11 ",
    "DIC": "12 ",
}
url = 'http://www.bde.es/webbde/es/estadis/infoest/series/ti_1_7.csv'
# use sep="," for coma separation.
curvas = pd.read_csv(url, encoding='latin-1')
curvas.columns = curvas.iloc[2]
curvas.rename(columns={curvas.columns[0]: "Fecha"}, inplace=True)

curvas = curvas.iloc[5:-2, :]
for key in monthdic:
    curvas['Fecha'] = curvas['Fecha'].str.replace(key, monthdic[key])

curvas['Fecha'] = pd.to_datetime(curvas['Fecha'], format='%d %m %Y')
curvas.set_index(curvas.loc[:, 'Fecha'].values, inplace=True)

curvas = curvas[curvas.columns.intersection(curvas_list)]
curvas.columns = (curvas_colnames)

curvas = curvas[(curvas['Eonia'] != "_")]
curvas.rename_axis(None, inplace=True)
curvas.sort_values(by='Fecha', ascending=False, inplace=True)
curvas = homogeneizar(curvas, fecha_inicio, fecha_fin)
curvas['Eonia'] = curvas['Eonia'].apply(
    pd.to_numeric, errors='coerce')
curvas['Eonia'] = np.log((1+curvas['Eonia'])**(1/365))
curvas.set_index(curvas['Fecha'], inplace=True)

curvas_fin = curvas.filter(['Eonia'], axis=1)

    return curvas_fin


def descarga_limpieza_homogeneizacion_desmanipulacion(indice, fecha_inicio, fecha_fin, ventana):

    # Funcion principal
    fecha_inicio = encontrar_fecha_anterior_inicio(fecha_inicio, ventana)
    info_activos = obtener_info_activos(indice)
    info_activos.to_csv('info_activos2.csv', sep=';')
    datos_descargados = generar_df_activos(
        info_activos, fecha_inicio, fecha_fin)

    # Obtenemos la información del índice.

    cotizaciones_indice = obtener_info_indice(indice, fecha_inicio, fecha_fin)
    datos_descargados.append(cotizaciones_indice)

    # Obtenemos la información de la divisa
    divisa = info_activos.loc[0, 'currency'].lower()
    cotizaciones_divisa = otener_info_divisa(divisa, fecha_inicio, fecha_fin)
    datos_descargados.append(cotizaciones_divisa)

    # Obtenemos la renta fija
    cotizaciones_renta_fija = obtener_info_renta_fija(fecha_inicio, fecha_fin)
    datos_descargados.append(cotizaciones_renta_fija)

    # Metemos el maestro de valores (info activos) como dato final.
    datos_descargados.append(info_activos)

    return datos_descargados


# %%
datos_descargados = descarga_limpieza_homogeneizacion_desmanipulacion(
    indice, fecha_inicio, fecha_fin, ventana)

# %%
