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
                ultima_condicion_compra.loc[dia, activo] =np.where((minimo.loc[dia:(
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
def generar_recomendacion(datos_descargados, activos_seleccionados, datos_ranking_asignacion, beneficio_objetivo_por_operacion, stop_loss, comision, comision_minima):







datos_ranking_asignacion = ranking_de_asignacion_recursos(
    datos_descargados, activos_seleccionados, ventana, comision_minima)
