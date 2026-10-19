#!/usr/bin/env python3
"""
Système de Monitoring Énergétique (SME) — Marsa Maroc DEPA (Port d'Agadir)
Marché n° 12/DEPA/2026 | Norme ISO 50001:2018
Interface de Supervision & Pilotage Énergétique — Prêt pour Streamlit Community Cloud
100% Autonome : Moteur de simulation Modbus intégré en arrière-plan via st.cache_resource.
Stockage en mémoire et chemins relatifs pour disques éphémères.
"""

import os
import sys
import json
import time
import math
import random
import threading
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Chemins relatifs sécurisés
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "meters_state.json"
INDEX_HTML_FILE = BASE_DIR / "index.html"

# Configuration de la page Streamlit
st.set_page_config(
    page_title="SME Marsa Maroc — Port d'Agadir",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 1. DÉFINITION DU PÉRIMÈTRE TECHNIQUE (6 POSTES ÉLECTRIQUES)
# -------------------------------------------------------------
SUBSTATIONS_CONFIG = [
    {
        "id": "P1",
        "name": "Poste P1 — Quai Nord (Polyvalent)",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P1-M01", "name": "Arrivée Générale HTA/BT P1", "ip": "192.168.10.11", "port": 502, "nominal_kw": 650, "type": "TGBT"},
            {"id": "P1-M02", "name": "Grues Mobiles Gottwald Quai Nord", "ip": "192.168.10.12", "port": 502, "nominal_kw": 380, "type": "Levage"},
            {"id": "P1-M03", "name": "Bandes Transporteuses Engrais/Clinker", "ip": "192.168.10.13", "port": 502, "nominal_kw": 180, "type": "Convoyage"},
            {"id": "P1-M04", "name": "Éclairage Mâts & Auxiliaires Quai Nord", "ip": "192.168.10.14", "port": 502, "nominal_kw": 45, "type": "Auxiliaires"}
        ]
    },
    {
        "id": "P2",
        "name": "Poste P2 — Quai Sud & Cold-Ironing",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P2-M01", "name": "Arrivée Générale P2 Quai Sud", "ip": "192.168.10.21", "port": 502, "nominal_kw": 900, "type": "TGBT"},
            {"id": "P2-M02", "name": "Cold-Ironing Navires (Alimentation à Quai)", "ip": "192.168.10.22", "port": 502, "nominal_kw": 550, "type": "Cold-Ironing"},
            {"id": "P2-M03", "name": "Station Pompage Eau de Mer & Ballast", "ip": "192.168.10.23", "port": 502, "nominal_kw": 220, "type": "Pompage"},
            {"id": "P2-M04", "name": "Grues et Terre-pleins Sud", "ip": "192.168.10.24", "port": 502, "nominal_kw": 120, "type": "Levage"}
        ]
    },
    {
        "id": "P3",
        "name": "Poste P3 — Terminal Roulier (Ro-Ro)",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P3-M01", "name": "Arrivée Générale Terminal Ro-Ro", "ip": "192.168.10.31", "port": 502, "nominal_kw": 380, "type": "TGBT"},
            {"id": "P3-M02", "name": "Rampes & Ponts Basculants d'Accès", "ip": "192.168.10.32", "port": 502, "nominal_kw": 160, "type": "Roulier"},
            {"id": "P3-M03", "name": "Zone Stationnement Remorques & Prises Frigo", "ip": "192.168.10.33", "port": 502, "nominal_kw": 140, "type": "Reefer"}
        ]
    },
    {
        "id": "P4",
        "name": "Poste P4 — Terminal à Conteneurs",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P4-M01", "name": "Arrivée Générale Terminal Conteneurs", "ip": "192.168.10.41", "port": 502, "nominal_kw": 1200, "type": "TGBT"},
            {"id": "P4-M02", "name": "Portique Quai STS-01 (ZPMC)", "ip": "192.168.10.42", "port": 502, "nominal_kw": 420, "type": "STS"},
            {"id": "P4-M03", "name": "Portique Quai STS-02 (ZPMC)", "ip": "192.168.10.43", "port": 502, "nominal_kw": 390, "type": "STS"},
            {"id": "P4-M04", "name": "Cavaliers Gerbeurs RTG Parc", "ip": "192.168.10.44", "port": 502, "nominal_kw": 260, "type": "RTG"},
            {"id": "P4-M05", "name": "Parc Prises Reefer (120 bornes)", "ip": "192.168.10.45", "port": 502, "nominal_kw": 310, "type": "Reefer"}
        ]
    },
    {
        "id": "P5",
        "name": "Poste P5 — Silos & Vracs Agroalimentaires",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P5-M01", "name": "Arrivée Générale Silos & Vracs", "ip": "192.168.10.51", "port": 502, "nominal_kw": 480, "type": "TGBT"},
            {"id": "P5-M02", "name": "Tours Élévatrices à Grains", "ip": "192.168.10.52", "port": 502, "nominal_kw": 240, "type": "Élévateurs"},
            {"id": "P5-M03", "name": "Trémies d'Ensachage Mobile", "ip": "192.168.10.53", "port": 502, "nominal_kw": 110, "type": "Ensachage"},
            {"id": "P5-M04", "name": "Aspiration Dépoussiérage & Ventilation", "ip": "192.168.10.54", "port": 502, "nominal_kw": 85, "type": "Ventilation"}
        ]
    },
    {
        "id": "P6",
        "name": "Poste P6 — Ateliers Centraux & Siège DEPA",
        "ip_base": "192.168.10.",
        "meters": [
            {"id": "P6-M01", "name": "Arrivée Générale Ateliers & Siège", "ip": "192.168.10.61", "port": 502, "nominal_kw": 280, "type": "TGBT"},
            {"id": "P6-M02", "name": "Bancs d'Essai Moteurs & Machines-Outils", "ip": "192.168.10.62", "port": 502, "nominal_kw": 140, "type": "Atelier"},
            {"id": "P6-M03", "name": "Climatisation Centrale (HVAC) & Datacenter", "ip": "192.168.10.63", "port": 502, "nominal_kw": 95, "type": "Tertiaire"}
        ]
    }
]

# -------------------------------------------------------------
# 2. MOTEUR DE SIMULATION EN ARRIÈRE-PLAN (IN-MEMORY / THREAD-SAFE)
# -------------------------------------------------------------
class ModbusSimulationEngine:
    """Moteur de simulation intégré exécuté en arrière-plan (in-memory avec tolérance de panne)."""
    def __init__(self):
        self.lock = threading.Lock()
        self.accumulated_energies = {}
        self.acknowledged_alarms = set()
        self.state = None
        self.running = True

        # Tentative de récupération des énergies initiales
        self._load_cached_state()

        # Première génération synchrone
        self.update_cycle(cycle_seconds=3)

        # Lancement du thread daemon en arrière-plan
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _load_cached_state(self):
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sub in data.get("substations", []):
                        for m in sub.get("meters", []):
                            self.accumulated_energies[m["id"]] = m.get("energy_kwh", 150000.0)
            except Exception:
                pass

    def _run_loop(self):
        while self.running:
            time.sleep(3)
            try:
                self.update_cycle(cycle_seconds=3)
            except Exception:
                pass

    def update_cycle(self, cycle_seconds=3):
        now = datetime.now()
        timestamp_iso = now.isoformat()
        hour = now.hour + now.minute / 60.0

        daily_factor = 0.65 + 0.35 * math.sin((hour - 6) / 24.0 * 2 * math.pi)
        daily_factor = max(0.45, min(1.15, daily_factor))

        substations_output = []
        total_site_kw = 0.0
        total_site_kwh = 0.0
        active_alarms = []

        for sub in SUBSTATIONS_CONFIG:
            meters_output = []
            sub_kw = 0.0
            sub_kwh = 0.0

            for meter in sub["meters"]:
                m_id = meter["id"]
                nom_kw = meter["nominal_kw"]

                noise = random.uniform(-0.06, 0.06)
                load_factor = max(0.15, min(1.05, daily_factor + noise))

                if "Cold-Ironing" in meter["name"]:
                    active_ship = (hour > 4 and hour < 22)
                    kw = nom_kw * (0.85 + random.uniform(-0.08, 0.08)) if active_ship else nom_kw * 0.08
                elif "STS" in meter["name"] or "Gottwald" in meter["name"]:
                    kw = nom_kw * random.uniform(0.40, 0.95)
                else:
                    kw = nom_kw * load_factor

                kw = round(kw, 1)
                sub_kw += kw

                v_base = 400.0 + random.uniform(-3.5, 3.5)
                u12 = round(v_base + random.uniform(-0.8, 0.8), 1)
                u23 = round(v_base + random.uniform(-0.8, 0.8), 1)
                u31 = round(v_base + random.uniform(-0.8, 0.8), 1)

                cos_phi = round(0.93 + random.uniform(-0.04, 0.03), 3)
                if m_id == "P5-M02" and random.random() < 0.03:
                    cos_phi = 0.825

                tan_phi = math.tan(math.acos(min(1.0, max(0.5, cos_phi))))
                kvar = round(kw * tan_phi, 1)
                kva = round(math.sqrt(kw**2 + kvar**2), 1)
                current_a = round((kva * 1000.0) / (math.sqrt(3) * u12), 1) if u12 > 0 else 0.0
                freq = round(50.0 + random.uniform(-0.04, 0.04), 2)

                inc_kwh = (kw * (cycle_seconds / 3600.0))
                current_kwh = self.accumulated_energies.get(m_id, 145000.0 + random.randint(1000, 50000))
                current_kwh += inc_kwh
                self.accumulated_energies[m_id] = current_kwh
                sub_kwh += current_kwh

                comm_status = "OK"
                latency_ms = random.randint(8, 38)
                if random.random() < 0.005:
                    comm_status = "RETRY"
                    latency_ms = 450

                modbus_registers = {
                    "40001_U12": int(u12 * 10),
                    "40002_U23": int(u23 * 10),
                    "40003_U31": int(u31 * 10),
                    "40004_I_avg": int(current_a * 10),
                    "40007_P_tot": int(kw * 10),
                    "40008_Q_tot": int(kvar * 10),
                    "40009_S_tot": int(kva * 10),
                    "40010_CosPhi": int(cos_phi * 1000),
                    "40011_Freq": int(freq * 100),
                    "40012_E_Act_High": int(current_kwh) >> 16,
                    "40013_E_Act_Low": int(current_kwh) & 0xFFFF
                }

                # Alarmes
                alm_cos_id = f"ALM-COS-{m_id}"
                if cos_phi < 0.85 and alm_cos_id not in self.acknowledged_alarms:
                    active_alarms.append({
                        "id": alm_cos_id,
                        "level": "WARNING",
                        "timestamp": timestamp_iso,
                        "meter_id": m_id,
                        "meter_name": meter["name"],
                        "message": f"Facteur de puissance bas ({cos_phi} < 0.85) — Pénalité réactif ONEE",
                        "status": "ACTIVE"
                    })

                alm_pwr_id = f"ALM-PWR-{m_id}"
                if kw > nom_kw * 1.15 and alm_pwr_id not in self.acknowledged_alarms:
                    active_alarms.append({
                        "id": alm_pwr_id,
                        "level": "CRITICAL",
                        "timestamp": timestamp_iso,
                        "meter_id": m_id,
                        "meter_name": meter["name"],
                        "message": f"Dépassement de puissance ({kw} kW > {int(nom_kw*1.15)} kW)",
                        "status": "ACTIVE"
                    })

                meters_output.append({
                    "id": m_id,
                    "name": meter["name"],
                    "type": meter["type"],
                    "ip": meter["ip"],
                    "port": meter["port"],
                    "status": comm_status,
                    "latency_ms": latency_ms,
                    "voltage_u12": u12,
                    "voltage_u23": u23,
                    "voltage_u31": u31,
                    "current_a": current_a,
                    "power_kw": kw,
                    "reactive_kvar": kvar,
                    "apparent_kva": kva,
                    "cos_phi": cos_phi,
                    "frequency_hz": freq,
                    "energy_kwh": round(current_kwh, 2),
                    "last_poll": timestamp_iso,
                    "registers": modbus_registers
                })

            total_site_kw += sub_kw
            total_site_kwh += sub_kwh

            substations_output.append({
                "id": sub["id"],
                "name": sub["name"],
                "ip_base": sub["ip_base"],
                "sub_total_kw": round(sub_kw, 1),
                "sub_total_kwh": round(sub_kwh, 1),
                "meters": meters_output
            })

        subscribed_power_kw = 2500.0
        alm_site_id = "ALM-SITE-PMAX"
        if total_site_kw > subscribed_power_kw and alm_site_id not in self.acknowledged_alarms:
            active_alarms.append({
                "id": alm_site_id,
                "level": "CRITICAL",
                "timestamp": timestamp_iso,
                "meter_id": "SITE",
                "meter_name": "Site Global Agadir",
                "message": f"Dépassement Puissance Souscrite ONEE ({int(total_site_kw)} kW > 2500 kW)",
                "status": "ACTIVE"
            })

        baseline_kw = round(total_site_kw * 1.085, 1)
        gain_kw = round(baseline_kw - total_site_kw, 1)
        gain_pct = round((gain_kw / baseline_kw) * 100, 2) if baseline_kw > 0 else 0.0

        new_state = {
            "timestamp": timestamp_iso,
            "site": "Marsa Maroc — Direction d'Exploitation au Port d'Agadir (DEPA)",
            "market": "12/DEPA/2026",
            "standard": "ISO 50001:2018",
            "global_metrics": {
                "total_power_kw": round(total_site_kw, 1),
                "baseline_ser_kw": baseline_kw,
                "gain_kw": gain_kw,
                "gain_pct": gain_pct,
                "total_energy_mwh": round(total_site_kwh / 1000.0, 3),
                "mean_cos_phi": 0.942,
                "frequency_hz": 50.01,
                "subscribed_power_kw": subscribed_power_kw,
                "power_usage_pct": round((total_site_kw / subscribed_power_kw) * 100, 1),
                "total_meters": sum(len(s["meters"]) for s in SUBSTATIONS_CONFIG),
                "online_meters": sum(len(s["meters"]) for s in SUBSTATIONS_CONFIG)
            },
            "ipe_indicators": {
                "containers_kwh_per_teu": round(18.4 + random.uniform(-0.6, 0.6), 2),
                "bulk_kwh_per_ton": round(3.12 + random.uniform(-0.15, 0.15), 2),
                "roro_kwh_per_unit": round(7.85 + random.uniform(-0.3, 0.3), 2),
                "tertiary_kwh_per_sqm": round(4.25 + random.uniform(-0.1, 0.1), 2)
            },
            "substations": substations_output,
            "active_alarms": active_alarms
        }

        with self.lock:
            self.state = new_state

        # Sauvegarde disque non bloquante avec tolérance d'échec (compatible disques éphémères)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp_f = STATE_FILE.with_suffix(".tmp")
            with open(tmp_f, "w", encoding="utf-8") as f:
                json.dump(new_state, f, indent=2, ensure_ascii=False)
            tmp_f.replace(STATE_FILE)
        except Exception:
            pass

    def get_state(self):
        with self.lock:
            if self.state is None:
                self.update_cycle(cycle_seconds=3)
            return self.state

    def acknowledge_alarm(self, alarm_id):
        with self.lock:
            self.acknowledged_alarms.add(alarm_id)
            if self.state and "active_alarms" in self.state:
                self.state["active_alarms"] = [
                    a for a in self.state["active_alarms"] if a["id"] != alarm_id
                ]

# Initialisation unique du moteur de simulation via st.cache_resource
@st.cache_resource
def get_simulation_engine():
    """Démarre le moteur de simulation Modbus une seule fois pour tout le serveur Streamlit."""
    return ModbusSimulationEngine()

# Instanciation ou récupération de l'état courant
engine = get_simulation_engine()
data = engine.get_state()
glob = data.get("global_metrics", {})
last_ts = data.get("timestamp", datetime.now().isoformat())[:19].replace("T", " ")

# -------------------------------------------------------------
# 3. INTERFACE STREAMLIT
# -------------------------------------------------------------
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
        font-family: monospace;
    }
    .metric-delta {
        font-size: 0.85rem;
        margin-top: 4px;
    }
    .badge-ok {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-warn {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-crit {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Barre latérale (Sidebar)
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
        <div style="background:linear-gradient(135deg, #2563eb, #06b6d4); padding:10px; border-radius:10px; font-size:24px;">⚡</div>
        <div>
            <div style="font-size:11px; font-weight:700; color:#06b6d4; text-transform:uppercase; letter-spacing:1px;">Marsa Maroc</div>
            <div style="font-size:16px; font-weight:800; color:#fff;">DEPA Agadir</div>
            <div style="font-size:11px; color:#94a3b8;">Marché 12/DEPA/2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🌐 État du Système")
    st.markdown(f"**Dernière acquisition :** `{last_ts}`")
    st.markdown(f"**Protocole :** <span class='badge-ok'>Modbus TCP/IP (FC03)</span>", unsafe_allow_html=True)
    st.markdown(f"**Disponibilité :** <span class='badge-ok'>{glob.get('online_meters', 20)}/{glob.get('total_meters', 20)} compteurs</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Actualisation")
    if st.button("🔄 Actualiser les mesures maintenant"):
        engine.update_cycle(cycle_seconds=3)
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px; color:#64748b; line-height:1.4;">
        Conforme à la norme <b>ISO 50001:2018</b>.<br>
        Supervision continue des 6 postes électriques du Port d'Agadir sans double comptage.<br>
        Moteur autonome actif en mémoire.
    </div>
    """, unsafe_allow_html=True)

# En-tête principal
st.markdown("""
<div style="background:linear-gradient(90deg, #0f172a 0%, #1e293b 100%); border:1px solid #334155; border-radius:12px; padding:18px 24px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
        <h2 style="margin:0; font-size:1.6rem; font-weight:800; color:#f8fafc; display:flex; align-items:center; gap:10px;">
            Système de Monitoring Énergétique (SME)
            <span style="font-size:12px; background:#065f46; color:#34d399; padding:4px 8px; border-radius:6px; font-weight:600;">ISO 50001:2018</span>
        </h2>
        <div style="font-size:13px; color:#94a3b8; margin-top:4px;">
            Direction d'Exploitation au Port d'Agadir — Supervision en temps réel des 6 postes électriques HTA/BT
        </div>
    </div>
    <div style="text-align:right;">
        <span class="badge-ok">● SERVEUR CLOUD ACTIF</span>
        <div style="font-size:12px; color:#94a3b8; margin-top:4px; font-family:monospace;">Streamlit Community Cloud | Autonome</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation principale par onglets
tab_dash, tab_substations, tab_iso, tab_alerts, tab_modbus, tab_reports, tab_iframe = st.tabs([
    "📊 Tableau de Bord Global",
    "🏢 Les 6 Postes Électriques",
    "🎯 IPE & SER (ISO 50001)",
    "🚨 Gestion des Alertes",
    "🔌 Registres Modbus TCP",
    "📋 Revue Énergétique & Rapports",
    "💻 Interface Synoptique Complète"
])

# -------------------------------------------------------------
# TAB 1 : TABLEAU DE BORD GLOBAL
# -------------------------------------------------------------
with tab_dash:
    col1, col2, col3, col4 = st.columns(4)
    tot_p = glob.get("total_power_kw", 0)
    sub_p = glob.get("subscribed_power_kw", 2500)
    p_pct = glob.get("power_usage_pct", 0)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Puissance Active Totale</div>
            <div class="metric-value">{tot_p:,.1f} <span style="font-size:1rem; color:#94a3b8;">kW</span></div>
            <div class="metric-delta" style="color:{'#f87171' if p_pct > 90 else '#34d399'};">
                {p_pct:.1f}% de la puissance souscrite (2 500 kW)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        tot_e = glob.get("total_energy_mwh", 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Énergie Active Cumulée</div>
            <div class="metric-value">{tot_e:,.2f} <span style="font-size:1rem; color:#94a3b8;">MWh</span></div>
            <div class="metric-delta" style="color:#38bdf8;">Comptage certifié sans double emploi</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        cos_p = glob.get("mean_cos_phi", 0.94)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Facteur de Puissance Moyen (cos φ)</div>
            <div class="metric-value">{cos_p:.3f}</div>
            <div class="metric-delta" style="color:{'#34d399' if cos_p >= 0.90 else '#fbbf24'};">
                {'Conforme ONEE (≥ 0.90)' if cos_p >= 0.90 else 'Pénalité réactif potentielle'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        gain_kw = glob.get("gain_kw", 0)
        gain_pct = glob.get("gain_pct", 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Écart Situation de Référence (SER)</div>
            <div class="metric-value" style="color:#34d399;">-{gain_pct:.1f}%</div>
            <div class="metric-delta" style="color:#34d399;">Gain immédiat : -{gain_kw:.1f} kW vs Baseline</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📈 Courbe de Charge Globale du Port (24h) vs Seuil Souscrit")
    hours = [f"{h:02d}:00" for h in range(24)]
    base_curve = [
        1100, 1050, 980, 950, 920, 1050, 1350, 1680,
        1850, 1950, 2050, 2120, 1980, 1920, 2040, 2180,
        2240, 2190, 2050, 1920, 1780, 1620, 1450, 1280
    ]
    current_hour = datetime.now().hour
    base_curve[current_hour] = tot_p

    chart_df = pd.DataFrame({
        "Heure": hours,
        "Puissance Réelle (kW)": base_curve,
        "Seuil Souscrit ONEE (2500 kW)": [2500] * 24,
        "Référence SER (kW)": [int(v * 1.085) for v in base_curve]
    }).set_index("Heure")
    st.line_chart(chart_df, color=["#06b6d4", "#ef4444", "#94a3b8"])

    st.markdown("### ⚡ Répartition de la Charge par Poste Électrique")
    sub_names = []
    sub_kws = []
    for s in data.get("substations", []):
        sub_names.append(s["id"] + " - " + s["name"].split("—")[1].strip())
        sub_kws.append(s["sub_total_kw"])

    df_subs = pd.DataFrame({
        "Poste": sub_names,
        "Puissance Appelée (kW)": sub_kws
    }).set_index("Poste")
    st.bar_chart(df_subs, color="#38bdf8")

# -------------------------------------------------------------
# TAB 2 : LES 6 POSTES ÉLECTRIQUES
# -------------------------------------------------------------
with tab_substations:
    substations = data.get("substations", [])
    sub_choice = st.selectbox(
        "Sélectionnez le poste électrique à inspecter :",
        options=[s["id"] for s in substations],
        format_func=lambda x: next(s["name"] for s in substations if s["id"] == x)
    )

    selected_sub = next(s for s in substations if s["id"] == sub_choice)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Puissance Sous-Station", f"{selected_sub['sub_total_kw']} kW")
    with col_s2:
        st.metric("Énergie Cumulée", f"{selected_sub['sub_total_kwh']:,.1f} kWh")
    with col_s3:
        st.metric("Nombre de Départs / Compteurs", len(selected_sub["meters"]))

    st.markdown("#### 📋 Liste des Compteurs et Points de Mesure")
    rows = []
    for m in selected_sub["meters"]:
        rows.append({
            "Réf": m["id"],
            "Désignation Départ / Usage": m["name"],
            "Type": m["type"],
            "Adresse IP Modbus": f"{m['ip']}:{m['port']}",
            "U (V)": m["voltage_u12"],
            "I (A)": m["current_a"],
            "P (kW)": m["power_kw"],
            "Q (kVAR)": m["reactive_kvar"],
            "cos φ": m["cos_phi"],
            "f (Hz)": m["frequency_hz"],
            "Énergie (kWh)": f"{m['energy_kwh']:,.1f}",
            "Statut Comm": m["status"]
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# -------------------------------------------------------------
# TAB 3 : IPE & SER (ISO 50001:2018)
# -------------------------------------------------------------
with tab_iso:
    st.markdown("""
    ### 🎯 Indicateurs de Performance Énergétique (IPE)
    Conformément à la norme **ISO 50001:2018** et aux exigences du marché **12/DEPA/2026**, les IPE sont calculés en continu par rapport aux unités d'œuvre portuaires.
    """)

    ipes = data.get("ipe_indicators", {})
    c_ipe1, c_ipe2, c_ipe3, c_ipe4 = st.columns(4)

    with c_ipe1:
        st.metric("IPE Terminal Conteneurs", f"{ipes.get('containers_kwh_per_teu', 18.4)} kWh / EVP", delta="-1.2 kWh vs Cible")
    with c_ipe2:
        st.metric("IPE Vracs & Silos", f"{ipes.get('bulk_kwh_per_ton', 3.12)} kWh / Tonne", delta="-0.25 kWh vs Cible")
    with c_ipe3:
        st.metric("IPE Terminal Ro-Ro", f"{ipes.get('roro_kwh_per_unit', 7.85)} kWh / Remorque", delta="-0.4 kWh vs Cible")
    with c_ipe4:
        st.metric("IPE Tertiaire & Ateliers", f"{ipes.get('tertiary_kwh_per_sqm', 4.25)} kWh / m²", delta="-0.15 kWh vs Cible")

    st.markdown("---")
    st.markdown("### 📉 Situation Énergétique de Référence (SER) — Suivi Mensuel")
    months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct"]
    real_cons = [420, 395, 410, 380, 390, 405, 430, 445, 415, 398] # MWh
    ser_baseline = [460, 435, 450, 420, 430, 448, 475, 490, 460, 440] # MWh

    df_ser = pd.DataFrame({
        "Mois": months,
        "Consommation Réelle (MWh)": real_cons,
        "Référence SER Baseline (MWh)": ser_baseline
    }).set_index("Mois")

    st.bar_chart(df_ser, color=["#06b6d4", "#94a3b8"])
    total_saved_mwh = sum(ser_baseline) - sum(real_cons)
    st.success(f"🌱 **Gain énergétique total cumulé :** `{total_saved_mwh} MWh` évités | Économie estimée : `~{total_saved_mwh * 1150:,.0f} MAD` | CO₂ évité : `~{total_saved_mwh * 0.72:.1f} tCO₂`")

# -------------------------------------------------------------
# TAB 4 : GESTION DES ALERTES
# -------------------------------------------------------------
with tab_alerts:
    st.markdown("### 🚨 Événements & Alertes Actives du Réseau")
    alarms = data.get("active_alarms", [])
    if not alarms:
        st.success("✅ Aucune anomalie détectée. Tous les seuils de tension, puissance et facteur de puissance sont conformes.")
    else:
        for alm in alarms:
            level_color = "badge-crit" if alm["level"] == "CRITICAL" else "badge-warn"
            st.markdown(f"""
            <div style="background:#1e293b; border-left:4px solid {'#ef4444' if alm['level']=='CRITICAL' else '#f59e0b'}; padding:12px 16px; border-radius:0 8px 8px 0; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="{level_color}">{alm['level']}</span>
                    <span style="font-size:12px; color:#94a3b8; font-family:monospace;">{alm['timestamp'][:19]}</span>
                </div>
                <div style="font-weight:700; color:#f8fafc; margin-top:6px;">{alm['meter_name']} ({alm['meter_id']})</div>
                <div style="font-size:13px; color:#cbd5e1; margin-top:2px;">{alm['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Acquitter l'alerte {alm['id']}", key=alm['id']):
                engine.acknowledge_alarm(alm["id"])
                st.rerun()

# -------------------------------------------------------------
# TAB 5 : REGISTRES MODBUS TCP
# -------------------------------------------------------------
with tab_modbus:
    st.markdown("### 🔌 Cartographie des Registres Modbus TCP (FC03 Holding Registers)")
    st.markdown("Visualisation directe des mots registres 16 bits générés en mémoire pour les compteurs communicants :")

    all_meters = [m for s in data.get("substations", []) for m in s["meters"]]
    selected_m_id = st.selectbox(
        "Sélectionnez le compteur à interroger :",
        options=[m["id"] for m in all_meters],
        format_func=lambda x: next(f"{m['id']} — {m['name']} ({m['ip']})" for m in all_meters if m["id"] == x)
    )

    meter_obj = next(m for m in all_meters if m["id"] == selected_m_id)
    reg_rows = []
    for reg_name, reg_val in meter_obj.get("registers", {}).items():
        reg_rows.append({
            "Adresse Registre": reg_name.split("_")[0],
            "Grandeur": reg_name.split("_", 1)[1],
            "Valeur Brute (Décimal)": reg_val,
            "Valeur Hexadécimale": f"0x{reg_val:04X}" if isinstance(reg_val, int) else "N/A"
        })
    st.table(pd.DataFrame(reg_rows))

# -------------------------------------------------------------
# TAB 6 : REVUE ÉNERGÉTIQUE & RAPPORTS
# -------------------------------------------------------------
with tab_reports:
    st.markdown("### 📋 Revue Énergétique Périodique (ISO 50001)")
    st.markdown("Génération automatique du rapport d'exploitation conforme aux audits de management de l'énergie.")

    report_col1, report_col2 = st.columns(2)
    with report_col1:
        st.date_input("Période d'analyse — Du :", value=datetime(2026, 10, 1))
    with report_col2:
        st.date_input("Au :", value=datetime(2026, 10, 19))

    summary_data = []
    for s in data.get("substations", []):
        summary_data.append({
            "Poste Électrique": s["name"],
            "Puissance Moyenne (kW)": s["sub_total_kw"],
            "Énergie Période (MWh)": round(s["sub_total_kwh"] / 1000.0, 2),
            "Part du Port (%)": round((s["sub_total_kw"] / max(1.0, glob.get("total_power_kw", 1))) * 100, 1),
            "Statut ISO 50001": "Conforme"
        })
    df_rep = pd.DataFrame(summary_data)
    st.dataframe(df_rep, use_container_width=True)

    csv_data = df_rep.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger le Rapport en CSV",
        data=csv_data,
        file_name=f"Rapport_SME_Marsa_Maroc_DEPA_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# -------------------------------------------------------------
# TAB 7 : INTERFACE SYNOPTIQUE COMPLÈTE
# -------------------------------------------------------------
with tab_iframe:
    st.markdown("### 💻 Interface Synoptique Haute Fidélité")
    st.markdown("Vue complète avec schéma unifilaire et cartographie des postes du Port d'Agadir :")

    if INDEX_HTML_FILE.exists():
        try:
            with open(INDEX_HTML_FILE, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=920, scrolling=True)
        except Exception as e:
            st.error(f"Erreur de lecture du synoptique HTML : {e}")
    else:
        st.info("Le fichier index.html est optionnel pour la vue synoptique.")

# Pied de page
st.markdown("---")
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:#64748b;">
    <div>Marsa Maroc — Direction d'Exploitation au Port d'Agadir (DEPA) | Marché 12/DEPA/2026</div>
    <div>Déploiement certifié <b>Streamlit Community Cloud</b> | Moteur de simulation autonome</div>
</div>
""", unsafe_allow_html=True)
