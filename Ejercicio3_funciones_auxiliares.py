def ranking_de_asignacion_recursos(datos_descargados, activos_seleccionados, ventana, comision_minima):

    apertura = datos_descargados[0]
    cierre = datos_descargados[1]
    maximo = datos_descargados[2]
    minimo = datos_descargados[3]
    volumen = datos_descargados[4]
    indice = datos_descargados[5]
    divisa = datos_descargados[6]
    # Nos quedamos sólo cone l close de la divisa
    divisa = divisa.iloc[:, 0]
    alpha_entrada = activos_seleccionados[2]
    precio_objetivo_compra = activos_seleccionados[4]
    precio_objetivo_venta = activos_seleccionados[5]

    fecha_inicio_calculos = cierre.index[-1] + BDay(3*ventana)
    date_calculos_mask = (cierre.index >= fecha_inicio_calculos)
    temp_cierre = cierre[date_calculos_mask].sort_index(
        ascending=True)

    volumen_minimo = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    volumen_maximo = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    frecuencia_condicion_compra = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    ultima_condicion_compra = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    frecuencia_condicion_venta = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    ultima_condicion_venta = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)
    ranking = pd.DataFrame(
        0, index=cierre.index, columns=cierre.columns)

    dia = temp_cierre.index[0]
    activo = cierre.columns[0]
    for dia in temp_cierre.index:
        for activo in cierre.columns:
            # Calculamos el volumen mínimo a comprar (aquel que cubre las comisiones). redondear(comision/(precio_venta - precio_compra))
            volumen_minimo.loc[dia, activo] = math.floor(
                comision_minima*2/(precio_objetivo_venta.loc[dia, activo]/divisa.loc[dia]-precio_objetivo_compra.loc[dia, activo]/divisa.loc[dia]))+1
            # Calculamos el volumen máximo a comprar (umbral de arrastre). 0,5% del volumen medio de las últimas sesiones.
            volumen_maximo.loc[dia, activo] = math.floor(
                np.mean(volumen.loc[dia:(dia - BDay(ventana)), activo])*0.005)
            # Calculamos el porcentaje de veces que se ha cumplido la condición de compra en la ventana temporal.
            frecuencia_condicion_compra.loc[dia, activo] = sum(minimo.loc[dia:(
                dia - BDay(ventana)), activo] <= precio_objetivo_compra.loc[dia, activo])/(ventana+1)
            # Calculamos la última vez que se ha cumplido la condición de compra en la ventana temporal.
            if(frecuencia_condicion_compra.loc[dia, activo] > 0):
                ultima_condicion_compra.loc[dia, activo] = np.where((minimo.loc[dia:(
                    dia - BDay(ventana)), activo] <= precio_objetivo_compra.loc[dia, activo]) == True)[0][0]+1
            else:
                ultima_condicion_compra.loc[dia, activo] = ventana*2

            # Calculamos el porcentaje de veces que se ha cumplido la condición de venta en la ventana temporal.
            frecuencia_condicion_venta.loc[dia, activo] = sum(maximo.loc[dia:(
                dia - BDay(ventana)), activo] >= precio_objetivo_venta.loc[dia, activo])/(ventana+1)
            # Calculamos la última vez que se ha cumplido la condición de venta en la ventana temporal.
            if(frecuencia_condicion_venta.loc[dia, activo] > 0):
                ultima_condicion_venta.loc[dia, activo] = np.where((maximo.loc[dia:(
                    dia - BDay(ventana)), activo] >= precio_objetivo_venta.loc[dia, activo]) == True)[0][0]+1
            else:
                ultima_condicion_venta.loc[dia, activo] = ventana*2
            # Fabricamos un ranking de asignación de recursos en función de la probabilidad de ocurrencia.
            ranking.loc[dia, activo] = (frecuencia_condicion_venta.loc[dia, activo]/ultima_condicion_venta.loc[dia, activo])*(
                frecuencia_condicion_compra.loc[dia, activo]/ultima_condicion_compra.loc[dia, activo])
        # Transformamos la probabilidad de ocurrencia en un ranking (el activo conmayor puntuación será el primero que recibirá recursos disponibles).
        ranking.loc[dia, :] = ranking.loc[dia, :].rank()

    datos_ranking_asignacion = [volumen_minimo, volumen_maximo, frecuencia_condicion_compra,
                                ultima_condicion_compra, frecuencia_condicion_venta, ultima_condicion_venta, ranking]

    return datos_ranking_asignacion

# Generamos la recomendación para el día siguiente


def generar_recomendacion(datos_descargados, activos_seleccionados, datos_ranking_asignacion, beneficio_objetivo_por_operacion, stop_loss, comision, comision_minima, fecha_fin, fecha_inicio):

    cierre = datos_descargados[1]
    volumen = datos_descargados[4]
    divisa = datos_descargados[6].iloc[:, 0]
    precio_objetivo_compra = activos_seleccionados[4]
    precio_objetivo_venta = activos_seleccionados[5]
    volumen_minimo = datos_ranking_asignacion[0]
    volumen_maximo = datos_ranking_asignacion[1]
    frecuencia_condicion_compra = datos_ranking_asignacion[2]
    frecuencia_condicion_venta = datos_ranking_asignacion[4]
    ranking = datos_ranking_asignacion[6]

    recomendacion_manana = pd.DataFrame(
        0, index=range(0, 16), columns=cierre.columns)

    # Nombre de los activos.
    recomendacion_manana.iloc[0, :] = recomendacion_manana.columns
    # Precio de cierre de ayer.
    recomendacion_manana.iloc[1, :] = cierre.loc[fecha_fin, :]
    # Precio objetivo de compra.
    recomendacion_manana.iloc[2, :] = precio_objetivo_compra.loc[fecha_fin, :]
    # Precio objetivo de venta.
    recomendacion_manana.iloc[3, :] = precio_objetivo_venta.loc[fecha_fin, :]
    recomendacion_manana.iloc[4, :] = precio_objetivo_venta.loc[fecha_fin, :] - \
        precio_objetivo_compra.loc[fecha_fin, :]  # Horquilla.
    recomendacion_manana.iloc[5, :] = (precio_objetivo_venta.loc[fecha_fin, :]-precio_objetivo_compra.loc[fecha_fin, :]
                                       )/precio_objetivo_compra.loc[fecha_fin, :]  # Rentabilidad esperada
    recomendacion_manana.iloc[6, :] = frecuencia_condicion_compra.loc[fecha_fin,
                                                                      :]*frecuencia_condicion_venta.loc[fecha_fin, :]  # Probabilidad de ocurrencia
    recomendacion_manana.iloc[7, :] = precio_objetivo_compra.loc[fecha_fin, :]-(
        precio_objetivo_venta.loc[fecha_fin, :]-precio_objetivo_compra.loc[fecha_fin, :])*stop_loss  # Stop loss
    # Beneficio objetivo por operación
    recomendacion_manana.iloc[8, :] = beneficio_objetivo_por_operacion

    for accion in recomendacion_manana.columns:

        # Bº=(pv-pc)*nacc-com
        # 100=(12-11)*nacc-(0,008*nacc*12)-(0,008*nacc*11)
        # 100=1nacc-0,096nacc-0,088nacc
        # 100=1nacc-0,096nacc-0,088nacc
        # 100=0,816nacc
        # nacc=100/0,816 --> 122,54 acciones a comprar

        if ((precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-precio_objetivo_compra.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-comision*precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-comision*precio_objetivo_compra.loc[fecha_fin, accion]/divisa.loc[fecha_fin]) > 0):

            recomendacion_manana.loc[9, accion] = round(beneficio_objetivo_por_operacion/(precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-precio_objetivo_compra.loc[fecha_fin, accion] /
                                                                                          divisa.loc[fecha_fin]-comision*precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-comision*precio_objetivo_compra.loc[fecha_fin, accion]/divisa.loc[fecha_fin]))+1  # Num de acciones
            recomendacion_manana.loc[10, accion] = ((recomendacion_manana.loc[9, accion]))*precio_objetivo_compra.loc[fecha_fin, accion]/divisa.loc[fecha_fin]*comision+(
                (recomendacion_manana.loc[9, accion]))*precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]*comision  # Comisiones

            # Comprobamos que la comisión es mayor que la comisión mínima.
            if (((recomendacion_manana.loc[10, accion])) < comision_minima*2):

                recomendacion_manana.loc[9, accion] = round((beneficio_objetivo_por_operacion+comision_minima*2)/(
                    precio_objetivo_venta.loc[fecha_fin, accion]/divisa.loc[fecha_fin]-precio_objetivo_compra.loc[fecha_fin, accion]/divisa.loc[fecha_fin]))
                recomendacion_manana.loc[10, accion] = comision_minima*2

    else:  # Las comisiones son superiores a los beneficios. No compensa hacer la operación.
        recomendacion_manana.loc[9, accion] = 0
        recomendacion_manana.loc[10, accion] = 0

    recomendacion_manana.iloc[11, :] = (precio_objetivo_compra.loc[fecha_fin, :] /
                                        divisa.loc[fecha_fin])*((recomendacion_manana.loc[9, :]))  # Capital invertido
    recomendacion_manana.iloc[12, :] = ((recomendacion_manana.loc[9, :])) / \
        volumen.loc[fecha_fin:fecha_inicio, :].mean()  # % sobre volumen diario
    # Volumen mínimo
    recomendacion_manana.iloc[13, :] = volumen_minimo.loc[fecha_fin, :]
    # Volumen máximo
    recomendacion_manana.iloc[14, :] = volumen_maximo.loc[fecha_fin, :]
    recomendacion_manana.iloc[15, :] = ranking.loc[fecha_fin, :]
    recomendacion_manana.sort_values(
        by=15, axis=1, ascending=False, inplace=True)
    recomendacion_manana.index = ["Activo", "Ultimo cierre (en div)", "Precio obj compra (en div)", "Precio obj venta (en div)", "Horquilla", "Rentabilidad esperada", "Probabilidad ocurrencia",
                                  "Stop loss (en div)", "Bº obj por operación (en eur)", "Nº de acc a comprar", "Comisiones (en eur)", "Capital invertido (en eur)", "% sobre volumen diario", "Vol mínimo comprar (nº acc)", "Vol máximo (nº acc)", "Rank"]
    recomendacion_manana = recomendacion_manana.transpose()
    recomendacion_manana.to_excel(
        'recomendacion_manana.xlsx', engine='xlsxwriter')
    return recomendacion_manana


datos_ranking_asignacion = ranking_de_asignacion_recursos(
    datos_descargados, activos_seleccionados, ventana, comision_minima)

recomendacion_manana = generar_recomendacion(datos_descargados, activos_seleccionados, datos_ranking_asignacion,
                                             beneficio_objetivo_por_operacion, stop_loss, comision, comision_minima, fecha_fin, fecha_inicio)
