import streamlit as st
import numpy as np
import pandas as pd
from astroquery.jplhorizons import Horizons
from datetime import datetime
from analytical_engine_8D import Manifold8DEngine

st.set_page_config(page_title="8D Manifold Auditor", layout="wide")
st.title("🌌 8D Manifold: NASA JPL Horizons Audit")

AU_TO_KM = 149597870.7
BODIES = [
    {'name': 'Sun',     'id': '10',  'gm': 132712440041.939},
    {'name': 'Mercury', 'id': '199', 'gm': 22031.868},
    {'name': 'Venus',   'id': '299', 'gm': 324858.592},
    {'name': 'Earth',   'id': '3',   'gm': 403503.235}, 
    {'name': 'Mars',    'id': '499', 'gm': 42828.375},
    {'name': 'Jupiter', 'id': '5',   'gm': 126712764.8},
    {'name': 'Saturn',  'id': '6',   'gm': 37940585.2},
    {'name': 'Uranus',  'id': '7',   'gm': 5794548.6},
    {'name': 'Neptune', 'id': '8',   'gm': 6836527.1}
]

with st.sidebar:
    start_dt = st.date_input("Start Date", datetime(2026, 3, 18))
    jump_days = st.slider("Jump (Days)", 1, 365, 365)
    run_audit = st.button("🚀 Run Audit")

if run_audit:
    jd0 = pd.Timestamp(start_dt).to_julian_date()
    jd1 = jd0 + jump_days
    
    r_init, v_init, r_truth = [], [], []
    for b in BODIES:
        q0 = Horizons(id=b['id'], location='@0', epochs=jd0).vectors()
        r_init.append([q0['x'][0], q0['y'][0], q0['z'][0]])
        v_init.append([q0['vx'][0], q0['vy'][0], q0['vz'][0]])
        q1 = Horizons(id=b['id'], location='@0', epochs=jd1).vectors()
        r_truth.append([q1['x'][0], q1['y'][0], q1['z'][0]])

    r_vecs = np.array(r_init) * AU_TO_KM
    v_vecs = np.array(v_init) * AU_TO_KM / 86400.0
    r_target = np.array(r_truth) * AU_TO_KM

    # Heliocentric Shift
    r_rel = r_vecs - r_vecs[0]; v_rel = v_vecs - v_vecs[0]
    r_truth_rel = r_target - r_target[0]

    engine = Manifold8DEngine(mu=BODIES[0]['gm'])
    results = []

    for i in range(1, len(BODIES)):
        # Interference Term chi [cite: 131, 147]
        m_int_sum = 0
        for j in range(1, len(BODIES)):
            if i == j: continue
            r_ij = np.linalg.norm(r_rel[j] - r_rel[i])
            m_int_sum += BODIES[j]['gm'] / max(1e-6, r_ij**3)

        pos_8d = engine.propagate(i, BODIES, r_rel, v_rel, 86400.0 * jump_days, {'M_int': m_int_sum * 10.0})
        
        error_km = np.linalg.norm(pos_8d - r_truth_rel[i])
        results.append({
            'Planet': BODIES[i]['name'],
            '8D Dist (AU)': np.linalg.norm(pos_8d) / AU_TO_KM,
            'NASA Dist (AU)': np.linalg.norm(r_truth_rel[i]) / AU_TO_KM,
            'Position Error (km)': error_km
        })

    st.table(pd.DataFrame(results))
    st.info(f"RMSE: {np.sqrt(np.mean([x['Position Error (km)']**2 for x in results])):,.2f} km")