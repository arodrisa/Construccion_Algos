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

# Calculo la variación del percentil dinámico de entrada, en función de la recomendación de ayer y los precios de hoy. 
def percentil_entrada_dinamico(precio_objetivo_compra, precio_objetivo_venta, maximo, minimo, entrada):
    
    # Si incremento el percentil, incremento el precio (subo la banda)
    # Si reduzco el percentil, bajo el precio (bajo la banda)
    
    # Si la el precio de compra, recomendado para ayer, comparándolo con los precios de hoy:
    #	No toca la vela y el mínimo está por encima, incrementamos la configuración de compra de ayer.
    #	No toca la vela y el máximo está por debajo, reducimos la configuración de compra de ayer.
    #	Si toca la vela pero la banda de venta no la toca, reducimos la configuración de compra.
    #	Si toca la vela y la banda de venta la toca, volvemos un paso a la configuración inicial de compra (15%).
    
    vector_percentiles_entrada=[0.0381, 0.0424, 0.0471, 0.0523, 0.0581, 0.0646, 0.0717, 0.0797, 0.0886, 0.0984, 0.1094,
                                  0.1215, 0.1350, 0.1500, 0.1650, 0.1815, 0.1997, 0.2196, 0.2416, 0.2657, 0.2923, 0.3215,
                                  0.3537, 0.3891, 0.4280, 0.4708] # Usamos un vector de configuraciones xq los incrementos % son diferentes al ir en una direcicón y volver.
    
    # Comprobamos la posición del percentil dentro del vector.
    posicion = vector_percentiles_entrada.index(entrada)
    
    # Comprobamos si el precio recomendado ha tocado la vela.
    if(precio_objetivo_compra <= maximo & precio_objetivo_compra >= minimo):
      
        # Comprobamos si la banda de venta toca la vela.
        if(precio_objetivo_venta <= maximo & precio_objetivo_venta >= minimo):
            
            #	Si toca la vela y la banda de venta la toca, volvemos un paso a la configuración inicial de compra (15%).
                if (posicion > 14):
                
                    entrada=vector_percentiles_entrada[posicion-1]
                
                 else if (posicion < 14):
                   
                    entrada=vector_percentiles_entrada[posicion+1]
        else:
            
            # Si toca la vela y la banda de venta no la toca, reducimos la configuración de compra.
            if (posicion > 1):
                entrada=vector_percentiles_entrada[posicion-1]
            
        
      
    else if(precio_objetivo_compra < minimo & posicion < len(vector_percentiles_entrada)):
      
        # No toca la vela y el mínimo está por encima, incrementamos la configuración de compra de ayer.
        entrada=vector_percentiles_entrada[posicion+1]
      
    else if(precio_objetivo_compra > maximo & posicion > 1):
      
        #	No toca la vela y el máximo está por debajo, reducimos la configuración de compra de ayer.
        entrada=vector_percentiles_entrada[posicion-1]

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
                                    0.9201, 0.9385, 0.9572, 0.9764] # Usamos un vector de configuraciones xq los incrementos % son diferentes al ir en una direcicón y volver.

    # Comprobamos la posición del percentil dentro del vector.
    posicion = vector_percentiles_salida.index(salida)

    # Comprobamos si el precio recomendado ha tocado la vela.
    if(precio_objetivo_venta <= maximo & precio_objetivo_venta >= minimo):
        
        # Comprobamos si la banda de compra toca la vela.
        if(precio_objetivo_compra <= maximo & precio_objetivo_compra >= minimo):
        
        #	Si toca la vela y la banda de compra la toca, volvemos un paso a la configuración de venta (85%).
        if (posicion > 19):
            
            salida=vector_percentiles_salida[posicion-1]
            
         else if (posicion < 19):
            
            salida=vector_percentiles_salida[posicion+1]
        
        
         else:
        
        #	Si toca la vela pero la banda de compra no la toca, incrementamos la configuración de venta.
        if (posicion < length(vector_percentiles_salida)):
            salida=vector_percentiles_salida[posicion+1]
        
        
     else if(precio_objetivo_venta < minimo & posicion < len(vector_percentiles_salida)):
        
        #	No toca la vela y el mínimo está por encima, incrementamos la configuración de venta.
        salida=vector_percentiles_salida[posicion+1]
        
     else if(precio_objetivo_venta > maximo & posicion > 1):
        
        #	No toca la vela y el máximo está por debajo, reducimos la configuración de venta.
        salida=vector_percentiles_salida[posicion-1]
    

    return(salida)







   def seleccion_activos(datos_descargados, ventana, entrada, salida, percentil_dinamico, fecha_inicio):
    apertura = datos_descargados[0]
    cierre = datos_descargados[1]
    maximo = datos_descargados[2]
    minimo = datos_descargados[3]
    volumen = datos_descargados[4]
    indice = datos_descargados[5]
    divisa = datos_descargados[6]
    renta_fija = datos_descargados[7].iloc[:,0]
