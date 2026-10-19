#!/usr/bin/env python3
"""
Système de Monitoring Énergétique (SME) — Marsa Maroc DEPA (Port d'Agadir)
Marché n° 12/DEPA/2026 — Norme ISO 50001:2018
Simulateur industriel de télémétrie Modbus TCP/IP pour les 6 postes électriques.
"""

import os
import sys
import time
import json
import random
import math
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
METERS_STATE_FILE = os.path.join(DATA_DIR, "meters_state.json")
ALARMS_FILE = os.path.join(DATA_DIR, "alarms.json")

SUBSTATIONS = [
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

def load_initial_energies():
    """Charge ou génère les compteurs d'énergie active cumulée (kWh) de base."""
    energies = {}
    if os.path.exists(METERS_STATE_FILE):
        try:
            with open(METERS_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for sub in data.get("substations", []):
                    for m in sub.get("meters", []):
                        energies[m["id"]] = m.get("energy_kwh", 150000.0)
        except Exception:
            pass
    return energies

def simulate_cycle(accumulated_energies, cycle_seconds=3):
    now = datetime.now()
    timestamp_iso = now.isoformat()
    hour = now.hour + now.minute / 60.0

    # Facteur horaire d'activité portuaire (activités intenses 8h-20h, activité continue navires/reefer 24h)
    daily_factor = 0.65 + 0.35 * math.sin((hour - 6) / 24.0 * 2 * math.pi)
    daily_factor = max(0.45, min(1.15, daily_factor))

    substations_output = []
    total_site_kw = 0.0
    total_site_kvar = 0.0
    total_site_kwh = 0.0
    active_alarms = []

    for sub in SUBSTATIONS:
        meters_output = []
        sub_kw = 0.0
        sub_kwh = 0.0

        for meter in sub["meters"]:
            m_id = meter["id"]
            nom_kw = meter["nominal_kw"]

            # Variation pseudo-aléatoire continue
            noise = random.uniform(-0.06, 0.06)
            load_factor = max(0.15, min(1.05, daily_factor + noise))

            # Cas particuliers
            if "Cold-Ironing" in meter["name"]:
                # Navire connecté ou non (80% du temps un porte-conteneurs ou vraquier est raccordé)
                active_ship = (hour > 4 and hour < 22)
                kw = nom_kw * (0.85 + random.uniform(-0.08, 0.08)) if active_ship else nom_kw * 0.08
            elif "STS" in meter["name"] or "Gottwald" in meter["name"]:
                # Cycles de levage de conteneurs / bennes
                kw = nom_kw * random.uniform(0.40, 0.95)
            else:
                kw = nom_kw * load_factor

            kw = round(kw, 1)
            sub_kw += kw

            # Tensions triphasées 400V (légère dissymétrie réaliste < 1%)
            v_base = 400.0 + random.uniform(-3.5, 3.5)
            u12 = round(v_base + random.uniform(-0.8, 0.8), 1)
            u23 = round(v_base + random.uniform(-0.8, 0.8), 1)
            u31 = round(v_base + random.uniform(-0.8, 0.8), 1)

            # Facteur de puissance cos phi (généralement 0.91-0.96 grâce aux batteries de condensateurs)
            cos_phi = round(0.93 + random.uniform(-0.04, 0.03), 3)
            # Occasionnellement simuler un banc désaccordé pour tester l'alerte
            if m_id == "P5-M02" and random.random() < 0.03:
                cos_phi = 0.825

            # Puissance réactive Q = P * tan(acos(cos_phi))
            tan_phi = math.tan(math.acos(min(1.0, max(0.5, cos_phi))))
            kvar = round(kw * tan_phi, 1)

            # Puissance apparente S = sqrt(P^2 + Q^2)
            kva = round(math.sqrt(kw**2 + kvar**2), 1)

            # Courant moyen par phase I = S / (sqrt(3) * U)
            current_a = round((kva * 1000.0) / (math.sqrt(3) * u12), 1) if u12 > 0 else 0.0

            # Fréquence réseau (50 Hz +- 0.05 Hz)
            freq = round(50.0 + random.uniform(-0.04, 0.04), 2)

            # Énergie incrémentée kWh
            inc_kwh = (kw * (cycle_seconds / 3600.0))
            current_kwh = accumulated_energies.get(m_id, 145000.0 + random.randint(1000, 50000))
            current_kwh += inc_kwh
            accumulated_energies[m_id] = current_kwh
            sub_kwh += current_kwh

            # Statut communication Modbus TCP
            comm_status = "OK"
            latency_ms = random.randint(8, 38)
            # 0.5% chance de timeout simulé pour valider la tolérance de panne
            if random.random() < 0.005:
                comm_status = "RETRY"
                latency_ms = 450

            # Cartographie des registres Modbus (FC03 Holding Registers)
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

            # Détection d'alertes
            if cos_phi < 0.85:
                active_alarms.append({
                    "id": f"ALM-COS-{m_id}",
                    "level": "WARNING",
                    "timestamp": timestamp_iso,
                    "meter_id": m_id,
                    "meter_name": meter["name"],
                    "message": f"Facteur de puissance bas ({cos_phi} < 0.85) — Risque pénalité ONEE",
                    "status": "ACTIVE"
                })
            if kw > nom_kw * 1.15:
                active_alarms.append({
                    "id": f"ALM-PWR-{m_id}",
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

    # Site-wide calculations
    subscribed_power_kw = 2500.0  # Seuil puissance souscrite contrat ONEE
    if total_site_kw > subscribed_power_kw:
        active_alarms.append({
            "id": "ALM-SITE-PMAX",
            "level": "CRITICAL",
            "timestamp": timestamp_iso,
            "meter_id": "SITE",
            "meter_name": "Site Global Agadir",
            "message": f"Dépassement Puissance Souscrite ONEE ({int(total_site_kw)} kW > 2500 kW)",
            "status": "ACTIVE"
        })

    # SER (Situation Énergétique de Référence) modèle prévisionnel
    baseline_kw = round(total_site_kw * 1.085, 1)  # La référence historique consommait ~8.5% de plus
    gain_kw = round(baseline_kw - total_site_kw, 1)
    gain_pct = round((gain_kw / baseline_kw) * 100, 2) if baseline_kw > 0 else 0.0

    state = {
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
            "total_meters": sum(len(s["meters"]) for s in SUBSTATIONS),
            "online_meters": sum(len(s["meters"]) for s in SUBSTATIONS)
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

    # Sauvegarde atomique du fichier JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    temp_file = METERS_STATE_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, METERS_STATE_FILE)

    return state

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage du Simulateur Modbus TCP SME Marsa Maroc (Marché 12/DEPA/2026)...")
    accumulated_energies = load_initial_energies()

    cycle = 0
    try:
        while True:
            cycle += 1
            state = simulate_cycle(accumulated_energies, cycle_seconds=3)
            tot_kw = state["global_metrics"]["total_power_kw"]
            meters_cnt = state["global_metrics"]["total_meters"]
            alms = len(state["active_alarms"])
            print(f"[Cycle #{cycle} - {datetime.now().strftime('%H:%M:%S')}] 20/20 compteurs scrutés | P_tot={tot_kw} kW | Alertes actives={alms}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nArrêt propre du simulateur Modbus.")
        sys.exit(0)

if __name__ == "__main__":
    main()
