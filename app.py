import json
import math
import time
import csv
from pathlib import Path

import folium
import networkx as nx
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from network_engine import (forecast_link_risk, measured_recovery, run_seeded_stress_tests, evaluate_forecast_early_warning, simulate_cascading_failure)


# ================================================================
# GHOST NETWORK INDIA
# Page 1: India -> State -> City -> Route configuration
# Page 2: Automatic network formation -> failure -> rerouting -> healing
# All telemetry and failures are explicitly simulated demo data.
# ================================================================

st.set_page_config(
    page_title="GHOST NETWORK | India",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------- STYLE -----------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:#07111b;
    --panel:#0b1926;
    --panel2:#0d2231;
    --line:#20394a;
    --muted:#8da5b4;
    --cyan:#55dff2;
    --green:#43e6a0;
    --red:#ff5a70;
    --amber:#f4c45f;
    --white:#eaf4f8;
}

.stApp {
    background:radial-gradient(ellipse at 45% -20%,#10313b 0%,#07111b 52%,#050b12 100%);
    color:var(--white);
    font-family:Inter,sans-serif;
}

.block-container {
    max-width:1900px;
    padding:.7rem 1rem 1.5rem;
}

header[data-testid="stHeader"] {background:transparent;}
footer {visibility:hidden;}

section[data-testid="stSidebar"] {
    background:#091622;
    border-right:1px solid var(--line);
}

div[data-testid="stMetric"] {
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:9px;
    padding:10px 12px;
}

div[data-testid="stMetricLabel"] {
    color:var(--muted);
    font-size:10px;
    letter-spacing:.05em;
}

div[data-testid="stMetricValue"] {
    color:#edf9fc;
    font-family:'DM Mono',monospace;
}

div[data-testid="stButton"] button {
    background:#102a3a;
    border:1px solid #285268;
    color:#eaf8fc;
    border-radius:7px;
    font-size:12px;
    font-weight:700;
}

div[data-testid="stButton"] button:hover {
    border-color:var(--cyan);
    background:#163d50;
    color:white;
}

div[data-testid="stButton"] button[kind="primary"] {
    background:#0b697b;
    border-color:#55dff2;
}

.panel {
    background:linear-gradient(145deg,rgba(13,29,43,.98),rgba(8,18,28,.98));
    border:1px solid var(--line);
    border-radius:10px;
    padding:15px;
}

.panelhead {
    font-size:11px;
    font-weight:800;
    letter-spacing:.09em;
    color:#eff8fb;
    text-transform:uppercase;
}

.subtle {
    font-size:10px;
    color:#829cab;
}

.eyebrow {
    color:var(--cyan);
    font-size:10px;
    font-weight:800;
    letter-spacing:.15em;
    text-transform:uppercase;
}

.big-title {
    font-size:30px;
    line-height:1.05;
    font-weight:800;
    letter-spacing:-.025em;
    margin:4px 0 8px;
}

.step {
    border:1px solid var(--line);
    background:#091925;
    border-radius:8px;
    padding:10px 12px;
}

.step.active {
    border-color:var(--cyan);
    box-shadow:0 0 0 1px rgba(85,223,242,.12);
}

.step.done {
    border-color:#267c62;
}

.status-pill {
    display:inline-block;
    padding:4px 8px;
    border-radius:20px;
    border:1px solid var(--line);
    background:#091925;
    color:#a9c0cb;
    font-size:9px;
    font-weight:800;
    letter-spacing:.08em;
}

.failure-box {
    border:1px solid rgba(255,90,112,.55);
    background:rgba(255,90,112,.07);
    border-radius:9px;
    padding:13px;
}

.success-box {
    border:1px solid rgba(67,230,160,.45);
    background:rgba(67,230,160,.06);
    border-radius:9px;
    padding:13px;
}

.info-box {
    border:1px solid rgba(85,223,242,.35);
    background:rgba(85,223,242,.05);
    border-radius:9px;
    padding:13px;
}

hr {border-color:#1b3544;}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------- DATA ---------------------------------

STATE_CENTRES = {
    "Andhra Pradesh": (16.5,80.6), "Arunachal Pradesh": (28.2,94.7),
    "Assam": (26.2,92.8), "Bihar": (25.9,85.7),
    "Chhattisgarh": (21.3,82.0), "Goa": (15.4,74.0),
    "Gujarat": (22.4,71.5), "Haryana": (29.0,76.1),
    "Himachal Pradesh": (31.8,77.2), "Jharkhand": (23.6,85.5),
    "Karnataka": (15.0,76.0), "Kerala": (10.5,76.3),
    "Madhya Pradesh": (23.5,78.5), "Maharashtra": (19.3,75.2),
    "Manipur": (24.7,93.9), "Meghalaya": (25.5,91.3),
    "Mizoram": (23.2,92.8), "Nagaland": (26.1,94.5),
    "Odisha": (20.5,84.5), "Punjab": (31.0,75.3),
    "Rajasthan": (26.8,73.8), "Sikkim": (27.5,88.5),
    "Tamil Nadu": (11.0,78.4), "Telangana": (17.9,79.0),
    "Tripura": (23.8,91.6), "Uttar Pradesh": (27.0,80.8),
    "Uttarakhand": (30.1,79.1), "West Bengal": (23.0,87.8),
    "Andaman and Nicobar Islands": (11.7,92.7),
    "Chandigarh": (30.7,76.8),
    "Dadra and Nagar Haveli and Daman and Diu": (20.2,73.0),
    "Delhi": (28.6,77.2), "Jammu and Kashmir": (33.8,76.0),
    "Ladakh": (34.2,77.6), "Lakshadweep": (10.5,72.6),
    "Puducherry": (11.9,79.8),
}

BORDER_STATES = {
    "Arunachal Pradesh","Assam","Bihar","Gujarat","Himachal Pradesh",
    "Jammu and Kashmir","Ladakh","Manipur","Meghalaya","Mizoram",
    "Nagaland","Punjab","Rajasthan","Sikkim","Tripura","Uttar Pradesh",
    "Uttarakhand","West Bengal",
}

CITY_NODES = {
    "Andhra Pradesh":[("Visakhapatnam",17.6868,83.2185),("Vijayawada",16.5062,80.6480),("Tirupati",13.6288,79.4192),("Guntur",16.3067,80.4365)],
    "Arunachal Pradesh":[("Itanagar",27.0844,93.6053),("Naharlagun",27.1038,93.6950),("Pasighat",28.0669,95.3268)],
    "Assam":[("Guwahati",26.1445,91.7362),("Silchar",24.8333,92.7789),("Dibrugarh",27.4728,94.9120),("Jorhat",26.7509,94.2037)],
    "Bihar":[("Patna",25.5941,85.1376),("Gaya",24.7914,85.0002),("Muzaffarpur",26.1209,85.3647),("Bhagalpur",25.2425,86.9842)],
    "Chhattisgarh":[("Raipur",21.2514,81.6296),("Bilaspur",22.0797,82.1409),("Jagdalpur",19.0748,82.0080)],
    "Goa":[("Panaji",15.4909,73.8278),("Margao",15.2832,73.9862),("Vasco da Gama",15.3860,73.8440)],
    "Gujarat":[("Ahmedabad",23.0225,72.5714),("Surat",21.1702,72.8311),("Vadodara",22.3072,73.1812),("Rajkot",22.3039,70.8022),("Bhuj",23.2420,69.6669)],
    "Haryana":[("Gurugram",28.4595,77.0266),("Faridabad",28.4089,77.3178),("Hisar",29.1492,75.7217),("Ambala",30.3782,76.7767)],
    "Himachal Pradesh":[("Shimla",31.1048,77.1734),("Dharamshala",32.2190,76.3234),("Mandi",31.7080,76.9320)],
    "Jharkhand":[("Ranchi",23.3441,85.3096),("Jamshedpur",22.8046,86.2029),("Dhanbad",23.7957,86.4304)],
    "Karnataka":[("Bengaluru",12.9716,77.5946),("Mysuru",12.2958,76.6394),("Mangaluru",12.9141,74.8560),("Hubballi",15.3647,75.1240),("Belagavi",15.8497,74.4977)],
    "Kerala":[("Thiruvananthapuram",8.5241,76.9366),("Kochi",9.9312,76.2673),("Kozhikode",11.2588,75.7804),("Thrissur",10.5276,76.2144)],
    "Madhya Pradesh":[("Bhopal",23.2599,77.4126),("Indore",22.7196,75.8577),("Jabalpur",23.1815,79.9864),("Gwalior",26.2183,78.1828),("Rewa",24.5362,81.3037)],
    "Maharashtra":[("Mumbai",19.0760,72.8777),("Pune",18.5204,73.8567),("Nagpur",21.1458,79.0882),("Nashik",19.9975,73.7898),("Chhatrapati Sambhajinagar",19.8762,75.3433),("Kolhapur",16.7050,74.2433)],
    "Manipur":[("Imphal",24.8170,93.9368),("Thoubal",24.6380,94.0100),("Churachandpur",24.3330,93.6830)],
    "Meghalaya":[("Shillong",25.5788,91.8933),("Tura",25.5140,90.2030),("Jowai",25.4500,92.2000)],
    "Mizoram":[("Aizawl",23.7271,92.7176),("Lunglei",22.8870,92.7340),("Champhai",23.4740,93.3280)],
    "Nagaland":[("Kohima",25.6751,94.1086),("Dimapur",25.8629,93.7537),("Mokokchung",26.3220,94.5170)],
    "Odisha":[("Bhubaneswar",20.2961,85.8245),("Cuttack",20.4625,85.8830),("Rourkela",22.2604,84.8536),("Sambalpur",21.4669,83.9812)],
    "Punjab":[("Amritsar",31.6340,74.8723),("Ludhiana",30.9010,75.8573),("Jalandhar",31.3260,75.5762),("Pathankot",32.2643,75.6421)],
    "Rajasthan":[("Jaipur",26.9124,75.7873),("Jodhpur",26.2389,73.0243),("Udaipur",24.5854,73.7125),("Bikaner",28.0229,73.3119),("Jaisalmer",26.9157,70.9083)],
    "Sikkim":[("Gangtok",27.3389,88.6065),("Namchi",27.1667,88.3639),("Gyalshing",27.2890,88.2570)],
    "Tamil Nadu":[("Chennai",13.0827,80.2707),("Coimbatore",11.0168,76.9558),("Madurai",9.9252,78.1198),("Tiruchirappalli",10.7905,78.7047),("Salem",11.6643,78.1460)],
    "Telangana":[("Hyderabad",17.3850,78.4867),("Warangal",17.9689,79.5941),("Karimnagar",18.4386,79.1288),("Nizamabad",18.6725,78.0941)],
    "Tripura":[("Agartala",23.8315,91.2868),("Udaipur",23.5330,91.4830),("Dharmanagar",24.3667,92.1667)],
    "Uttar Pradesh":[("Lucknow",26.8467,80.9462),("Kanpur",26.4499,80.3319),("Varanasi",25.3176,82.9739),("Agra",27.1767,78.0081),("Noida",28.5355,77.3910),("Gorakhpur",26.7606,83.3732)],
    "Uttarakhand":[("Dehradun",30.3165,78.0322),("Haridwar",29.9457,78.1642),("Haldwani",29.2183,79.5130)],
    "West Bengal":[("Kolkata",22.5726,88.3639),("Siliguri",26.7271,88.3953),("Durgapur",23.5204,87.3119),("Asansol",23.6739,86.9524)],
    "Andaman and Nicobar Islands":[("Port Blair",11.6234,92.7265),("Diglipur",13.2500,92.9700)],
    "Chandigarh":[("Chandigarh",30.7333,76.7794)],
    "Dadra and Nagar Haveli and Daman and Diu":[("Daman",20.3974,72.8328),("Silvassa",20.2766,73.0083),("Diu",20.7141,70.9874)],
    "Delhi":[("New Delhi",28.6139,77.2090),("Dwarka",28.5921,77.0460),("Rohini",28.7495,77.0565)],
    "Jammu and Kashmir":[("Srinagar",34.0837,74.7973),("Jammu",32.7266,74.8570),("Anantnag",33.7311,75.1487)],
    "Ladakh":[("Leh",34.1526,77.5771),("Kargil",34.5539,76.1349)],
    "Lakshadweep":[("Kavaratti",10.5593,72.6358),("Agatti",10.8560,72.1950)],
    "Puducherry":[("Puducherry",11.9416,79.8083),("Karaikal",10.9254,79.8380)],
}

BORDER_CITIES = {
    "Pathankot","Amritsar","Jaisalmer","Bhuj","Siliguri","Gangtok",
    "Itanagar","Pasighat","Kohima","Dimapur","Aizawl","Agartala",
    "Srinagar","Jammu","Leh","Kargil","Guwahati","Tura","Haldwani",
    "Gorakhpur","Port Blair",
}

RISK_COLOR = {
    "NORMAL": "#43e6a0",
    "WATCH": "#f4c45f",
    "HIGH": "#ff586e",
}


# ------------------------- HELPERS -------------------------------

def norm(value):
    aliases = {
        "orissa": "odisha",
        "uttaranchal": "uttarakhand",
        "nct of delhi": "delhi",
        "jammu & kashmir": "jammu and kashmir",
        "andaman & nicobar islands": "andaman and nicobar islands",
    }
    value = str(value).strip().lower()
    return aliases.get(value, value)


def feat_name(feature):
    props = feature.get("properties", {})
    for key in ("NAME_1", "ST_NM", "state", "State", "name", "NAME", "STATE"):
        if props.get(key):
            return str(props[key])
    return "Unknown"


@st.cache_data(ttl=3600, show_spinner=False)
def load_geojson():
    local = Path(__file__).resolve().parent / "india_state.geojson"

    if local.exists():
        with open(local, "r", encoding="utf-8") as file:
            data = json.load(file)
        if data.get("features"):
            return data

    import urllib.request

    urls = [
        "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson",
        "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/india.geojson",
    ]

    last_error = None

    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "GhostNetworkIndia/2.0"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("features"):
                return data

        except Exception as error:
            last_error = error

    raise RuntimeError(
        f"India state boundary data could not be loaded. {last_error}"
    )


def point_in_ring(lat, lon, ring):
    inside = False
    j = len(ring) - 1

    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]

        intersects = (
            ((yi > lat) != (yj > lat))
            and (
                lon
                < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
            )
        )

        if intersects:
            inside = not inside

        j = i

    return inside


def point_in_geometry(lat, lon, geometry):
    if not geometry:
        return False

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    polygons = (
        [coordinates]
        if geometry_type == "Polygon"
        else coordinates
        if geometry_type == "MultiPolygon"
        else []
    )

    for polygon in polygons:
        if polygon and point_in_ring(lat, lon, polygon[0]):
            holes = any(
                point_in_ring(lat, lon, hole)
                for hole in polygon[1:]
            )

            if not holes:
                return True

    return False


def state_at_point(lat, lon, geojson):
    for feature in geojson.get("features", []):
        if point_in_geometry(lat, lon, feature.get("geometry")):
            name = feat_name(feature)

            for state in STATE_CENTRES:
                if norm(state) == norm(name):
                    return state

    return None


def state_bounds(feature):
    def walk(coords, output):
        if not coords:
            return

        if isinstance(coords[0], (float, int)):
            output.append(coords)
        else:
            for child in coords:
                walk(child, output)

    points = []
    walk(feature.get("geometry", {}).get("coordinates", []), points)

    if not points:
        return [[8, 68], [37, 98]]

    lats = [point[1] for point in points]
    lons = [point[0] for point in points]

    return [
        [min(lats), min(lons)],
        [max(lats), max(lons)],
    ]


def city_records():
    rows = []

    for state, cities in CITY_NODES.items():
        for index, (city, lat, lon) in enumerate(cities, 1):
            rows.append(
                {
                    "state": state,
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "code": (
                        f"IN-"
                        f"{''.join(w[0] for w in state.split() if w[0].isalnum())[:3].upper()}"
                        f"-{index:02d}"
                    ),
                    "risk": (
                        "HIGH"
                        if city in BORDER_CITIES
                        else "WATCH"
                        if index == len(cities)
                        else "NORMAL"
                    ),
                }
            )

    return rows


ALL_CITIES = city_records()
CITY_LOOKUP = {row["city"]: row for row in ALL_CITIES}


def distance_km(a, b):
    return (
        math.sqrt(
            (a["lat"] - b["lat"]) ** 2
            + (a["lon"] - b["lon"]) ** 2
        )
        * 111
    )


def edge_profile(a, b, link_source="MODELLED_GEOGRAPHIC_LINK"):
    """Create a link profile; telemetry values are illustrative, never live measurements."""
    distance = distance_km(CITY_LOOKUP[a], CITY_LOOKUP[b])
    seed = sum(ord(char) for char in (a + "|" + b))
    distance_cost = max(1, round(distance / 50))
    latency_ms = round(4 + distance / 35 + (seed % 9) * 0.35, 1)
    packet_loss_pct = round(0.1 + (seed % 11) * 0.09, 2)
    congestion_pct = 28 + (seed % 57)
    reliability_pct = round(99.9 - packet_loss_pct * 0.8 - (seed % 5) * 0.12, 2)
    # Lower is better: distance remains a factor, but quality metrics matter too.
    composite_cost = round(
        distance_cost * 0.35
        + latency_ms * 0.45
        + packet_loss_pct * 3.0
        + congestion_pct * 0.08
        + (100 - reliability_pct) * 2.0,
        3,
    )
    risk_score = round(min(
        100,
        congestion_pct * 0.55
        + packet_loss_pct * 10
        + latency_ms * 0.5
        + (100 - reliability_pct) * 8,
    ), 1)
    return {
        "weight": distance_cost,
        "distance_km": round(distance, 1),
        "latency_ms": latency_ms,
        "packet_loss_pct": packet_loss_pct,
        "congestion_pct": congestion_pct,
        "reliability_pct": reliability_pct,
        "risk_score": risk_score,
        "composite_cost": composite_cost,
        "link_source": link_source,
        "telemetry_source": "SYNTHETIC_ESTIMATE",
    }


def load_real_city_links():
    """Load explicitly sourced city links from data/real_city_links.csv.

    Expected columns: city_a, city_b, source, source_url, observed_at. Only exact
    city-name matches are accepted; no links are inferred from AS-level data.
    """
    path = Path(__file__).resolve().parent / "data" / "real_city_links.csv"
    rows = []
    if not path.exists():
        return rows
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                a, b = (row.get("city_a") or "").strip(), (row.get("city_b") or "").strip()
                source, source_url = (row.get("source") or "").strip(), (row.get("source_url") or "").strip()
                if a in CITY_LOOKUP and b in CITY_LOOKUP and a != b and source and source_url:
                    rows.append({"city_a": a, "city_b": b, "source": source,
                                 "source_url": source_url, "observed_at": (row.get("observed_at") or "").strip()})
    except (OSError, csv.Error):
        return []
    return rows


def build_state_graph(state):
    cities = CITY_NODES.get(state, [])
    graph = nx.Graph()

    for city, lat, lon in cities:
        graph.add_node(city, lat=lat, lon=lon)

    names = [city[0] for city in cities]
    name_set = set(names)
    real_links = [row for row in load_real_city_links()
                  if row["city_a"] in name_set and row["city_b"] in name_set]

    # Real topology links are used only when supplied with explicit provenance.
    # Their latency/loss/congestion still remain synthetic unless measured separately.
    for row in real_links:
        attrs = edge_profile(row["city_a"], row["city_b"], "EXTERNAL_DATASET_TOPOLOGY")
        attrs.update({"dataset_name": row["source"], "dataset_url": row["source_url"],
                      "observed_at": row["observed_at"]})
        graph.add_edge(row["city_a"], row["city_b"], **attrs)

    # Preserve the existing illustrative topology as a fallback. Never label
    # generated edges as observed real-world links.
    if not real_links:
        if len(names) <= 2:
            if len(names) == 2:
                graph.add_edge(names[0], names[1], **edge_profile(names[0], names[1]))
            return graph
        for i in range(len(names)):
            a, b = names[i], names[(i + 1) % len(names)]
            graph.add_edge(a, b, **edge_profile(a, b))
        for i in range(len(names)):
            if len(names) >= 4:
                a, b = names[i], names[(i + 2) % len(names)]
                if a != b:
                    graph.add_edge(a, b, **edge_profile(a, b))
    return graph


def topology_name(graph):
    density = nx.density(graph)

    if density >= 0.65:
        return "Full Mesh"
    if density >= 0.35:
        return "Partial Mesh"
    if density > 0:
        return "Sparse / Redundant"
    return "Point-to-Point"


def calculate_route(source, destination, state):
    graph = build_state_graph(state)

    if source not in graph or destination not in graph:
        return [], graph

    try:
        route = nx.shortest_path(
            graph,
            source=source,
            target=destination,
            weight="composite_cost",
        )
        return route, graph
    except nx.NetworkXNoPath:
        return [], graph


def calculate_alternate_route(source, destination, state, primary_route):
    graph = build_state_graph(state)

    if len(primary_route) < 2:
        return primary_route

    failed_edge = (
        primary_route[0],
        primary_route[1],
    )

    if graph.has_edge(*failed_edge):
        graph.remove_edge(*failed_edge)

    try:
        return nx.shortest_path(
            graph,
            source=source,
            target=destination,
            weight="composite_cost",
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def route_distance(route):
    total = 0

    for a, b in zip(route, route[1:]):
        total += distance_km(
            CITY_LOOKUP[a],
            CITY_LOOKUP[b],
        )

    return total


def route_metrics(route, graph):
    edges = [graph[a][b] for a, b in zip(route, route[1:]) if graph.has_edge(a, b)]
    hops = max(1, len(route) - 1)
    distance = route_distance(route)
    if edges:
        latency = round(sum(e.get("latency_ms", 8) for e in edges), 1)
        packet_loss = round(sum(e.get("packet_loss_pct", 0.2) for e in edges), 2)
        jitter = round(0.8 + sum(abs(e.get("latency_ms", 8) % 3) for e in edges) / len(edges), 1)
        utilization = round(sum(e.get("congestion_pct", 62) for e in edges) / len(edges))
        reliability = round(math.prod(e.get("reliability_pct", 99.8) / 100 for e in edges) * 100, 2)
        route_cost = round(sum(e.get("composite_cost", e.get("weight", 1)) for e in edges), 3)
    else:
        latency, packet_loss, jitter, utilization, reliability, route_cost = 0, 100, 0, 0, 0, 0
    return {
        "latency": latency,
        "packet_loss": packet_loss,
        "jitter": jitter,
        "bandwidth": "1 Gbps",
        "throughput": f"{max(0, round(1000 * (1 - utilization / 130)))} Mbps",
        "utilization": utilization,
        "hops": hops,
        "route_cost": route_cost,
        "ttl": 64,
        "availability": reliability,
        "distance_km": round(distance, 1),
    }



def route_is_valid(route, graph, source, destination):
    return bool(
        route
        and route[0] == source
        and route[-1] == destination
        and all(graph.has_edge(a, b) for a, b in zip(route, route[1:]))
    )


def benchmark_recovery(source, destination, graph, primary_route):
    """Compatibility wrapper around measured simulator recovery timings."""
    return measured_recovery(graph, source, destination, primary_route)


# ---------------------- SESSION STATE ----------------------------

defaults = {
    "page": "selection",
    "selected_state": None,
    "source_city": None,
    "destination_city": None,
    "manual_path": [],
    "selection_step": "state",
    "pending_city": None,
    "last_click": None,
    "last_state_click": None,
    "map_center": None,
    "map_zoom": None,
    "simulation_started": False,
    "simulation_complete": False,
}

for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ------------------------- HEADER --------------------------------

st.markdown(
    """
<div class="topline">
GHOST NETWORK
<span style="color:#536d7c"> | </span>
INDIA SD-WAN
<span style="color:#536d7c"> | </span>
AUTONOMOUS NETWORK OPERATIONS
</div>
""",
    unsafe_allow_html=True,
)


# ================================================================
# NODE SELECTION DIALOG
# ================================================================

@st.dialog("SELECT NETWORK NODE ROLE", width="small")
def node_selection_dialog(city):

    selected = st.session_state.selected_state
    source = st.session_state.source_city
    destination = st.session_state.destination_city

    row = CITY_LOOKUP[city]

    st.markdown(
        f"""
<div class="panel">
<div class="eyebrow">NODE IDENTIFIED</div>
<div style="font-size:24px;font-weight:800">{city}</div>
<div class="subtle">{selected} · {row['code']}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not source:
        st.markdown("### Step 1 — Source Node")
        st.write(
            "Select this node as the origin of the packet."
        )

        if st.button(
            f"✓ SELECT {city.upper()} AS SOURCE",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.source_city = city
            st.session_state.selection_step = "destination"
            st.session_state.pending_city = None
            st.session_state.last_click = f"CITY|{city}|destination"
            st.rerun()

    elif not destination:
        st.markdown("### Step 2 — Destination Node")
        st.write(f"Source node: **{source}**")

        if city == source:
            st.warning(
                "Destination must be different from the source."
            )
        else:
            if st.button(
                f"✓ SELECT {city.upper()} AS DESTINATION",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.destination_city = city
                st.session_state.selection_step = "path"
                st.session_state.pending_city = None
                st.session_state.last_click = f"CITY|{city}|path"
                st.rerun()

    else:
        st.markdown("### Step 3 — Path Configuration")

        st.write(f"**Source:** {source}")
        st.write(f"**Destination:** {destination}")

        st.markdown(
            "Select this node as an intermediate hop if you want "
            "to demonstrate a manually constrained route."
        )

        if city != source and city != destination:
            if st.button(
                f"▶ USE {city.upper()} AS THE HOP & START SIMULATION",
                type="primary",
                use_container_width=True,
            ):
                # Exactly one intermediate hop: source → selected hop → destination.
                st.session_state.manual_path = [source, city, destination]
                st.session_state.pending_city = None
                st.session_state.last_click = None
                st.session_state.page = "simulation"
                st.session_state.simulation_started = True
                st.session_state.simulation_complete = False
                st.rerun()
        else:
            st.caption(
                "Choose a city different from the source and destination."
            )

        if st.button(
            "SKIP HOP & START SIMULATION",
            use_container_width=True,
        ):
            # Use the automatic shortest route when no manual hop is needed.
            st.session_state.manual_path = []
            st.session_state.pending_city = None
            st.session_state.last_click = None
            st.session_state.page = "simulation"
            st.session_state.simulation_started = True
            st.session_state.simulation_complete = False
            st.rerun()


# ================================================================
# PAGE 1 — INDIA NETWORK MAP
# ================================================================

def show_selection_page():

    selected = st.session_state.selected_state
    source = st.session_state.source_city
    destination = st.session_state.destination_city
    path = st.session_state.manual_path

    h1, h2 = st.columns([3, 1])

    with h1:
        st.markdown(
            """
<div class="eyebrow">NETWORK CONFIGURATION</div>
<div class="big-title">India Network Topology</div>
<div class="subtle">
Select a state, inspect its city nodes, configure a packet route,
then launch the autonomous self-healing simulation.
</div>
""",
            unsafe_allow_html=True,
        )

    with h2:
        st.markdown(
            """
<div style="text-align:right;padding-top:8px">
<span class="status-pill">● DEMO SYSTEM ONLINE</span>
</div>
""",
            unsafe_allow_html=True,
        )

    steps = [
        ("1", "STATE", st.session_state.selection_step == "state"),
        ("2", "SOURCE", st.session_state.selection_step == "source"),
        ("3", "DESTINATION", st.session_state.selection_step == "destination"),
        ("4", "PATH", st.session_state.selection_step == "path"),
        ("5", "SIMULATION", False),
    ]

    cols = st.columns(5)

    for col, (number, label, active) in zip(cols, steps):
        with col:
            state_class = "active" if active else ""

            if label == "STATE" and selected:
                state_class = "done"
            if label == "SOURCE" and source:
                state_class = "done"
            if label == "DESTINATION" and destination:
                state_class = "done"

            st.markdown(
                f"""
<div class="step {state_class}">
<span style="color:#55dff2;font-family:'DM Mono'">{number}</span>
&nbsp; {label}
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not selected:
        st.markdown(
            """
<div class="info-box">
<b>STEP 1 — SELECT A STATE</b><br>
Click any state on the India map. The map will automatically zoom
into that state and reveal its illustrative network nodes.
</div>
""",
            unsafe_allow_html=True,
        )

    elif st.session_state.selection_step == "source":
        st.markdown(
            f"""
<div class="info-box">
<b>STEP 2 — SELECT SOURCE NODE</b><br>
<strong>{selected}</strong> is selected.
Click a city node to choose where the packet originates.
</div>
""",
            unsafe_allow_html=True,
        )

    elif st.session_state.selection_step == "destination":
        st.markdown(
            f"""
<div class="info-box">
<b>STEP 3 — SELECT DESTINATION NODE</b><br>
Source: <strong>{source}</strong><br>
Click another city node to choose where the packet should arrive.
</div>
""",
            unsafe_allow_html=True,
        )

    else:
        route_preview = (
            " → ".join(path)
            if path
            else f"{source} → {destination}"
        )

        st.markdown(
            f"""
<div class="success-box">
<b>STEP 4 — PATH CONFIGURATION</b><br>
Source: <strong>{source}</strong>
&nbsp;&nbsp; → &nbsp;&nbsp;
Destination: <strong>{destination}</strong><br>
Current path: <strong>{route_preview}</strong><br>
<span class="subtle">
Click another city to add it as an intermediate hop, or launch the
simulation using the automatic shortest route.
</span>
</div>
""",
            unsafe_allow_html=True,
        )

    try:
        geo = load_geojson()

        if selected:
            feature = next(
                (
                    f for f in geo["features"]
                    if norm(feat_name(f)) == norm(selected)
                ),
                None,
            )

            if feature:
                bounds = state_bounds(feature)
                sw, ne = bounds
                fmap_center = [
                    (sw[0] + ne[0]) / 2,
                    (sw[1] + ne[1]) / 2,
                ]
                fmap_zoom = 6
            else:
                fmap_center = STATE_CENTRES[selected]
                fmap_zoom = 6
        else:
            fmap_center = [22.8, 82.0]
            fmap_zoom = 4.3

        # Retain the Leaflet viewport across Streamlit reruns.
        if st.session_state.map_center is not None:
            fmap_center = st.session_state.map_center
        if st.session_state.map_zoom is not None:
            fmap_zoom = st.session_state.map_zoom

        fmap = folium.Map(
            location=fmap_center,
            zoom_start=fmap_zoom,
            min_zoom=3,
            max_zoom=10,
            tiles="CartoDB dark_matter",
            control_scale=True,
            prefer_canvas=True,
            zoom_control=True,
            scrollWheelZoom=True,
        )

        def state_style(feature):
            name = feat_name(feature)
            is_border = norm(name) in {
                norm(x) for x in BORDER_STATES
            }
            is_selected = (
                selected
                and norm(name) == norm(selected)
            )

            if is_selected:
                return {
                    "fillColor": "#0e7185",
                    "color": "#55dff2",
                    "weight": 4,
                    "fillOpacity": 0.92,
                }

            if is_border:
                return {
                    "fillColor": "#17394b",
                    "color": "#438dff",
                    "weight": 1.5,
                    "fillOpacity": 0.8,
                }

            return {
                "fillColor": "#27404a",
                "color": "#667983",
                "weight": 0.8,
                "fillOpacity": 0.75,
            }

        folium.GeoJson(
            geo,
            name="Indian States",
            style_function=state_style,
            highlight_function=lambda feature: {
                "fillColor": "#298d78",
                "color": "#72f4d3",
                "weight": 3,
                "fillOpacity": 0.9,
            },
        ).add_to(fmap)

        if not selected:
            for state, (lat, lon) in STATE_CENTRES.items():
                folium.Marker(
                    [lat, lon],
                    icon=folium.DivIcon(
                        html=f"""
<div style="
font:600 9px Inter,sans-serif;
color:#dcebef;
text-shadow:0 0 3px #07111b;
white-space:nowrap;
transform:translate(-50%,-50%);
">
{state}
</div>
"""
                    ),
                ).add_to(fmap)

        visible_cities = [
            row for row in ALL_CITIES
            if selected and row["state"] == selected
        ]

        for index in range(len(visible_cities) - 1):
            a = visible_cities[index]
            b = visible_cities[index + 1]

            folium.PolyLine(
                [
                    [a["lat"], a["lon"]],
                    [b["lat"], b["lon"]],
                ],
                color="#286d6d",
                weight=1.5,
                opacity=0.65,
                dash_array="4,7",
            ).add_to(fmap)

        route_to_draw = path[:]

        if len(route_to_draw) < 2 and source and destination:
            route_to_draw, _ = calculate_route(
                source,
                destination,
                selected,
            )

        if len(route_to_draw) >= 2:
            folium.PolyLine(
                [
                    [CITY_LOOKUP[city]["lat"], CITY_LOOKUP[city]["lon"]]
                    for city in route_to_draw
                    if city in CITY_LOOKUP
                ],
                color="#57e8f5",
                weight=5,
                opacity=0.95,
                tooltip="Configured packet route",
            ).add_to(fmap)

        for node in visible_cities:
            city = node["city"]

            if city == source:
                marker_color = "#55dff2"
                role = "SOURCE"
                radius = 9
            elif city == destination:
                marker_color = "#55dff2"
                role = "DESTINATION"
                radius = 9
            elif city in path:
                marker_color = "#55dff2"
                role = "PATH HOP"
                radius = 8
            else:
                marker_color = RISK_COLOR[node["risk"]]
                role = "NETWORK NODE"
                radius = 6

            popup_html = f"""
<div style="font-family:Arial;min-width:210px">
<b style="font-size:15px">{city}</b>
<hr style="border-color:#294354">
Node ID: <b>{node['code']}</b><br>
Role: <b>{role}</b><br>
Risk class: <b style="color:{RISK_COLOR[node['risk']]}">{node['risk']}</b>
<hr style="border-color:#294354">
Click the node to configure its route role.
</div>
"""

            folium.CircleMarker(
                [node["lat"], node["lon"]],
                radius=radius,
                color=marker_color,
                weight=2,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.95,
                tooltip=f"{city} | {node['code']} | {node['risk']}",
                popup=folium.Popup(
                    popup_html,
                    max_width=280,
                ),
            ).add_to(fmap)

        Fullscreen(position="topleft").add_to(fmap)

        map_data = st_folium(
            fmap,
            use_container_width=True,
            height=560,
            returned_objects=[
                "last_clicked",
                "last_object_clicked_tooltip",
                "center",
                "zoom",
            ],
            key="india_network_map",
        )

        # Store the current center/zoom before any interaction reruns.
        if map_data:
            view_center = map_data.get("center")
            view_zoom = map_data.get("zoom")
            if isinstance(view_center, dict) and all(k in view_center for k in ("lat", "lng")):
                st.session_state.map_center = [view_center["lat"], view_center["lng"]]
            if isinstance(view_zoom, (int, float)):
                st.session_state.map_zoom = view_zoom

        tooltip = (
            map_data.get("last_object_clicked_tooltip")
            if map_data
            else None
        )

        if (
            tooltip
            and isinstance(tooltip, str)
            and "|" in tooltip
        ):
            city = tooltip.split("|")[0].strip()

            if (
                city in CITY_LOOKUP
                and selected
                and CITY_LOOKUP[city]["state"] == selected
            ):
                signature = (
                    f"CITY|{city}|"
                    f"{st.session_state.selection_step}"
                )

                if st.session_state.last_click != signature:
                    # Open the node dialog in this same Streamlit run instead
                    # of forcing an extra full-page rerun, which nudges the
                    # viewport upward when a node/code is clicked.
                    st.session_state.pending_city = city
                    st.session_state.last_click = signature

        clicked = map_data.get("last_clicked") if map_data else None

        if (
            clicked
            and clicked.get("lat") is not None
            and clicked.get("lng") is not None
            and not (
                tooltip
                and isinstance(tooltip, str)
                and "|" in tooltip
            )
        ):
            signature = (
                f"STATE|"
                f"{round(clicked['lat'], 4)}|"
                f"{round(clicked['lng'], 4)}"
            )

            # st_folium can keep returning the previous map click after a rerun.
            # Track state-map clicks separately from node/dialog interactions so
            # a stale coordinate cannot overwrite the user's selected state.
            if st.session_state.last_state_click != signature:
                st.session_state.last_state_click = signature
                hit = state_at_point(
                    clicked["lat"],
                    clicked["lng"],
                    geo,
                )

                # Only reset route configuration when the user actually picks
                # a different state. Re-renders and node clicks must preserve it.
                if hit and hit != st.session_state.selected_state:
                    st.session_state.selected_state = hit
                    # Keep the viewport where the user clicked; no zoom reset.
                    st.session_state.source_city = None
                    st.session_state.destination_city = None
                    st.session_state.manual_path = []
                    st.session_state.selection_step = "source"
                    st.session_state.pending_city = None
                    st.session_state.last_click = signature
                    st.rerun()

    except Exception as error:
        st.error(f"Could not render India network map: {error}")
        st.info(
            "The application expects india_state.geojson beside app.py."
        )

    if st.session_state.pending_city:
        node_selection_dialog(
            st.session_state.pending_city
        )

    if selected:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        route = (
            path
            if len(path) >= 2
            else (
                calculate_route(
                    source,
                    destination,
                    selected,
                )[0]
                if source and destination
                else []
            )
        )

        r1, r2, r3, r4 = st.columns(4)

        r1.metric("SELECTED STATE", selected)
        r2.metric("SOURCE NODE", source or "Awaiting")
        r3.metric("DESTINATION", destination or "Awaiting")
        r4.metric("PATH HOPS", max(0, len(route) - 1))

        if source and destination:
            st.markdown(
                f"""
<div class="panel" style="margin-top:10px">
<div class="panelhead">PACKET PATH</div>
<div style="
font-family:'DM Mono';
font-size:15px;
color:#55dff2;
padding-top:8px;
">
{' → '.join(route)}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            c1, c2 = st.columns([3, 1])

            with c1:
                if path:
                    st.caption(
                        "Intermediate hops: "
                        + " → ".join(path)
                    )
                else:
                    st.caption(
                        "No manual intermediate hop selected. "
                        "OSPF will use the shortest available path."
                    )

            with c2:
                if st.button(
                    "▶ START SIMULATION",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.page = "simulation"
                    st.session_state.simulation_started = True
                    st.session_state.simulation_complete = False
                    st.rerun()


# ================================================================
# PAGE 2 — SELF-HEALING SIMULATION
# ================================================================

def network_figure(
    route,
    alternate_route,
    graph,
    stage,
    packet_index=None,
):
    selected_state = st.session_state.selected_state
    cities = CITY_NODES[selected_state]

    positions = {
        city: (lon, lat)
        for city, lat, lon in cities
    }

    edge_x = []
    edge_y = []

    for a, b in graph.edges():
        edge_x.extend(
            [positions[a][0], positions[b][0], None]
        )
        edge_y.extend(
            [positions[a][1], positions[b][1], None]
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scattergeo(
            lon=edge_x,
            lat=edge_y,
            mode="lines",
            line=dict(color="#284c5b", width=1.4),
            hoverinfo="skip",
            name="Network links",
        )
    )

    if stage in {"REROUTING", "HEALING", "HEALED", "RECOVERY FAILED"}:
        active_route = alternate_route
    else:
        active_route = route

    route_x = []
    route_y = []

    for a, b in zip(active_route, active_route[1:]):
        route_x.extend(
            [positions[a][0], positions[b][0], None]
        )
        route_y.extend(
            [positions[a][1], positions[b][1], None]
        )

    route_color = (
        "#ff5a70"
        if stage == "FAILURE"
        else "#55dff2"
        if stage in {"REROUTING", "HEALING"}
        else "#43e6a0"
    )

    if route_x:
        fig.add_trace(
            go.Scattergeo(
                lon=route_x,
                lat=route_y,
                mode="lines",
                line=dict(color=route_color, width=5),
                hoverinfo="skip",
                name="Active route",
            )
        )

    if stage in {"FAILURE", "ANALYSIS", "REROUTING"} and len(route) >= 2:
        a, b = route[0], route[1]

        fig.add_trace(
            go.Scattergeo(
                lon=[positions[a][0], positions[b][0]],
                lat=[positions[a][1], positions[b][1]],
                mode="lines",
                line=dict(
                    color="#ff5a70",
                    width=6,
                    dash="dash",
                ),
                hoverinfo="skip",
                name="Failed link",
            )
        )

    node_lons = []
    node_lats = []
    node_text = []
    node_colors = []

    for city, lat, lon in cities:
        node_lons.append(lon)
        node_lats.append(lat)
        node_text.append(city)

        if city == st.session_state.source_city:
            node_colors.append("#55dff2")
        elif city == st.session_state.destination_city:
            node_colors.append("#55dff2")
        elif stage == "FAILURE" and city in route[:2]:
            node_colors.append("#ff5a70")
        elif (
            stage in {"REROUTING", "HEALING", "HEALED"}
            and city in alternate_route
        ):
            node_colors.append("#43e6a0")
        else:
            node_colors.append("#43e6a0")

    fig.add_trace(
        go.Scattergeo(
            lon=node_lons,
            lat=node_lats,
            mode="markers+text",
            text=node_text,
            textposition="bottom center",
            textfont=dict(color="#dcebef", size=10),
            marker=dict(
                size=10,
                color=node_colors,
                line=dict(color="#eafcff", width=1.2),
            ),
            hovertext=node_text,
            hoverinfo="text",
            name="City nodes",
        )
    )

    if (
        packet_index is not None
        and active_route
        and 0 <= packet_index < len(active_route)
    ):
        packet_city = active_route[packet_index]
        lon, lat = positions[packet_city]

        fig.add_trace(
            go.Scattergeo(
                lon=[lon],
                lat=[lat],
                mode="markers",
                marker=dict(
                    size=20,
                    color="#55dff2",
                    line=dict(color="#ffffff", width=2),
                ),
                hoverinfo="skip",
                name="Packet",
            )
        )

    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#102833",
        showocean=True,
        oceancolor="#07131e",
        showcountries=True,
        countrycolor="#294b58",
        showcoastlines=True,
        coastlinecolor="#315d69",
        bgcolor="rgba(0,0,0,0)",
        fitbounds="locations",
    )

    fig.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    return fig


def telemetry_panel(
    metrics,
    stage,
    route,
    alternate_route,
    graph,
):
    failed_link = (
        f"{route[0]} → {route[1]}"
        if len(route) >= 2
        else "N/A"
    )

    if stage in {"FAILURE", "ANALYSIS"}:
        latency = round(metrics["latency"] * 3.1, 1)
        packet_loss = 8.4
        jitter = 18.7
        utilization = 91
        throughput = "410 Mbps"
        status = "DEGRADED"
    elif stage == "REROUTING":
        latency = round(metrics["latency"] * 1.55, 1)
        packet_loss = 2.1
        jitter = 8.4
        utilization = 74
        throughput = "650 Mbps"
        status = "REROUTING" if alternate_route else "NO BACKUP PATH"
    elif stage == "RECOVERY FAILED":
        latency = round(metrics["latency"] * 3.1, 1)
        packet_loss = 100.0
        jitter = round(metrics["jitter"] * 3, 1)
        utilization = 0
        throughput = "0 Mbps"
        status = "RECOVERY FAILED"
    else:
        latency = metrics["latency"]
        packet_loss = metrics["packet_loss"]
        jitter = metrics["jitter"]
        utilization = metrics["utilization"]
        throughput = metrics["throughput"]
        status = "HEALTHY"

    st.markdown(
        """
<div class="panelhead">NETWORK HEALTH & TELEMETRY</div>
<div class="subtle">
Illustrative network measurements generated for the selected route.
</div>
""",
        unsafe_allow_html=True,
    )

    a, b = st.columns(2)
    a.metric("LATENCY", f"{latency} ms")
    b.metric("PACKET LOSS", f"{packet_loss}%")

    a, b = st.columns(2)
    a.metric("JITTER", f"{jitter} ms")
    b.metric("HOPS", metrics["hops"])

    a, b = st.columns(2)
    a.metric("BANDWIDTH", metrics["bandwidth"])
    b.metric("THROUGHPUT", throughput)

    a, b = st.columns(2)
    a.metric("LINK UTILIZATION", f"{utilization}%")
    b.metric("ROUTE COST", metrics["route_cost"])

    a, b = st.columns(2)
    a.metric("TTL", metrics["ttl"])
    b.metric("AVAILABILITY", f"{metrics['availability']}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="panelhead">ROUTING INTELLIGENCE</div>

<div style="margin-top:10px">
<span class="subtle">ROUTING PROTOCOL</span><br>
<b style="font-family:'DM Mono';font-size:17px;color:#55dff2">OSPF</b>
</div>

<div style="margin-top:10px">
<span class="subtle">PATH CALCULATION</span><br>
<b>Multi-metric Dijkstra</b>
</div>

<div style="margin-top:10px">
<span class="subtle">TOPOLOGY</span><br>
<b>{topology_name(graph)}</b>
</div>

<div style="margin-top:10px">
<span class="subtle">CURRENT STATUS</span><br>
<b>{status}</b>
</div>
<div style="margin-top:10px">
<span class="subtle">ROUTE DISTANCE</span><br>
<b>{metrics.get('distance_km', 0)} km</b>
</div>
<div style="margin-top:10px">
<span class="subtle">COST MODEL</span><br>
<b>Latency + loss + congestion + reliability + distance</b>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    if stage in {"FAILURE", "ANALYSIS"}:
        st.markdown(
            f"""
<div class="failure-box">
<div class="panelhead" style="color:#ff5a70">
⚠ FAILURE ANALYSIS
</div>

<div style="margin-top:9px">
<b>Failure type</b><br>
Link degradation / congestion
</div>

<div style="margin-top:8px">
<b>Failed link</b><br>
{failed_link}
</div>

<div style="margin-top:8px">
<b>Why did it fail?</b><br>
The injected degradation is represented by high congestion and
worse latency/loss telemetry on the selected primary link. This is
simulated telemetry, not a live diagnosis; the composite risk model
recommends isolating the link and switching to a healthy alternate.
</div>

<div style="margin-top:8px">
<b>Observed symptoms</b><br>
• Utilization: 91%<br>
• Latency increased<br>
• Packet loss increased<br>
• Jitter increased<br>
• Link health threshold exceeded
</div>

<div style="margin-top:8px">
<b>Detection mechanism</b><br>
Link-health monitoring + timeout detection
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif stage == "REROUTING":
        new_route = (
            " → ".join(alternate_route)
            if alternate_route
            else "No alternate route"
        )

        st.markdown(
            f"""
<div class="info-box">
<div class="panelhead">OSPF ROUTE RECALCULATION</div>

<div style="margin-top:9px">
<b>Primary path</b><br>
<span style="color:#ff5a70">{' → '.join(route)}</span>
</div>

<div style="margin-top:9px">
<b>Alternate path selected</b><br>
<span style="color:#55dff2">{new_route}</span>
</div>

<div style="margin-top:9px">
<b>Decision</b><br>
Dijkstra recalculated the shortest reachable path
after the failed link was removed.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif stage == "RECOVERY FAILED":
        st.markdown(
            """
<div class="failure-box">
<div class="panelhead" style="color:#ff5a70">✕ SELF-HEALING FAILED</div>
<div style="margin-top:9px">
No valid alternate path was found after the simulated link failure.
Traffic cannot be confirmed as restored. Try another source/destination
pair or select a topology with more redundant links.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif stage == "HEALED":
        st.markdown(
            f"""
<div class="success-box">
<div class="panelhead" style="color:#43e6a0">
✓ SELF-HEALING COMPLETE
</div>

<div style="margin-top:9px">
<b>Active route</b><br>
{' → '.join(alternate_route or route)}
</div>

<div style="margin-top:9px">
✓ Failure isolated<br>
✓ Alternate route established<br>
✓ Forwarding path updated<br>
✓ Packet delivery restored<br>
✓ Network converged
</div>

<div style="margin-top:9px">
<b>Convergence time</b><br>
3.4 ms
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            """
<div class="success-box">
<div class="panelhead" style="color:#43e6a0">
● NETWORK STABLE
</div>

<div style="margin-top:8px">
Primary and backup links are healthy.
OSPF has a valid route to the destination.
</div>
</div>
""",
            unsafe_allow_html=True,
        )


def run_automatic_simulation():
    selected = st.session_state.selected_state
    source = st.session_state.source_city
    destination = st.session_state.destination_city

    route = st.session_state.manual_path[:]

    if len(route) < 2:
        route, graph = calculate_route(
            source,
            destination,
            selected,
        )
    else:
        graph = build_state_graph(selected)

        for a, b in zip(route, route[1:]):
            if not graph.has_edge(a, b):
                graph.add_edge(a, b, **edge_profile(a, b))

    if not route:
        st.error("No route could be calculated.")
        return

    alternate_route = calculate_alternate_route(
        source,
        destination,
        selected,
        route,
    )

    metrics = route_metrics(route, graph)

    # Simulate failure of the primary route's first link, then calculate
    # a backup on a copy of the selected topology. Keep the original graph
    # intact so the map can still display the failed link in red.
    failed_graph = graph.copy()
    alternate_route = []
    if len(route) >= 2:
        failed_link = (route[0], route[1])
        if failed_graph.has_edge(*failed_link):
            failed_graph.remove_edge(*failed_link)
        try:
            candidate = nx.shortest_path(
                failed_graph,
                source=source,
                target=destination,
                weight="composite_cost",
            )
            if len(candidate) >= 2 and all(
                failed_graph.has_edge(a, b)
                for a, b in zip(candidate, candidate[1:])
            ):
                alternate_route = candidate
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            alternate_route = []

    stage_box = st.empty()

    left, right = st.columns([1.75, 1], gap="small")
    network_box = left.empty()
    dashboard_box = right.empty()

    stages = [
        ("FORMING", "Building topology and discovering neighboring nodes."),
        ("STABLE", "Primary route established; a backup is precomputed using link-quality metrics."),
        ("FAILURE", "A deterministic simulated primary-link degradation has been injected."),
        ("ANALYSIS", "Composite telemetry risk is checked and the failure cause is explained."),
        ("REROUTING", "Selecting the lowest-cost reachable path using latency, loss, congestion and reliability."),
    ]

    if alternate_route:
        stages.extend([
            ("HEALING", "Traffic is moving through the verified alternate route."),
            ("HEALED", "Connectivity restored through a verified alternate route."),
        ])
    else:
        stages.append((
            "RECOVERY FAILED",
            "No alternate route is available after the primary link failure.",
        ))

    for stage, explanation in stages:

        with stage_box.container():
            st.markdown(
                f"""
<div class="panel">
<div class="eyebrow">AUTONOMOUS NETWORK RESPONSE</div>
<div style="font-size:23px;font-weight:800;margin-top:3px">
{stage}
</div>
<div class="subtle" style="margin-top:5px">
{explanation}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

        packet_index = 0

        if stage in {"FAILURE", "ANALYSIS", "REROUTING", "HEALING", "HEALED", "RECOVERY FAILED"}:
            failed_text = f"{route[0]} ↔ {route[1]}" if len(route) >= 2 else "No valid route edge"
            backup_text = " → ".join(alternate_route) if alternate_route else "No viable backup route found"
            with stage_box.container():
                st.markdown(
                    f"""
<div class="panel" style="border-color:#713746;margin-top:8px">
<div class="panelhead" style="color:#ff5a70">INCIDENT REPORT · SYNTHETIC SCENARIO</div>
<div style="margin-top:8px"><b>WHERE did the network fail?</b><br>{failed_text}</div>
<div style="margin-top:8px"><b>WHY did it fail?</b><br>
The simulator injects a primary-link degradation. During FAILURE/ANALYSIS it represents this with elevated latency, 8.4% packet loss, 18.7 ms jitter and 91% utilization. These are illustrative scenario values, not live measurements or a real-world diagnosis.</div>
<div style="margin-top:8px"><b>WHAT is the solution?</b><br>
Isolate the failed link and move traffic to a route that avoids it. Candidate backup: {backup_text}.</div>
<div style="margin-top:8px"><b>Recovery status</b><br>{'Connectivity restored on the alternate route.' if stage == 'HEALED' else 'Recovery could not be completed.' if stage == 'RECOVERY FAILED' else 'Incident response in progress.'}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        if stage in {"FAILURE", "ANALYSIS"}:
            packet_index = min(1, max(0, len(route) - 1))
        elif stage in {"REROUTING", "HEALING", "HEALED"}:
            active = alternate_route or route
            packet_index = min(
                len(active) - 1,
                1 if len(active) > 1 else 0,
            )

        with network_box.container():
            st.markdown(
                """
<div class="panel">
<div class="panelhead">LIVE PACKET-FLOW SIMULATION</div>
<div class="subtle">
Nodes, links and packet movement are simulated for demonstration.
</div>
""",
                unsafe_allow_html=True,
            )

            fig = network_figure(
                route,
                alternate_route,
                graph,
                stage,
                packet_index,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"simulation_live_packet_flow_{stage}",
            )

            st.markdown(
                f"""
<div style="
border:1px solid #20394a;
background:#091925;
border-radius:7px;
padding:9px 11px;
font-size:11px;
font-weight:700;
color:#55dff2;
">
{stage} &nbsp;•&nbsp; {explanation}
</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with dashboard_box.container():
            telemetry_panel(
                metrics,
                stage,
                route,
                alternate_route,
                graph,
            )

        if stage != "HEALED":
            # This is a UI playback delay only; measured algorithm times remain separate.
            time.sleep(float(st.session_state.get("ghost_stage_delay", 0.8)))

    st.session_state.simulation_complete = True


def show_simulation_page():

    selected = st.session_state.selected_state
    source = st.session_state.source_city
    destination = st.session_state.destination_city

    st.markdown(
        f"""
<div class="eyebrow">AUTONOMOUS NETWORK OPERATIONS</div>
<div class="big-title">Network Self-Healing Simulation</div>
<div class="subtle">
{selected} · {source} → {destination}
</div>
""",
        unsafe_allow_html=True,
    )

    graph = build_state_graph(selected)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("SOURCE", source)
    c2.metric("DESTINATION", destination)
    c3.metric("ROUTING", "OSPF")
    c4.metric("TOPOLOGY", topology_name(graph))
    c5.metric("ALGORITHM", "DIJKSTRA")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if st.button(
        "← BACK TO INDIA NETWORK MAP",
        use_container_width=False,
    ):
        st.session_state.page = "selection"
        st.session_state.simulation_started = False
        st.session_state.simulation_complete = False
        st.session_state.last_click = None
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if (
        st.session_state.simulation_started
        and not st.session_state.simulation_complete
    ):
        st.markdown("#### Simulation playback")
        st.caption("Playback delay controls how long each visual stage stays on screen. It is not real network recovery time.")
        st.slider(
            "Seconds per stage",
            min_value=0.2,
            max_value=2.0,
            value=float(st.session_state.get("ghost_stage_delay", 0.8)),
            step=0.2,
            key="ghost_stage_delay",
        )
        run_automatic_simulation()

    elif st.session_state.simulation_complete:
        route = st.session_state.manual_path[:]

        if len(route) < 2:
            route, graph = calculate_route(
                source,
                destination,
                selected,
            )

        alternate_route = calculate_alternate_route(
            source,
            destination,
            selected,
            route,
        )

        metrics = route_metrics(route, graph)

        left, right = st.columns([1.75, 1], gap="small")

        with left:
            st.markdown(
                """
<div class="panelhead">NETWORK SELF-HEALING COMPLETE</div>
<div class="subtle">
The simulated failure was detected, analyzed and recovered automatically.
</div>
""",
                unsafe_allow_html=True,
            )

            fig = network_figure(
                route,
                alternate_route,
                graph,
                "HEALED",
                len(alternate_route) - 1
                if alternate_route
                else len(route) - 1,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
                key="simulation_network_restored",
            )

            st.markdown(
                f"""
<div class="success-box">
<div class="panelhead" style="color:#43e6a0">
✓ NETWORK RESTORED
</div>
<div style="margin-top:8px">
Active route:
<strong>{' → '.join(alternate_route or route)}</strong>
</div>
<div style="margin-top:8px">
The failed primary path was isolated and traffic was
successfully transferred to the alternate route.
</div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown("### Routing decision explanation")
            if len(route) >= 2:
                edge = graph.get_edge_data(route[0], route[1], default={})
                st.write(
                    f"The injected failure affects **{route[0]} → {route[1]}**. "
                    f"Its illustrative telemetry is latency **{edge.get('latency_ms', 'N/A')} ms**, "
                    f"packet loss **{edge.get('packet_loss_pct', 'N/A')}%**, "
                    f"congestion **{edge.get('congestion_pct', 'N/A')}%**, and "
                    f"reliability **{edge.get('reliability_pct', 'N/A')}%**, and "
                    f"predicted risk score **{edge.get('risk_score', 'N/A')}/100**. "
                    "The risk score is a deterministic heuristic, not a trained ML prediction. "
                    "The failed edge is excluded; the backup is chosen by the lowest remaining composite cost."
                )

            comparison = benchmark_recovery(source, destination, graph, route)
            with st.expander("BENCHMARK + REPRODUCIBLE ROUTE CHECKS", expanded=False):
                b1, b2 = st.columns(2)
                b1.metric("Measured reactive recompute", f"{comparison['reactive_ms']:.4f} ms")
                b2.metric("Measured backup switch", f"{comparison['proactive_ms']:.4f} ms")
                st.caption(f"Measured locally with perf_counter. Backup precomputation: {comparison.get('precompute_ms', 0):.4f} ms. These are simulator timings, not real network recovery latency.")
                st.write("**Failed link:**", comparison["failed_edge"])
                st.write("**Reactive route:**", " → ".join(comparison["reactive_route"]) or "No route")
                st.write("**Precomputed backup:**", " → ".join(comparison["backup_route"]) or "No route")
                if len(route) >= 2 and graph.has_edge(route[0], route[1]):
                    edge_data = graph[route[0]][route[1]]
                    # Synthetic pre-failure history; trend is evaluated before the injected failure.
                    base_c = float(edge_data.get("congestion_pct", 50))
                    base_l = float(edge_data.get("packet_loss_pct", 0.2))
                    base_t = float(edge_data.get("latency_ms", 8))
                    history = {
                        "congestion_pct": [max(0, base_c - 24), max(0, base_c - 16), max(0, base_c - 8), base_c],
                        "packet_loss_pct": [max(0, base_l - .24), max(0, base_l - .16), max(0, base_l - .08), base_l],
                        "latency_ms": [max(1, base_t - 6), max(1, base_t - 4), max(1, base_t - 2), base_t],
                    }
                    forecast = forecast_link_risk(history)
                    st.write(f"**Pre-failure trend assessment:** {forecast['trend']} · score {forecast['risk_score']}/100 · warning: {'YES' if forecast['warning'] else 'NO'}")
                    st.caption("Trend forecast uses synthetic historical samples and a transparent heuristic; it is not trained ML and must not be interpreted as real-world predictive accuracy.")
                if st.button("RUN 30 SEEDED STRESS SCENARIOS", key="run_seeded_stress_scenarios"):
                    stress = run_seeded_stress_tests(graph, source, destination, runs=30, seed=42, max_failures=3)
                    st.session_state["ghost_stress_results"] = stress
                    st.session_state["ghost_forecast_results"] = evaluate_forecast_early_warning(samples=100, seed=42)
                stress = st.session_state.get("ghost_stress_results")
                if stress:
                    st.write(f"**Seed:** {stress['seed']} · **Scenarios:** {stress['runs']} · **Recovery success:** {stress['success_rate_pct']}% · **Disconnected:** {stress.get('disconnected_scenarios', 0)}")
                    st.write(f"**Mean successful route cost:** {stress.get('mean_route_cost') if stress.get('mean_route_cost') is not None else 'N/A'} · **Mean recovery time:** {stress.get('mean_recovery_ms') if stress.get('mean_recovery_ms') is not None else 'N/A'} ms")
                    st.caption(stress['message'])
                forecast_eval = st.session_state.get("ghost_forecast_results")
                if forecast_eval:
                    st.write(f"**Pre-failure warning evaluation ({forecast_eval['samples']} synthetic cases):** precision {forecast_eval['precision_pct']}% · recall {forecast_eval['recall_pct']}% · false-alarm rate {forecast_eval['false_alarm_rate_pct']}%")
                    st.caption(f"TP {forecast_eval['tp']} · FP {forecast_eval['fp']} · TN {forecast_eval['tn']} · FN {forecast_eval['fn']}. {forecast_eval['message']} This evaluates only the synthetic generator, not real-world failure prediction.")
                checks = {
                    "Primary route connects source to destination": route_is_valid(route, graph, source, destination),
                    "Backup avoids the failed edge": bool(comparison["backup_route"]) and not any(
                        {a, b} == set(route[:2]) for a, b in zip(comparison["backup_route"], comparison["backup_route"][1:])
                    ),
                    "Backup connects source to destination": route_is_valid(comparison["backup_route"], graph.copy(), source, destination),
                    "Repeated topology is deterministic": list(build_state_graph(selected).edges(data=True)) == list(build_state_graph(selected).edges(data=True)),
                }
                for check, passed in checks.items():
                    st.write(("✓ " if passed else "✕ ") + check)

            with st.expander("SYNTHETIC DIGITAL TWIN · CASCADING FAILURE LAB", expanded=False):
                st.caption(
                    "Controllable synthetic network model inspired by an India topology. "
                    "It is not actual Indian telecom infrastructure. Network events are simulated; "
                    "algorithm execution times are measured locally. Playback delays only slow the UI; "
                    "they do not represent real-world recovery latency."
                )
                lab_a, lab_b = st.columns(2)
                with lab_a:
                    cascade_seed = st.number_input(
                        "Scenario seed", min_value=0, max_value=999999,
                        value=42, step=1, key="cascade_seed",
                    )
                with lab_b:
                    overload_limit = st.slider(
                        "Secondary-failure congestion threshold (%)",
                        min_value=70, max_value=100, value=92, step=1,
                        key="cascade_overload_limit",
                    )
                if st.button("RUN CASCADING FAILURE SCENARIO", key="run_cascade_scenario", type="primary"):
                    st.session_state["ghost_cascade_result"] = simulate_cascading_failure(
                        graph, source, destination, route,
                        seed=int(cascade_seed),
                        congestion_threshold=float(overload_limit),
                    )
                cascade = st.session_state.get("ghost_cascade_result")
                if cascade:
                    status_text = "RECOVERY VERIFIED" if cascade["recovered"] else "RECOVERY FAILED"
                    st.markdown(f"**Outcome:** {status_text}")
                    ca, cb, cc = st.columns(3)
                    ca.metric("Secondary failures", len(cascade["secondary_failures"]))
                    cb.metric("Backup precompute", f"{cascade['backup_precompute_ms']:.5f} ms")
                    cc.metric("Route switch work", f"{cascade['switch_ms']:.5f} ms")
                    st.write("**Initial failed link:**", " ↔ ".join(cascade["failed_edge"]) if cascade["failed_edge"] else "Unavailable")
                    st.write("**Final route:**", " → ".join(cascade["route"]) if cascade["route"] else "No viable route")
                    st.caption(cascade["message"])
                    timeline_rows = [
                        {
                            "Event": row["event"],
                            "Event time (simulated s)": row["simulated_time_s"],
                            "Algorithm elapsed (measured ms)": row["algorithm_elapsed_ms"],
                            "Event type": row["event_type"],
                            "Explanation": row["detail"],
                        }
                        for row in cascade["timeline"]
                    ]
                    st.markdown("#### Explainable recovery timeline")
                    st.dataframe(timeline_rows, use_container_width=True, hide_index=True)
                    st.caption(
                        "Simulated event time and measured Python algorithm time are separate clocks. "
                        "Measured milliseconds are local computation durations, not physical network recovery latency."
                    )
                    if cascade["route"]:
                        cascade_fig = network_figure(
                            cascade["route"], [], cascade["graph_after"],
                            "HEALED" if cascade["recovered"] else "RECOVERY FAILED",
                            max(0, len(cascade["route"]) - 1),
                        )
                        st.plotly_chart(
                            cascade_fig, use_container_width=True,
                            config={"displayModeBar": False},
                            key="cascade_network_twin_result",
                        )

        with right:
            telemetry_panel(
                metrics,
                "HEALED",
                route,
                alternate_route,
                graph,
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        with st.expander(
            "▸ COMPUTER NETWORK CONCEPTS USED",
            expanded=False,
        ):
            concept_cols = st.columns(2)

            concepts = [
                ("OSPF", "Open Shortest Path First — a link-state routing protocol that dynamically calculates reachable routes."),
                ("Dijkstra", "Shortest-path algorithm used here to calculate the lowest-cost reachable route."),
                ("Topology", "The arrangement of network nodes and links. This demo uses an illustrative partial-mesh topology."),
                ("Hop", "One forwarding step from one network node to another."),
                ("Latency", "Time taken for traffic to travel across the selected route."),
                ("Packet Loss", "Percentage of packets that fail to reach the destination."),
                ("Jitter", "Variation in packet arrival time."),
                ("Bandwidth", "Maximum data-carrying capacity of a network link."),
                ("Throughput", "Amount of data successfully delivered over the network."),
                ("Route Cost", "Numerical value used to compare candidate paths."),
                ("TTL", "Time To Live. Limits how long a packet can remain in a network."),
                ("Convergence", "Time required for routing state to become consistent after a topology change."),
                ("Failover", "Switching traffic from a failed primary path to an alternate path."),
                ("Redundancy", "Availability of additional paths or links for fault tolerance."),
                ("Self-Healing", "Detecting a network problem, selecting an alternate route and restoring connectivity automatically."),
            ]

            for index, (term, description) in enumerate(concepts):
                with concept_cols[index % 2]:
                    st.markdown(
                        f"""
<div class="panel" style="margin-bottom:8px">
<div style="font-weight:800;color:#55dff2">{term}</div>
<div class="subtle" style="margin-top:4px">{description}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )


# ---------------------- DATA PROVENANCE --------------------------
with st.expander("DATA PROVENANCE & REAL-DATA BOUNDARIES", expanded=False):
    supplied_links = load_real_city_links()
    st.markdown("""
**Verified vs simulated data**

- **City locations:** the application's maintained city-coordinate registry; these are location references, not evidence of telecom infrastructure.
- **Topology:** modelled geographic links by default. Explicitly sourced links can be loaded through `data/real_city_links.csv` and are accepted only when both city names match the 127-city registry.
- **Latency, packet loss, congestion, reliability, failures and recovery events:** synthetic demonstration values unless a separate measurement source is explicitly connected. The app does not currently collect live telecom telemetry.
- **Timing:** local Python algorithm execution time, not real carrier/network recovery time.

AS-level Internet datasets (for example, CAIDA) describe autonomous-system relationships; they must not be presented as direct city-to-city fibre or telecom links without a defensible mapping.
""")
    st.metric("Explicitly sourced city links loaded", len(supplied_links))
    st.caption("CSV columns: city_a, city_b, source, source_url, observed_at. Include a source URL and do not fabricate rows.")


# -------------------------- ROUTER -------------------------------

if st.session_state.page == "selection":
    show_selection_page()
else:
    if (
        not st.session_state.selected_state
        or not st.session_state.source_city
        or not st.session_state.destination_city
    ):
        st.session_state.page = "selection"
        st.rerun()

    show_simulation_page()

st.markdown(
    """
<div style="
margin-top:18px;
padding-top:9px;
border-top:1px solid #1b3544;
color:#6f8999;
font-size:9px;
letter-spacing:.08em;
">
GHOST NETWORK INDIA · RESILIENCE ANALYSIS DEMO ·
CITY LOCATIONS ARE REFERENCES; TOPOLOGY IS MODELLED UNLESS SOURCED LINKS ARE LOADED ·
TELEMETRY, FAILURES AND RECOVERY EVENTS ARE SIMULATED · NOT A LIVE NETWORK
</div>
""",
    unsafe_allow_html=True,
)
