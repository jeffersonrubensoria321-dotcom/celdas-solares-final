"""Proyecto 1 / Problema 2.3. Ejecutar: streamlit run app.py."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
from constantes import *
from modelo import (spectral,spectrum,device,cascade,thermal_curve,validations,
                    comparison,analytical_slope,thermal_reference,LOSS_NAMES)
from animacion import energy_animation

st.set_page_config(page_title='Silicio · Luz, pérdidas y temperatura',page_icon='☀️',layout='wide')
st.markdown('''<style>
.block-container{max-width:1400px;padding-top:2rem}h1{letter-spacing:-.04em}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums}
[data-testid="stSidebar"]{border-right:1px solid #dbe2e8}
</style>''',unsafe_allow_html=True)

def reset(ideal=False):
    for k,v in DEFAULTS.items(): st.session_state[k]=v
    for i in range(8): st.session_state[f'loss{i}']=i<4 if ideal else True

if 'eg' not in st.session_state: reset()
with st.sidebar:
    st.header(f'☀ Silicio / S = {SEED}')
    st.caption('Proyecto 1 · Problema 2.3 · Equipo de dos integrantes')
    st.info(f'Asignado: semilla **{SEED}**, temperatura inicial **{T_DEFAULT_C:.0f} °C**.\n\nEspesor fijo: **100 µm** (caso canónico).')
    st.caption('Semilla: (4 + 5 + 6 + 2 + 0 + 4) mod 10 = 1. No se usan los dígitos verificadores.')
    st.button('Restablecer mi escenario',on_click=reset,use_container_width=True)
    st.button('Ver límite ideal del curso',on_click=reset,args=(True,),use_container_width=True)
    st.slider('Banda prohibida Eg (eV)',.5,3.0,step=.01,key='eg')
    st.slider('Temperatura de operación (°C)',15.,75.,step=1.,key='temp')
    st.caption('Eg explora un material hipotético. El barrido térmico estudia silicio con Eg(T).')
    with st.expander('Recombinación: parámetros exploratorios'):
        st.checkbox('SRH en volumen',key='srh');st.checkbox('Superficie y contactos',key='surface')
        st.checkbox('Radiativa',key='radiative')
        st.slider('Vida SRH en volumen (µs)',10.,1000.,step=10.,key='tau_us')
        st.number_input('S frontal (cm/s)',0.,100000.,step=100.,key='sf')
        st.number_input('S trasera/contacto (cm/s)',0.,100000.,step=100.,key='sr')
        st.caption('Estos controles son supuestos exploratorios; el anexo A solo asigna T al problema 2.3.')
    with st.expander('Óptica y circuito'):
        st.slider('Reflectancia frontal (fracción)',0.,.6,step=.01,key='reflection')
        st.slider('Área sombreada (fracción)',0.,.3,step=.01,key='shade')
        st.slider('Camino óptico / espesor (1)',1.,50.,step=1.,key='path')
        st.slider('Resistencia serie (Ω·cm²)',0.,3.,step=.1,key='rs')
        st.number_input('Resistencia paralela (Ω·cm²)',100.,1000000.,step=100.,key='rp')
    st.caption('Python + Streamlit · Modelo propio · IA utilizada: ChatGPT/Codex')

st.title('¿Dónde se pierde la energía solar?')
st.markdown('Explora cómo la luz se transforma en electricidad y por qué una celda caliente entrega menos potencia.')
tab1,tab2,tab3,tab4=st.tabs(['01 · Espectro solar','02 · Cascada de pérdidas','03 · Temperatura','Validación'])

def chart(fig,x=None,y=None,height=400):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=35,r=20,t=35,b=45),
                      font=dict(family='Arial',size=13),legend=dict(orientation='h',y=-.2))
    if x:fig.update_xaxes(title_text=x)
    if y:fig.update_yaxes(title_text=y)
    st.plotly_chart(fig,use_container_width=True)

with tab2:
    st.subheader('Ocho mecanismos, un balance de energía')
    st.caption('Activa o desactiva cada peldaño. Los valores se recalculan desde el modelo, sin porcentajes de pérdida prefijados.')
    cols=st.columns(2)
    for i,name in enumerate(LOSS_NAMES):
        with cols[i%2]: st.checkbox(f'{i+1}. {name}',key=f'loss{i}')

# Todos los widgets se leen DESPUÉS de construirse. Estado único entre pestañas.
p={k:st.session_state[k] for k in DEFAULTS}
enabled=[st.session_state[f'loss{i}'] for i in range(8)];p['enabled']=enabled
s=spectral(p['eg']);cas=cascade(p,enabled)

with tab1:
    st.subheader('La luz tiene distintos colores y distintas energías')
    a,b,c,d,e=st.columns(5)
    a.metric('Irradiancia integrada',f'{s["pin"]:.2f} W/m²')
    b.metric('Fotones con E > Eg',f'{s["flux"]:.3e} cm⁻² s⁻¹')
    c.metric('Jsc máxima',f'{s["jl"]*1000:.2f} mA/cm²')
    d.metric('λ de corte (λg)',f'{s["cutoff"]:.0f} nm')
    e.metric('Irradiancia en λg',f'{s["p"][-1]:.3f} W·m⁻²·nm⁻¹')
    x,y=spectrum();z=s['x'];use=s['photons']*p['eg']*Q
    f=go.Figure()
    f.add_trace(go.Scatter(x=z,y=use,fill='tozeroy',name='Energía tras termalización',line=dict(color='#179a80',width=1)))
    f.add_trace(go.Scatter(x=z,y=s['p'],fill='tonexty',name='Exceso convertido en calor',line=dict(color='#d58a2c',width=1)))
    beyond=np.append(s['cutoff'],x[x>s['cutoff']]);py=np.interp(beyond,x,y)
    f.add_trace(go.Scatter(x=beyond,y=py,fill='tozeroy',name='Sub-bandgap: no absorbida',line=dict(color='#8b97a5',width=1)))
    f.add_vline(x=s['cutoff'],line_dash='dash',annotation_text=f'λg = {s["cutoff"]:.0f} nm')
    chart(f,'Longitud de onda λ (nm)','Irradiancia espectral (W·m⁻²·nm⁻¹)')
    f=go.Figure(go.Scatter(x=x,y=y*x*1e-9/(H*C_LIGHT)/1e4,line=dict(color='#2478a5'),name='Flujo espectral'))
    f.add_vrect(x0=x[0],x1=min(s['cutoff'],x[-1]),fillcolor='#59d4bb',opacity=.15,line_width=0)
    chart(f,'Longitud de onda λ (nm)','Flujo de fotones (cm⁻²·s⁻¹·nm⁻¹)',300)
    components.html(energy_animation(s),height=310)
    st.caption('Animación temporal: 54 paquetes de igual energía repartidos según las fracciones calculadas; redondeo visual ≤ 1/54. No son fotones individuales ni tiempos microscópicos reales. Los porcentajes sí provienen de la integral.')
    with st.expander('Qué significan las ecuaciones y las unidades'):
        st.latex(r'E_{fotón}=hc/\lambda,\qquad N_\lambda=P_\lambda\lambda/(hc),\qquad J_{SC,max}=q\int^{\lambda_g}N_\lambda\,d\lambda')
        st.write('Un fotón es un paquete de luz. Eg es la energía mínima para crear un par electrón-hueco. Si sobra energía, el exceso se vuelve calor. Un hueco es la ausencia de un electrón en un enlace.')
        st.write('El Excel usa nm y W/m²/nm: λ se convierte a metros dentro de hc/λ, pero la integral conserva dλ en nm. Luego se divide por 10⁴ para pasar de m⁻² a cm⁻².')
        st.caption('Fuente: astmg173.xls, SMARTS2, columna Global tilt; Unidades 2 y 4, láminas 3–8.')

with tab2:
    if not all(enabled[:4]):
        st.warning('Escenario pedagógico: eliminar pérdidas fundamentales no representa una celda de silicio realizable. El porcentaje final es un contrafactual energético, no una eficiencia física predicha.')
    if enabled[6] and abs(p['eg']-EG_REF)>.03:
        st.info('Óptica: se mantienen los datos medidos de silicio a 300 K al explorar Eg. Esto es una sensibilidad hipotética, no una predicción para otro material.')
    f=go.Figure(go.Waterfall(x=['Incidente']+[str(i+1) for i in range(8)]+['Útil'],
       measure=['absolute']+['relative']*8+['total'],y=[100]+(-cas['losses']).tolist()+[0],
       text=[f'{v:.1f}%' for v in [100]+(-cas['losses']).tolist()+[cas['eta']]],textposition='outside',
       decreasing=dict(marker=dict(color='#c48a51')),increasing=dict(marker=dict(color='#258fa7')),
       totals=dict(marker=dict(color='#179a80'))))
    chart(f,'Mecanismo (numeración de la Unidad 4)','Potencia / potencia incidente (%)',450)
    a,b,c=st.columns(3)
    a.metric('Energía útil final',f'{cas["eta"]:.2f} %')
    b.metric('Referencia ideal del curso','29,3 %')
    c.metric('Residuo del balance',f'{cas["residual"]:.2e} pp')
    st.dataframe(pd.DataFrame({'Mecanismo':LOSS_NAMES,'Activado':enabled,
       'Pérdida (puntos porcentuales)':cas['losses'],'Energía restante (%)':cas['levels'][1:]}),hide_index=True,use_container_width=True)
    st.caption('A menos de 26,85 °C, el peldaño térmico puede ser una ganancia. La referencia ideal es 300 K; STC comercial es 25 °C. El botón del límite ideal desactiva pérdidas adicionales y temperatura.')
    with st.expander('Modelo, ecuaciones y límites de interpretación'):
        st.latex(r'G=J_L/(qW)=C\Delta n^3+B\Delta n^2+\Delta n/\tau_{SRH}+(S_f+S_r)\Delta n/W')
        st.latex(r'V_{OC}=2(k_BT/q)\ln(\Delta n/n_i),\qquad \eta=J_{SC}V_{OC}FF/P_{in}')
        st.write('Auger permanece siempre. Los tres términos adicionales son conmutables. Se supone alta inyección uniforme y n≈p≈Δn; este problema no asigna dopaje. La pérdida de colección se aproxima por (L/W)tanh(W/L), con L=√(Dτef).')
        st.caption('Para mantener el equilibrio al explorar Eg pequeño, el código conserva el fondo intrínseco: n=p=ni+Δn y U=(Cn+B)(n²−ni²)+Δn/τ+(Sf+Sr)Δn/W. En alta inyección recupera la ecuación mostrada.')
        st.latex(r'J=J_L-J_0[\exp((V+R_sJ)/V_T)-1]-(V+R_sJ)/R_p')
        st.write('La curva usa un diodo n=1 cuyo J0 se deduce del Voc calculado. Sigue la aproximación del curso para FF; no reproduce una curva Auger exacta en cada voltaje. RsJ se conserva mediante u=V+RsJ. Se maximiza VJ numéricamente.')
        st.write('La cascada aplica pérdidas espectrales, Voc/Eg, FF y cocientes entre potencias de escenarios sucesivos. Así no suma dos veces la misma pérdida; cambiar el orden cambiaría su atribución, no el dispositivo final cuando todos los mecanismos están activos.')
        st.write('Óptica: absorción 1−exp(−α·W·camino), α=4πk/λ. Reflectancia y sombra son entradas; k es medido. El camino es una aproximación efectiva, no un cálculo angular de atrapamiento.')
        st.markdown(f'[Green (2008), datos ópticos a 300 K, 250–1450 nm]({GREEN_URL}). Fuera de ese intervalo se impone absorción cero. La tabla original se entrega junto al código.')
    with st.expander('Curva eléctrica del escenario físico'):
        d=cas['physical']; f=make_subplots(rows=1,cols=2)
        f.add_trace(go.Scatter(x=d['v'],y=d['j']*1000,name='J-V'),1,1)
        f.add_trace(go.Scatter(x=d['v'],y=d['v']*d['j']*1000,name='P-V'),1,2)
        f.update_xaxes(title_text='Voltaje (V)');f.update_yaxes(title_text='J (mA/cm²)',row=1,col=1)
        f.update_yaxes(title_text='P (mW/cm²)',row=1,col=2);chart(f)
        st.caption(f'Punto de máxima potencia: {d["vmp"]:.3f} V, {d["imp"]*1000:.2f} mA/cm². Si se desactivan pérdidas fundamentales, esta curva sigue siendo la del dispositivo físico, no del contrafactual.')

with tab3:
    st.subheader('Más temperatura: algo más de corriente, menos voltaje')
    st.caption(f'Silicio · Inicio asignado: 35 °C · Punto seleccionado: {p["temp"]:.0f} °C · Barrido completo: 15–75 °C. Se comparten Rs, Rp, óptica y recombinación con la cascada.')
    thermal=thermal_curve(p)
    current=device(EG_REF,p,enabled[5],enabled[6],enabled[4],p['temp'])
    cols=st.columns(4)
    for c,k,label,scale,unit in zip(cols,['jsc','voc','ff','eta'],['Jsc','Voc','FF','Eficiencia'],[1000,1,1,1],['mA/cm²','V','','%']):
        c.metric(label,f'{current[k]*scale:.3f} {unit}')
    f=make_subplots(rows=2,cols=2,subplot_titles=['Corriente','Voltaje','Factor de forma','Eficiencia'])
    for i,(key,unit,scale) in enumerate([('jsc','Jsc (mA/cm²)',1000),('voc','Voc (V)',1),('ff','FF (1)',1),('eta','η (%)',1)]):
        r=i//2+1;c=i%2+1
        f.add_trace(go.Scatter(x=thermal['T (°C)'],y=thermal[key]*scale,name=unit,line=dict(color=['#238aa0','#e7a04a','#6f76b5','#179a80'][i])),r,c)
        f.add_vline(x=p['temp'],line_dash='dot',row=r,col=c)
        f.update_xaxes(title_text='T (°C)',row=r,col=c);f.update_yaxes(title_text=unit,row=r,col=c)
    chart(f,height=650)
    st.latex(r'E_g(T)=1.206-0.000273T\;[eV],\quad J_0(T)=J_0(300)(T/300)^3e^{(1.2/k_B)(1/300-1/T)}')
    st.caption('T en K. La ley Eg(T) calcula la corriente espectral. La energía de activación 1,2 eV de J0 sigue la lámina 42 y no debe sustituirse nuevamente por Eg(T). Óptica, colección y resistencias se mantienen constantes durante el barrido.')
    st.markdown('**Comprobación de la pendiente de voltaje**')
    h=.01;numeric=(thermal_reference(T_REF+h)-thermal_reference(T_REF-h))/(2*h)*1000
    ana=analytical_slope(.6)*1000
    st.write(f'Caso de la lámina 42 (JL constante, Voc=0,6 V a 300 K): numérico **{numeric:.4f} mV/°C**, analítico **{ana:.4f} mV/°C**.')
    st.latex(r'\frac{dV_{OC}}{dT}=-\frac{V_g-V_{OC}+\gamma k_BT/q}{T}')
    # Comprobación adicional para la curva visible, incluyendo JL(T) y shunt.
    lo=device(EG_REF,p,enabled[5],enabled[6],enabled[4],p['temp']-h)
    hi=device(EG_REF,p,enabled[5],enabled[6],enabled[4],p['temp']+h)
    slope=(hi['voc']-lo['voc'])/(2*h)
    t=current['t'];v=current['voc'];vt=K_EV*t;rp=p['rp'] if enabled[4] else np.inf
    jl_prime=(hi['jl']-lo['jl'])/(2*h);j0=current['j0']
    j0_prime=j0*(GAMMA/t+VG_THERMAL/(K_EV*t*t))
    ex=np.exp(v/vt)
    exact=(jl_prime-j0_prime*(ex-1)+j0*ex*v/(K_EV*t*t))/(j0*ex/vt+1/rp)
    st.write(f'Curva visible a {p["temp"]:.0f} °C: derivada numérica **{slope*1000:.4f}**, analítica del diodo completo **{exact*1000:.4f} mV/°C**. Esta última incluye la variación de JL y la resistencia paralela.')
    vv=np.linspace(.45,.85,81)
    f=go.Figure(go.Scatter(x=vv,y=analytical_slope(vv)*1000,line=dict(color='#2478a5')))
    chart(f,'Voc de referencia a 300 K (V)','dVoc/dT (mV/°C)',300)
    st.caption('Reproduce la lámina 44: al aumentar Voc, el coeficiente se acerca a cero y su magnitud disminuye.')
    st.markdown('**Confrontación con un módulo comercial**')
    comp,base=comparison(p)
    compare=pd.DataFrame({'Magnitud':['Voc','Isc / Jsc','Pmax'],
        'Celda simulada (%/°C)':[comp['voc'],comp['jsc'],comp['pmax']],
        'Módulo Jinko (%/°C)':[MODULE['beta_voc'],MODULE['alpha_isc'],MODULE['gamma_pmax']]})
    st.dataframe(compare,hide_index=True,use_container_width=True)
    st.markdown(f'[{MODULE["model"]} · ficha oficial, 2024, p. 2]({MODULE_URL})')
    st.write('Se comparan pendientes relativas locales a 25 °C. El módulo tiene 156 medias celdas (78×2); usamos 78 celdas serie equivalentes con ramas en paralelo. El voltaje se suma en serie: Voc,módulo≈Ns·Voc,celda. Los coeficientes relativos %/°C son comparables; los absolutos V/°C no lo son directamente.')
    st.write(f'Ficha: Voc={MODULE["voc"]} V, Isc={MODULE["isc"]} A, Pmax={MODULE["pmax"]:.0f} W. Equivalente: Voc por celda≈{MODULE["voc"]/MODULE["n_series"]:.3f} V. El coeficiente absoluto del módulo es {MODULE["voc"]*MODULE["beta_voc"]/100:.4f} V/°C.')
    st.info('La coincidencia exacta no se espera: el modelo es una celda genérica con aproximaciones de alta inyección y parámetros exploratorios; el módulo comercial usa TOPCon, pasivación y una arquitectura óptica diferente. No ajustamos sus coeficientes para forzar la comparación. La respuesta espectral ideal también limita la predicción de Isc(T).')
    st.download_button('Descargar barrido térmico (CSV)',thermal.to_csv(index=False).encode('utf-8-sig'),'barrido_termico.csv','text/csv')

with tab4:
    st.subheader('Verificaciones automáticas y reproducibles')
    st.caption(f'Se ejecutan al cargar y al cambiar parámetros: están listas al abrir esta pestaña. V1–V4 y V6 usan las condiciones canónicas explícitas del PDF; V5 y V7 usan el escenario actual. La semilla {SEED} fija el inicio térmico en {T_DEFAULT_C:.0f} °C.')
    checks=validations(p)
    n=sum(checks['Veredicto'].str.startswith('APROBADO'))
    if n == len(checks):
        st.success(f'{n}/{len(checks)} comprobaciones aprobadas (V2 y V4 tienen dos resultados cada una).')
    else:
        st.warning(f'{n}/{len(checks)} aprobadas: revisar los rechazos.')
    st.dataframe(checks,hide_index=True,use_container_width=True)
    st.caption('V7 evalúa que la comparación esté reportada, citada y discutida; el PDF no exige una tolerancia numérica. Su diferencia no se oculta. El error porcentual usa el valor absoluto de la referencia.')
    st.download_button('Descargar validaciones (CSV)',checks.to_csv(index=False).encode('utf-8-sig'),'validaciones.csv','text/csv')
    st.markdown('**Arquitectura y uso de IA**')
    st.write('app.py coordina controles y pestañas; modelo.py calcula toda la física; constantes.py centraliza constantes y fuentes; animacion.py transforma el balance calculado en movimiento; data/ contiene los datos originales. La interfaz comparte st.session_state; los datos inmutables se almacenan en caché.')
    st.write('ChatGPT/Codex se utilizó para estructurar y programar la solución, contrastar unidades y preparar verificaciones. Los supuestos y las diferencias con el dispositivo real se explicitan. No se utiliza solcore.')
    libraries=pd.DataFrame([
      ['NumPy','Álgebra de arreglos y exponenciales','No incorpora modelo físico; precisión flotante','Vectores → vectores'],
      ['SciPy','Trapecios, Brent y máximo de potencia','Función continua y raíz acotada; malla espectral finita','Funciones/datos → integral, raíz, máximo'],
      ['pandas + xlrd','Lectura del XLS y tablas','Sin modelo físico; columna/unidades elegidas explícitamente','XLS → datos numéricos'],
      ['Plotly','Gráficos interactivos','No resuelve física; representa resultados','Arreglos → gráficos'],
      ['Streamlit','Interfaz, pestañas y estado','Reejecución al modificar controles','Controles → parámetros compartidos']],
      columns=['Librería','Función/modelo','Supuestos','Entradas → salidas'])
    st.dataframe(libraries,hide_index=True,use_container_width=True)
    st.markdown('**Fuentes**')
    st.write('Felipe A. Larraín, Celdas Solares Fotovoltaicas, UAI, 2026-2: Proyecto 1, problema 2.3 y anexos A–B; Unidad 2, láminas 25–39; Unidad 3, láminas 18–26; Unidad 4, láminas 3–44.')
    st.markdown(f'• [Ficha JinkoSolar]({MODULE_URL})\n• [Green (2008), DOI 10.1016/j.solmat.2008.06.009]({GREEN_URL})\n• [Streamlit](https://docs.streamlit.io/) · [Stlite](https://github.com/whitphx/stlite)\n• [SciPy](https://docs.scipy.org/doc/scipy/) · [NumPy](https://numpy.org/doc/) · [pandas](https://pandas.pydata.org/docs/) · [Plotly](https://plotly.com/python/)')
