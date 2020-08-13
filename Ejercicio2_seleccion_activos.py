# Objetivo: Realiza la selección de los activos en función del percentil del Alpha de Jensen.

# Objetivo ejercicio 2.1: calcula el Alpha de Jensen para cada activo, en cada instante de tiempo.
# Objetivo ejercicio 2.2: calcula los precios objetivo de compra y venta
# Objetivo ejercicio 2.3: haz dinámicos los percentiles y la ventana


def calculamos_alpha(datos_descargados, ventana):
    # Los datos descargados están en formato de lista.
    cierre = datos_descargados[1]
    indice = datos_descargados[5].iloc[:, 0]
    renta_fija = datos_descargados[7].iloc[:, 0]

    # Calculamos la rentabilidad de los activos.
    cierre_log_ret = np.log(cierre.sort_index(ascending=True)).diff().fillna(0)
    indice_log_ret = np.log(indice.sort_index(ascending=True)).diff().fillna(0)

    renta_fija_ret = renta_fija/100
    renta_fija_ret.sort_index(ascending=True, inplace=True)
    rolling_cov = cierre_log_ret.rolling(ventana).cov(indice_log_ret)
    rolling_var = indice_log_ret.rolling(ventana).var()
    rolling_cov = rolling_cov.sort_index(ascending=False).fillna(
        method='ffill').sort_index(ascending=True)
    rolling_var = rolling_var.sort_index(ascending=False).fillna(
        method='ffill').sort_index(ascending=True)

    # Sacamos la Beta del activo. β=cov(Rc,Rm)/σRm
    beta = rolling_cov.div(rolling_var, axis='index')

    sub_rm_rf = indice_log_ret.sub(
        renta_fija_ret, axis='index').fillna(method='bfill')
    # indice_log_ret.sort_index(ascending=True, inplace=True)
    # cierre_log_ret.sort_index(ascending=True, inplace=True)
    # Calculamos el Alpha del activo. α=Rc-(Rf+β(Rm-Rf))
    alpha = beta.mul(sub_rm_rf, axis='index').add(
        renta_fija_ret, axis='index').mul(-1, axis='index').add(
            cierre_log_ret, axis='index').fillna(method='bfill')
    alpha.sort_index(ascending=False, inplace=True)
    return alpha


def precio_objetivo(alpha_objetivo, cotizaciones_activo, cotizaciones_indice, cotizaciones_renta_fija):
    # dia = temp_alpha_actual.index[0]
    # activo = alpha_actual.columns[0]
    # # alpha_objetivo = alpha_objetivo.loc[dia, activo]
    # cotizaciones_activo = cierre.loc[dia:(dia - BDay(ventana)), activo]
    # cotizaciones_indice = indice.loc[dia:(dia - BDay(ventana)), :]
    # cotizaciones_renta_fija = renta_fija.loc[dia:(dia - BDay(ventana))]
    # alpha_objetivo = alpha_entrada.loc[dia, activo]
    # cotizaciones_activo = cierre.loc[dia:(dia - BDay(ventana)), activo]
    # cotizaciones_indice = indice.loc[dia:(dia - BDay(ventana)), :]
    # cotizaciones_renta_fija = renta_fija.loc[dia:(dia - BDay(ventana))]
    # Calculamos la rentabilidad de los activos, su benchmark y el eonia.
    cotizaciones_activo_log_ret = np.log(
        cotizaciones_activo.sort_index(ascending=True)).diff()
    indice_log_ret = np.log(
        cotizaciones_indice.sort_index(ascending=True)).diff()

    renta_fija_ret = cotizaciones_renta_fija/100
    renta_fija_ret.sort_index(ascending=True)
    cotizaciones_activo_log_ret = cotizaciones_activo_log_ret.sort_index(
        ascending=True).fillna(method='bfill')
    indice_log_ret = indice_log_ret.sort_index(
        ascending=True).fillna(method='bfill')

    # Calculamos la varianza del benchmark
    varianza_benchmark = indice_log_ret.iloc[:, 0].var()

    # Calculamos la covarianza entre el activo y el benchmark
    covarianza_activos_benchmark = cotizaciones_activo_log_ret.cov(
        indice_log_ret.iloc[:, 0])

    # Sacamos la Beta de cada activo. β=cov(Rc,Rm)/σRm
    beta = covarianza_activos_benchmark/varianza_benchmark

    # Calculo la rentabilidad esperada RE= RF+Beta(RM-RF)
    rent_esperada = cotizaciones_renta_fija.iloc[0]+beta*(
        indice_log_ret.iloc[-1, 0]-cotizaciones_renta_fija.iloc[0])

    # Calculo la rentabilidad del precio de compra o venta. RPC = RE + Alpha entrada o RPV = RE + Alpha salida.
    rent_precio = alpha_objetivo+rent_esperada

    # Calculo el precio objetivo de compra o venta. Precio objetivo = Precio hoy * exp(Rent PC)
    precio_objetivo = cotizaciones_activo.iloc[0]*math.exp(rent_precio)
    return precio_objetivo

# Calculo la variación del percentil dinámico de entrada, en función de la recomendación de ayer y los precios de hoy.


def percentil_entrada_dinamico(precio_objetivo_compra, precio_objetivo_venta, maximo, minimo, entrada):

    # Si incremento el percentil, incremento el precio (subo la banda)
    # Si reduzco el percentil, bajo el precio (bajo la banda)

    # Si la banda toca el precio de compra, recomendado para ayer, comparándolo con los precios de hoy:
    #	No toca la vela y el mínimo está por encima, incrementamos la configuración de compra de ayer.
    #	No toca la vela y el máximo está por debajo, reducimos la configuración de compra de ayer.
    #	Si toca la vela pero la banda de venta no la toca, reducimos la configuración de compra.
    #	Si toca la vela y la banda de venta la toca, volvemos un paso a la configuración inicial de compra (15%).

    vector_percentiles_entrada = [0.0381, 0.0424, 0.0471, 0.0523, 0.0581, 0.0646, 0.0717, 0.0797, 0.0886, 0.0984, 0.1094,
                                  0.1215, 0.1350, 0.1500, 0.1650, 0.1815, 0.1997, 0.2196, 0.2416, 0.2657, 0.2923, 0.3215,
                                  0.3537, 0.3891, 0.4280, 0.4708]  # Usamos un vector de configuraciones xq los incrementos % son diferentes al ir en una direcicón y volver.

    # Comprobamos la posición del percentil dentro del vector.
    posicion = vector_percentiles_entrada.index(entrada)

    # Comprobamos si el precio recomendado ha tocado la vela.
    if((precio_objetivo_compra <= maximo) & (precio_objetivo_compra >= minimo)):

        # Comprobamos si la banda de venta toca la vela.
        if((precio_objetivo_venta <= maximo) & (precio_objetivo_venta >= minimo)):

            #	Si toca la vela y la banda de venta la toca, volvemos un paso a la configuración inicial de compra (15%).
            if (posicion > 13):

                entrada = vector_percentiles_entrada[posicion-1]

            elif (posicion < 13):

                entrada = vector_percentiles_entrada[posicion+1]
        else:

            # Si toca la vela y la banda de venta no la toca, reducimos la configuración de compra.
            if (posicion > 0):
                entrada = vector_percentiles_entrada[posicion-1]

    elif((precio_objetivo_compra < minimo) & (posicion < (len(vector_percentiles_entrada)-1))):

        # No toca la vela y el mínimo está por encima, incrementamos la configuración de compra de ayer.
        entrada = vector_percentiles_entrada[posicion+1]

    elif((precio_objetivo_compra > maximo) & (posicion > 0)):

        #	No toca la vela y el máximo está por debajo, reducimos la configuración de compra de ayer.
        entrada = vector_percentiles_entrada[posicion-1]

    return(entrada)


def percentil_salida_dinamico(precio_objetivo_compra, precio_objetivo_venta, maximo, minimo, salida):

    # Si incremento el percentil, incremento el precio (subo la banda)
    # Si reduzco el percentil, bajo el precio (bajo la banda)

    #	Si la banda de venta, en la recomendación anterior:
    #	No toca la vela y el máximo está por debajo, reducimos la configuración de venta.
    #	No toca la vela y el mínimo está por encima, incrementamos la configuración de venta.
    #	Si toca la vela pero la banda de compra no la toca, incrementamos la configuración de venta.
    #	Si toca la vela y la banda de compra la toca, volvemos un paso a la configuración de venta de (85%).

    vector_percentiles_salida = [0.5909, 0.6029, 0.6152, 0.6278, 0.6406, 0.6537, 0.6670, 0.6806, 0.6945, 0.7087, 0.7231,
                                 0.7379, 0.7530, 0.7683, 0.7840, 0.8000, 0.8163, 0.8330, 0.8500, 0.8670, 0.8843, 0.9020,
                                 0.9201, 0.9385, 0.9572, 0.9764]  # Usamos un vector de configuraciones xq los incrementos % son diferentes al ir en una direcicón y volver.

    # Comprobamos la posición del percentil dentro del vector.
    posicion = vector_percentiles_salida.index(salida)

    # Comprobamos si el precio recomendado ha tocado la vela.
    if((precio_objetivo_venta <= maximo) & (precio_objetivo_venta >= minimo)):

        # Comprobamos si la banda de compra toca la vela.
        if((precio_objetivo_compra <= maximo) & (precio_objetivo_compra >= minimo)):

            #	Si toca la vela y la banda de compra la toca, volvemos un paso a la configuración de venta (85%).
            if (posicion > 18):

                salida = vector_percentiles_salida[posicion-1]

            elif (posicion < 18):

                salida = vector_percentiles_salida[posicion+1]

        else:

            #	Si toca la vela pero la banda de compra no la toca, incrementamos la configuración de venta.
            if (posicion < (len(vector_percentiles_salida)-1)):
                salida = vector_percentiles_salida[posicion+1]

    elif((precio_objetivo_venta < minimo) & (posicion < (len(vector_percentiles_salida)-1))):

        #	No toca la vela y el mínimo está por encima, incrementamos la configuración de venta.
        salida = vector_percentiles_salida[posicion+1]

    elif((precio_objetivo_venta > maximo) & (posicion > 0)):

        #	No toca la vela y el máximo está por debajo, reducimos la configuración de venta.
        salida = vector_percentiles_salida[posicion-1]

    return(salida)


def seleccion_activos(datos_descargados, ventana, entrada, salida, percentil_dinamico, fecha_inicio):
    print("Iniciando el proceso de selección de activos")

    # Calculamos el Alpha de Jensen
    alpha_actual = calculamos_alpha(datos_descargados, ventana)
    apertura = datos_descargados[0]
    cierre = datos_descargados[1]
    maximo = datos_descargados[2]
    minimo = datos_descargados[3]
    volumen = datos_descargados[4]
    indice = datos_descargados[5]
    divisa = datos_descargados[6]
    renta_fija = datos_descargados[7].iloc[:, 0]

    fecha_inicio_datos = fecha_inicio - BDay(2*ventana)
    date_calculos_mask = (alpha_actual.index >= fecha_inicio_datos)
    temp_alpha_actual = alpha_actual[date_calculos_mask].sort_index(
        ascending=True)
    fecha_inicio_calculos = fecha_inicio - BDay(ventana)
    date_datos_mask = (alpha_actual.index >= fecha_inicio_calculos)
    temp_fechas = alpha_actual[date_datos_mask].sort_index(
        ascending=True)
    # alpha_entrada = pd.DataFrame(
    #     0, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # alpha_salida = pd.DataFrame(
    #     0, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # precio_objetivo_compra = pd.DataFrame(
    #     0, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # precio_objetivo_venta = pd.DataFrame(
    #     0, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # seleccion_activos = pd.DataFrame(
    #     0, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # percentil_entrada = pd.DataFrame(
    #     entrada, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # percentil_salida = pd.DataFrame(
    #     salida, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    # ventana_dinamica = pd.DataFrame(
    #     ventana, index=alpha_actual.index[date_calculos_mask], columns=alpha_actual.columns)
    alpha_entrada = pd.DataFrame(
        0, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    alpha_salida = pd.DataFrame(
        0, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    precio_objetivo_compra = pd.DataFrame(
        0, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    precio_objetivo_venta = pd.DataFrame(
        0, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    seleccion_activos = pd.DataFrame(
        0, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    percentil_entrada = pd.DataFrame(
        entrada, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    percentil_salida = pd.DataFrame(
        salida, index=temp_alpha_actual.index, columns=alpha_actual.columns)
    ventana_dinamica = pd.DataFrame(
        ventana, index=temp_alpha_actual.index, columns=alpha_actual.columns)

    for dia in temp_fechas.index:
        for activo in alpha_actual.columns:
            if percentil_dinamico:
                if (fecha_inicio_calculos != dia):
                    prev_day = dia - BDay(1)

                    # Consultamos si hemos tocado la vela el día anterior y variamos los percentiles de entrada y salida en función de ello.
                    percentil_entrada.loc[dia, activo] = percentil_entrada_dinamico(
                        precio_objetivo_compra.loc[prev_day, activo], precio_objetivo_venta.loc[prev_day, activo], maximo.loc[dia, activo], minimo.loc[dia, activo], percentil_entrada.loc[prev_day, activo])
                    percentil_salida.loc[dia, activo] = percentil_salida_dinamico(
                        precio_objetivo_compra.loc[prev_day, activo], precio_objetivo_venta.loc[prev_day, activo], maximo.loc[dia, activo], minimo.loc[dia, activo], percentil_salida.loc[prev_day, activo])

                    # Cambiamos la ventana en función únicamente del POC (lo que queremos evitar es que el POC esté siempre por debajo de las siguientes velas en una fuerte subida).
                    if(percentil_entrada.loc[dia, activo] > 0.15):
                        if(percentil_entrada.loc[dia, activo] > percentil_entrada.loc[prev_day, activo]):
                            # Nos estamos alejando del percentil estandar, acortamos la ventana
                            ventana_dinamica.loc[dia, activo] = round(
                                ventana_dinamica.loc[prev_day, activo]/1.35, 0)
                        elif(percentil_entrada.loc[dia, activo] < percentil_entrada.loc[prev_day, activo]):
                            # Regresamos al percentil estandar, ampliamos la ventana
                            ventana_dinamica.loc[dia, activo] = round(
                                ventana_dinamica.loc[prev_day, activo]*1.35, 0)
                            if (ventana_dinamica.loc[dia, activo] > ventana):
                                ventana_dinamica.loc[dia, activo] = ventana
                        else:
                            # Mantenemos la ventana anterior
                            ventana_dinamica.loc[dia,
                                                 activo] = ventana_dinamica.loc[prev_day, activo]

                    elif(percentil_entrada.loc[dia, activo] < 0.15):
                        if(percentil_entrada.loc[dia, activo] < percentil_entrada.loc[prev_day, activo]):
                            # Nos estamos alejando del percentil estandar, acortamos la ventana
                            ventana_dinamica.loc[dia, activo] = round(
                                ventana_dinamica.loc[prev_day, activo]/1.35, 0)
                        elif(percentil_entrada.loc[dia, activo] > percentil_entrada.loc[prev_day, activo]):
                            # Regresamos al percentil estandar, ampliamos la ventana
                            ventana_dinamica.loc[dia, activo] = round(
                                ventana_dinamica.loc[prev_day, activo]*1.35, 0)
                            if (ventana_dinamica.loc[dia, activo] > ventana):
                                ventana_dinamica.loc[dia, activo] = ventana
                        else:
                            # Mantenemos la ventana anterior
                            ventana_dinamica.loc[dia,
                                                 activo] = ventana_dinamica.loc[prev_day, activo]
                    else:
                        # Estamos en el percentil estandar, regresamos a la normalidad
                        ventana_dinamica.loc[dia, activo] = ventana

            # Comprobamos que el tamaño de la ventana dinámica no baja nunca de un umbral mínimo.
            if(ventana_dinamica.loc[dia, activo] < 5):
                ventana_dinamica.loc[dia, activo] = 5
            # Calculamos el Alpha de entrada (punto a partir del que compraríamos)
            alpha_entrada.loc[dia, activo] = alpha_actual.loc[dia:(
                dia - BDay(ventana_dinamica.loc[dia, activo])), activo].quantile(percentil_entrada.loc[dia, activo])
            # Calculamos el Alpha de salida (punto a partir del que venderíamos)
            alpha_salida.loc[dia, activo] = alpha_actual.loc[dia:(
                dia - BDay(ventana_dinamica.loc[dia, activo])), activo].quantile(percentil_salida.loc[dia, activo])
            # Calculamos el precio objetivo de compra para el periodo siguiente
            precio_objetivo_compra.loc[dia, activo] = precio_objetivo(alpha_entrada.loc[dia, activo], cierre.loc[dia:(
                dia - BDay(ventana_dinamica.loc[dia, activo])), activo], indice.loc[dia:(dia - BDay(ventana_dinamica.loc[dia, activo])), :], renta_fija.loc[dia:(dia - BDay(ventana_dinamica.loc[dia, activo]))])
            # Calculamos el precio objetivo de venta para el periodo siguiente
            precio_objetivo_venta.loc[dia, activo] = precio_objetivo(alpha_salida.loc[dia, activo], cierre.loc[dia:(
                dia - BDay(ventana_dinamica.loc[dia, activo])), activo], indice.loc[dia:(dia - BDay(ventana_dinamica.loc[dia, activo])), :], renta_fija.loc[dia:(dia - BDay(ventana_dinamica.loc[dia, activo]))])

    # Acortamos el tamaño de los DF para ajustarlos a la fecha_inicio y fecha_fin
    date_mask = (percentil_entrada.index >= fecha_inicio)
    percentil_entrada = percentil_entrada.iloc[date_mask, :]
    percentil_salida = percentil_salida.iloc[date_mask, :]
    alpha_entrada = alpha_entrada.iloc[date_mask, :]
    alpha_salida = alpha_salida.iloc[date_mask, :]
    precio_objetivo_compra = precio_objetivo_compra.iloc[date_mask, :]
    precio_objetivo_venta = precio_objetivo_venta.iloc[date_mask, :]
    ventana_dinamica = ventana_dinamica.iloc[date_mask, :]

    lista_activos = [percentil_entrada, percentil_salida, alpha_entrada,
                     alpha_salida, precio_objetivo_compra, precio_objetivo_venta, ventana_dinamica]
    return lista_activos


# %%
activos_seleccionados = seleccion_activos(
    datos_descargados, ventana, entrada, salida, percentil_dinamico, fecha_inicio)


# %%
