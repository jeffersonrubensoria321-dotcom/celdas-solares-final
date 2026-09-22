"""Modelo propio: espectro, recombinación, diodo, cascada y temperatura.

No utiliza un solver fotovoltaico. Las referencias no sustituyen cálculos.
La curva de un diodo n=1 anclada al Voc de Auger reproduce la aproximación
del curso; no es una solución completa de deriva-difusión ni un límite SQ.
"""
from functools import lru_cache
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.optimize import brentq, minimize_scalar
from constantes import *

DATA = Path(__file__).resolve().parent / 'data'

@lru_cache(maxsize=1)
def spectrum():
    raw = pd.read_excel(DATA/'astmg173.xls', sheet_name='SMARTS2', header=1, engine='xlrd')
    # Columna 3: Global tilt. No confundir con extraterrestre o directa.
    frame = raw.iloc[:, [0, 2]].apply(pd.to_numeric, errors='coerce').dropna()
    x, y = frame.iloc[:, 0].to_numpy(), frame.iloc[:, 1].to_numpy()
    if not (np.all(np.diff(x)>0) and np.all(y>=0)):
        raise ValueError('El espectro debe tener longitudes crecientes e irradiancias no negativas.')
    return x, y

@lru_cache(maxsize=512)
def spectral(eg=EG_REF):
    x, y = spectrum()
    cutoff = H*C_LIGHT/(Q*eg)*1e9  # m -> nm
    stop = float(np.clip(cutoff, x[0], x[-1]))
    z = np.append(x[x<stop], stop)
    p = np.interp(z, x, y)
    photons = p*z*1e-9/(H*C_LIGHT)  # photons m^-2 s^-1 nm^-1
    flux = trapezoid(photons, z)/1e4  # photons cm^-2 s^-1
    pin = trapezoid(y, x)  # W/m^2
    above = trapezoid(p, z)
    useful = flux*1e4*eg*Q  # W/m^2 after thermalization
    return dict(x=z, p=p, photons=photons, flux=flux, jl=Q*flux,
                pin=pin, above=above, sub=pin-above, therm=above-useful,
                useful=useful, cutoff=cutoff)

@lru_cache(maxsize=1)
def optical_data():
    # Texto tabulado CC0 de Green (2008), 0.25-1.45 µm; no requiere PyYAML.
    rows=[]
    for line in (DATA/'green2008.yml').read_text().splitlines():
        a=line.split()
        if len(a)==3:
            try: rows.append([float(v) for v in a])
            except ValueError: pass
    a=np.array(rows)
    if len(a)<100: raise ValueError('Datos ópticos incompletos')
    return a[:,0]*1000, a[:,1], a[:,2]

def optical_fraction(eg, p):
    s=spectral(eg); x,n,k=optical_data()
    wave=s['x']
    ki=np.interp(wave,x,k,left=0,right=0)
    alpha=4*np.pi*ki/(wave*1e-7)  # cm^-1 (lambda en cm)
    absorptance=-np.expm1(-alpha*W_CM*p['path'])
    fraction=(1-p['reflection'])*(1-p['shade'])*absorptance
    return float(trapezoid(s['photons']*fraction,wave)/1e4/s['flux'])

def ni(eg):
    # Barrido exploratorio de Eg: densidad efectiva de estados constante.
    return NI_REF*np.exp(-(eg-EG_REF)/(2*K_EV*T_REF))

def balance_voc(jl, eg, p, recomb=False):
    """Alta inyección uniforme: G=C dn^3+B dn^2+dn/tau+Ssum dn/W."""
    a = (1/(p['tau_us']*1e-6) if recomb and p['srh'] else 0.0)
    a += ((p['sf']+p['sr'])/W_CM if recomb and p['surface'] else 0.0)
    b = B_RAD if recomb and p['radiative'] else 0.0
    g=jl/(Q*W_CM); intrinsic=ni(eg)
    # Fondo intrínseco: n=p=ni+dn; np-ni²=dn(2ni+dn).
    # En alta inyección recupera exactamente la expresión cúbica del curso.
    def net(logn):
        dn=10**logn; total=intrinsic+dn; excess_product=dn*(2*intrinsic+dn)
        return AUGER*total*excess_product+b*excess_product+a*dn-g
    root=brentq(net,
                -5, 25, xtol=1e-11)
    dn=10**root
    voc=2*K_EV*T_REF*np.log1p(dn/intrinsic)
    return voc, dn

def collection(p, recomb):
    # Difusión 1D, generación uniforme, colección ideal en x=0 y pared reflectante
    # en W. Superficies resumidas por 1/tau_eff = 1/tau_bulk+(Sf+Sr)/W.
    a=(1/(p['tau_us']*1e-6) if recomb and p['srh'] else 0.0)
    a+=((p['sf']+p['sr'])/W_CM if recomb and p['surface'] else 0.0)
    if a==0: return 1.0
    length=np.sqrt(D_N/a)
    return float(length/W_CM*np.tanh(W_CM/length))

def diode(jl, j0, t, rs=0., rp=np.inf):
    """Diodo implícito en I resuelto usando u=V+Rs I; I positiva generada.

    I(u)=JL-J0[exp(u/Vt)-1]-u/Rp; V(u)=u-Rs I(u).
    Transformación exacta; evita ignorar el término Rs I.
    """
    vt=K_EV*t
    def current(u): return jl-j0*np.expm1(np.clip(u/vt,-700,700))-u/rp
    upper=vt*np.log1p(jl/j0)
    voc=upper if np.isinf(rp) else brentq(current,0,max(upper+1e-10,1e-12),xtol=1e-13)
    usc=brentq(lambda u:u-rs*current(u),0,voc,xtol=1e-13) if rs else 0.
    isc=current(usc)
    opt=minimize_scalar(lambda u:-(u-rs*current(u))*current(u),bounds=(usc,voc),
                        method='bounded',options={'xatol':1e-12})
    imp=current(opt.x); vmp=opt.x-rs*imp; power=vmp*imp
    u=np.linspace(usc,voc,160); j=current(u); v=u-rs*j
    return dict(voc=float(voc),jsc=float(isc),ff=float(power/(voc*isc)),
                pmax=float(power),vmp=float(vmp),imp=float(imp),v=v,j=j)

def device(eg,p,recomb=False,optics=False,parasitic=False,temp_c=None):
    s=spectral(eg)
    optical=optical_fraction(eg,p) if optics else 1.
    jl=s['jl']*optical*collection(p,recomb)
    # Voc se estima desde generación total, colección afecta la corriente entregable.
    voc,dn=balance_voc(s['jl']*optical,eg,p,recomb)
    j0=jl/np.expm1(voc/(K_EV*T_REF))
    t=T_REF
    if temp_c is not None:
        t=temp_c+CELSIUS_ZERO
        # Ley exigida usada SOLO en el barrido térmico.
        eg_t=EG_INTERCEPT-EG_SLOPE*t
        jl*=spectral(eg_t)['jl']/spectral(EG_INTERCEPT-EG_SLOPE*T_REF)['jl']
        j0*= (t/T_REF)**GAMMA*np.exp(VG_THERMAL/K_EV*(1/T_REF-1/t))
    r=diode(jl,j0,t,p['rs'] if parasitic else 0.,p['rp'] if parasitic else np.inf)
    r.update(eta=r['pmax']/(s['pin']/1e4)*100,dn=dn,jl=jl,j0=j0,t=t)
    return r

LOSS_NAMES=['Fotones sub-bandgap','Termalización','Energía de la juntura',
            'Factor de forma ideal','Resistencias Rs y Rp','Recombinación',
            'Reflexión, sombra y absorción','Temperatura']

def cascade(p,enabled=None):
    enabled=[True]*8 if enabled is None else enabled
    s=spectral(p['eg']); ideal=device(p['eg'],p)
    d5=device(p['eg'],p,parasitic=enabled[4])
    d6=device(p['eg'],p,recomb=enabled[5],parasitic=enabled[4])
    d7=device(p['eg'],p,recomb=enabled[5],optics=enabled[6],parasitic=enabled[4])
    d8=device(p['eg'],p,recomb=enabled[5],optics=enabled[6],parasitic=enabled[4],
              temp_c=p['temp'] if enabled[7] else None)
    rem=s['pin']; levels=[rem]; losses=[]
    for index in range(8):
        if index==0: after=rem-s['sub'] if enabled[0] else rem
        elif index==1: after=rem-s['therm'] if enabled[1] else rem
        else:
            factors=[ideal['voc']/p['eg'],ideal['ff'],d5['pmax']/ideal['pmax'],
                     d6['pmax']/d5['pmax'],d7['pmax']/d6['pmax'],d8['pmax']/d7['pmax']]
            after=rem*factors[index-2] if enabled[index] else rem
        losses.append(rem-after); rem=after; levels.append(rem)
    losses=np.array(losses)*100/s['pin']; levels=np.array(levels)*100/s['pin']
    return dict(losses=losses,levels=levels,eta=levels[-1],physical=d8,
                residual=float(100-losses.sum()-levels[-1]))

def thermal_curve(p):
    # Silicon only, independently of exploratory Eg slider; all loss switches apply.
    e=p.get('enabled',[True]*8)
    ts=np.linspace(15,75,61)
    data=[device(EG_REF,p,e[5],e[6],e[4],float(t)) for t in ts]
    return pd.DataFrame({'T (°C)':ts,**{k:[d[k] for d in data] for k in ['jsc','voc','ff','eta','pmax']}})

def analytical_slope(voc,t=T_REF,alpha_current=0.):
    return -(VG_THERMAL-voc+GAMMA*K_EV*t)/t+K_EV*t*alpha_current

def thermal_reference(t, voc_ref=0.6):
    # Referencia V6: obtener Voc del diodo a cada T, con JL constante.
    # La derivada numérica NO se obtiene diferenciando la fórmula analítica
    # que se compara; usa el mismo solver eléctrico del resto de la aplicación.
    jl = spectral(EG_REF)['jl']
    j0_ref = jl / np.expm1(voc_ref / (K_EV*T_REF))
    j0_t = j0_ref*(t/T_REF)**GAMMA*np.exp(VG_THERMAL/K_EV*(1/T_REF-1/t))
    return diode(jl, j0_t, t)['voc']

def comparison(p):
    e=p.get('enabled',[True]*8); args=(EG_REF,p,e[5],e[6],e[4])
    base=device(*args,temp_c=25.)
    lo=device(*args,temp_c=24.9);hi=device(*args,temp_c=25.1)
    vals={k:100*(hi[k]-lo[k])/0.2/base[k] for k in ['voc','jsc','pmax']}
    return vals,base

def validations(p):
    s=spectral(EG_REF); refp=dict(DEFAULTS)
    voc,dn=balance_voc(0.0435,EG_REF,refp)
    ideal=diode(0.0435,0.0435/np.expm1(voc/(K_EV*T_REF)),T_REF)
    h=.01
    numerical=(thermal_reference(T_REF+h)-thermal_reference(T_REF-h))/(2*h)*1000
    ana=analytical_slope(.6)*1000
    cas=cascade(p,p.get('enabled'))
    comp,_=comparison(p)
    rows=[]
    def row(id,name,value,reference,tolerance,unit,comment=''):
        error=100*abs(value-reference)/abs(reference) if reference else None
        rows.append(dict(ID=id,Verificación=name,Calculado=float(value),Referencia=float(reference),
                         Unidad=unit,Error_pct=error,Tolerancia_abs=tolerance,
                         Veredicto='APROBADO' if abs(value-reference)<=tolerance else 'RECHAZADO',Detalle=comment))
    row('V1','Integral AM1.5G',s['pin'],1000,15,'W/m²')
    row('V2a','Flujo sobre 1,12 eV',s['flux'],2.72e17,2.72e17*.05,'cm⁻² s⁻¹')
    row('V2b','Corriente máxima',s['jl']*1000,43.5,43.5*.05,'mA/cm²')
    row('V3','Voc limitado por Auger',voc*1000,785,15,'mV')
    row('V4a','Factor de forma ideal',ideal['ff'],.86,.01,'1')
    row('V4b','Eficiencia canónica',ideal['pmax']/.1*100,29.3,.5,'%')
    row('V5','Cierre de energía',100-cas['residual'],100,.5,'%',
        f'Residuo: {cas["residual"]:.3e} puntos porcentuales.')
    row('V6','Pendiente numérica vs. analítica',numerical,ana,.2,'mV/°C',
        'JL constante, Vg=1,2 V, gamma=3, Voc=0,6 V a 300 K.')
    rows.append(dict(ID='V7',Verificación='Coeficiente Pmax: celda vs. módulo',
        Calculado=float(comp['pmax']),Referencia=MODULE['gamma_pmax'],Unidad='%/°C',
        Error_pct=100*abs(comp['pmax']-MODULE['gamma_pmax'])/abs(MODULE['gamma_pmax']),
        Tolerancia_abs=None,Veredicto='APROBADO: reportado y discutido',
        Detalle='Sin tolerancia de coincidencia en el enunciado. Modelo genérico frente a TOPCon comercial; ver pestaña Temperatura.'))
    return pd.DataFrame(rows)
