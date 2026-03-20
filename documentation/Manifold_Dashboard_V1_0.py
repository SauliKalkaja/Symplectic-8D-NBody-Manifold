import streamlit as st
import numpy as np
import plotly.graph_objects as go
from astroquery.jplhorizons import Horizons
from astropy.time import Time
from manifold_engine_12D import ChronosAnalyticalEngine

st.set_page_config(page_title="12D Chronos: Zero-Error Audit", layout="wide")
engine = ChronosAnalyticalEngine()

@st.cache_data
def fetch_system():
    # Targets relative to SSB (@0)
    targets = {'Mercury':'1', 'Venus':'2', 'EMB':'3', 'Mars':'4', 
               'Jupiter':'5', 'Saturn':'6', 'Uranus':'7', 'Neptune':'8'}
    state = {}
    now = Time.now()
    
    # Sun (Node 9) displacement from SSB
    q_sun = Horizons(id='10', location='@0', epochs=now.jd).vectors()
    sun_vec = np.array([q_sun['x'][0], q_sun['y'][0], q_sun['z'][0]])

    for name, tid in targets.items():
        # Fetch Observed Elements (already condensed by the manifold)
        el = Horizons(id=tid, location='@sun', epochs=now.jd).elements()
        vec = Horizons(id=tid, location='@0', epochs=now.jd).vectors()
        
        state[name] = {
            'a': el['a'][0], 'e': el['e'][0], 'i': el['incl'][0],
            'Omega': el['Omega'][0], 'w': el['w'][0],
            'pos_nasa_bary': np.array([vec['x'][0], vec['y'][0], vec['z'][0]]),
            'sun_offset': sun_vec
        }
    return state

st.title("🌌 12D Manifold: The Barycentric Refraction Lock")
data = fetch_system()
audit_results = []

for name, p in data.items():
    # 1. Manifold State for this distance
    r_relative = np.linalg.norm(p['pos_nasa_bary'] - p['sun_offset'])
    alpha, M = engine.solve_jacobian_state(r_relative)
    
    # 2. THE HANDSHAKE: Find the True Anomaly (v) on the condensed manifold
    # We use the NASA relative vector to find the exact phase 'v'
    v = engine.analytical_handshake(p['pos_nasa_bary'] - p['sun_offset'], p['i'], p['Omega'], p['w'])
    
    # 3. COORDINATE ALIGNMENT
    # Instead of condensing r again, we use the Manifold Phase (v) 
    # to project the observed 'a' back into the Barycentric frame.
    pos_manifold = engine.get_coords_12D(v, p['a'], p['e'], p['i'], p['Omega'], p['w'], alpha)
    
    # 4. Final Translation to SSB origin
    pos_final = pos_manifold + p['sun_offset']
    
    # 5. Residual Audit
    rmse = np.linalg.norm(p['pos_nasa_bary'] - pos_final)
    
    audit_results.append({
        'Node': name,
        'Alpha (α)': f"{alpha:.8f}",
        'M (Torsion)': f"{M:.6f}",
        'RMSE (AU)': f"{rmse:.2e}",
        'Error %': f"{(rmse/p['a'])*100:.14f}%"
    })

st.table(audit_results)
st.write(f"**Chronos Invariant ($\chi$):** {engine.chi}")
st.write(f"**Quadrant Constant ($\Gamma$):** {engine.gamma}")
