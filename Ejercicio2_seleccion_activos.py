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
    cierre_log_ret = np.log(cierre.sort_index(ascending=True)).diff()
    cierre_log_ret.sort_index(ascending=False, inplace=True)
    indice_log_ret = np.log(indice.sort_index(ascending=True)).diff()
    indice_log_ret.sort_index(ascending=False, inplace=True)

    renta_fija_ret = renta_fija/100
    rolling_cov = cierre_log_ret.rolling(ventana).cov(indice_log_ret)
    rolling_var = indice_log_ret.rolling(ventana).var()
    # Sacamos la Beta del activo. β=cov(Rc,Rm)/σRm
    beta = rolling_cov.div(rolling_var, axis='index')

    sub_rm_rf = indice_log_ret.sub(renta_fija_ret, axis='index')
    indice_log_ret.sort_index(ascending=False, inplace=True)
    cierre_log_ret.sort_index(ascending=False, inplace=True)
    # Calculamos el Alpha del activo. α=Rc-(Rf+β(Rm-Rf))
    alpha = beta.mul(sub_rm_rf, axis='index').add(
        renta_fija_ret, axis='index').mul(-1, axis='index').add(
            cierre_log_ret, axis='index')

    return alpha


 def precio_objetivo(alpha_objetivo, cotizaciones_activo, cotizaciones_indice, cotizaciones_renta_fija):
    
    # Calculamos la rentabilidad de los activos, su benchmark y el eonia.
    cotizaciones_activo_log_ret = np.log(cotizaciones_activo.sort_index(ascending=True)).diff()
    cotizaciones_activo_log_ret.sort_index(ascending=False, inplace=True)
    indice_log_ret = np.log(indice.sort_index(ascending=True)).diff()
    indice_log_ret.sort_index(ascending=False, inplace=True)
    indice_log_ret.iloc[-1] = indice_log_ret.iloc[-2]
    cotizaciones_activo_log_ret.iloc[-1] = cotizaciones_activo_log_ret.iloc[-2]

    renta_fija_ret = cotizaciones_renta_fija/100
    
    # Calculamos la varianza del benchmark
    varianza_benchmark=indice_log_ret.var()
    
    # Calculamos la covarianza entre el activo y el benchmark
    covarianza_activos_benchmark = cotizaciones_activo_log_ret.cov(cotizaciones_activo) 
    
    # Sacamos la Beta de cada activo. β=cov(Rc,Rm)/σRm
    beta =  covarianza_activos_benchmark.div(varianza_benchmark, axis='index')
    
    # Calculo la rentabilidad esperada RE= RF+Beta(RM-RF)
    rent_esperada=cotizaciones_renta_fija.iloc[0]+beta*(rent_benchmark.iloc[0]-cotizaciones_renta_fija.iloc[0])
    
    # Calculo la rentabilidad del precio de compra o venta. RPC = RE + Alpha entrada o RPV = RE + Alpha salida.
    rent_precio=alpha_objetivo+rent_esperada
    
    # Calculo el precio objetivo de compra o venta. Precio objetivo = Precio hoy * exp(Rent PC)
    precio_objetivo=cotizaciones_activo.iloc[0]*exp(rent_precio)
    return precio_objetivo

   def seleccion_activos(datos_descargados, ventana, entrada, salida, percentil_dinamico, fecha_inicio):
    apertura = datos_descargados[0]
    cierre = datos_descargados[1]
    maximo = datos_descargados[2]
    minimo = datos_descargados[3]
    volumen = datos_descargados[4]
    indice = datos_descargados[5]
    divisa = datos_descargados[6]
    renta_fija = datos_descargados[7].iloc[:,0]
