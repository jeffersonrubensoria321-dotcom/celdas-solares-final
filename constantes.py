"""Constantes físicas, referencias y parámetros explícitos; unidades indicadas."""
Q = 1.602176634e-19  # C, SI exacto; https://physics.nist.gov/cgi-bin/cuu/Value?e
H = 6.62607015e-34  # J s, SI exacto; https://physics.nist.gov/cgi-bin/cuu/Value?h
C_LIGHT = 299792458.0  # m/s, SI exacto; https://physics.nist.gov/cgi-bin/cuu/Value?c
KB = 1.380649e-23  # J/K, SI exacto; https://physics.nist.gov/cgi-bin/cuu/Value?k
K_EV = KB / Q  # eV/K; derivado de las constantes SI anteriores
T_REF = 300.0  # K, caso canónico; Proyecto 1, anexo B
CELSIUS_ZERO = 273.15  # K, conversión SI
T_STC = 298.15  # K, ficha Jinko, condiciones STC
NI_REF = 1e10  # cm^-3 a 300 K; Proyecto 1, anexo B
EG_REF = 1.12  # eV, silicio canónico; Proyecto 1, anexo B
AUGER = 4e-31  # cm^6/s, c_n+c_p; Unidad 4, lámina 23
B_RAD = 4.73e-15  # cm^3/s, coeficiente radiativo; Proyecto 1, anexo B
W_CM = 100e-4  # cm = 100 micrómetros; problema 2.3
D_N = 31.0  # cm^2/s a 300 K; Proyecto 1, anexo B
EG_INTERCEPT = 1.206  # eV, extrapolación lineal; Unidad 4, lámina 38
EG_SLOPE = 0.000273  # eV/K; Unidad 4, lámina 38
VG_THERMAL = 1.2  # V, energía de activación / q; Unidad 4, láminas 40-42
GAMMA = 3.0  # adimensional; Unidad 4, lámina 42
FF_OFFSET = 0.72  # adimensional, aproximación FF0; Unidad 4, lámina 25
SEED = 1  # (4+5+6+2+0+4) mod 10; Proyecto 1, sección 1.1. Grupo de dos.
T_DEFAULT_C = 35.0  # °C; Proyecto 1, anexo A, fila S=1 (único parámetro asignado a 2.3)
# Los siguientes son escenarios exploratorios, NO parámetros asignados a 2.3.
DEFAULTS = dict(eg=EG_REF, temp=T_DEFAULT_C, tau_us=500.0, sf=10.0,
                sr=10.0, reflection=0.04, shade=0.03, path=2.0,
                rs=0.4, rp=3000.0, srh=True, surface=True, radiative=True)
MODULE_URL = 'https://jinkosolarcdn.shwebspace.com/uploads/JKM625-650N-78HL4-BDV-F9-EN.pdf'
# Fuente: JinkoSolar (2024), ficha F9-EN, página 2, modelo JKM640N-78HL4-BDV, STC frontal.
MODULE = dict(model='JinkoSolar JKM640N-78HL4-BDV', voc=57.34, isc=13.98,
              pmax=640.0, n_series=78, beta_voc=-0.25, alpha_isc=0.045,
              gamma_pmax=-0.29)  # V, A, W, celdas serie equivalentes; coeficientes en %/°C
GREEN_URL = 'https://refractiveindex.info/?shelf=main&book=Si&page=Green-2008'
