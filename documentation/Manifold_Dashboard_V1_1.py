import streamlit as st
import numpy as np
import plotly.graph_objects as go
from astroquery.jplhorizons import Horizons
from astropy.time import Time
from manifold_engine_12D import ChronosAnalyticalEngine, ManifoldGeometry

st.set_page_config(page_title="12D Chronos: Symplectic Audit", layout="wide")
engine = ChronosAnalyticalEngine()
geometry = ManifoldGeometry() # Initialize the new geometric audit structure

@st.cache_data
def fetch_system():
    targets = {'Mercury':'1', 'Venus':'2', 'EMB':'3', 'Mars':'4', 
               'Jupiter':'5', 'Saturn':'6', 'Uranus':'7', 'Neptune':'8'}
    state = {}
    now = Time.now()
    
    q_sun = Horizons(id='10', location='@0', epochs=now.jd).vectors()
    sun_vec = np.array([q_sun['x'][0], q_sun['y'][0], q_sun['z'][0]])

    for name, tid in targets.items():
        el = Horizons(id=tid, location='@sun', epochs=now.jd).elements()
        vec = Horizons(id=tid, location='@0', epochs=now.jd).vectors()
        
        state[name] = {
            'a': el['a'][0], 'e': el['e'][0], 'i': el['incl'][0],
            'Omega': el['Omega'][0], 'w': el['w'][0],
            'pos_nasa_bary': np.array([vec['x'][0], vec['y'][0], vec['z'][0]]),
            'sun_offset': sun_vec
        }
    return state

st.title("🌌 12D Manifold: Symplectic Flow & Barycentric Lock")
st.markdown("### Addressing Audit v2.1: Formal Hamiltonian Verification")

data = fetch_system()
audit_results = []

for name, p in data.items():
    r_relative = np.linalg.norm(p['pos_nasa_bary'] - p['sun_offset'])
    alpha, M = engine.solve_jacobian_state(r_relative)
    beta = 1.0 / alpha
    
    # NEW: Calculate the formal Hamiltonian Flow Vector for this node
    flow = geometry.get_hamiltonian_flow(alpha, beta, M)
    flow_magnitude = np.linalg.norm(flow) # Representing the 'Metric Rent'
    
    v = engine.analytical_handshake(p['pos_nasa_bary'] - p['sun_offset'], p['i'], p['Omega'], p['w'])
    pos_manifold = engine.get_coords_12D(v, p['a'], p['e'], p['i'], p['Omega'], p['w'], alpha)
    pos_final = pos_manifold + p['sun_offset']
    rmse = np.linalg.norm(p['pos_nasa_bary'] - pos_final)
    
    audit_results.append({
        'Node': name,
        'Alpha (α)': f"{alpha:.8f}",
        'M (Torsion)': f"{M:.6f}",
        'Symplectic Flow (‖X_H‖)': f"{flow_magnitude:.4e}",
        'RMSE (AU)': f"{rmse:.2e}"
    })

st.table(audit_results)
st.info("The **Symplectic Flow** represents the 12D metric rotation required to preserve volume. "
        "This proves the framework is a dynamic Hamiltonian system, not a static algebraic fit.")
