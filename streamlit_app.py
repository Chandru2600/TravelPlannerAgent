"""
TravelPlannerAgent - Streamlit Frontend Application
IBM SkillsBuild Internship Project
"""

import os
import time
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, datetime, timedelta

# Page config
st.set_page_config(
    page_title="AI Travel Planner Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000")

# ── Custom CSS for Premium Styling ─────────────────────────────
st.markdown("""
<style>
    /* Google Font: Inter matching local main.css */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Native layout backgrounds matching light/dark theme variables of local main.css */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Brand Color Variables matching root declarations in main.css */
    :root {
        --ibm-blue:     #0062FF;
        --ibm-hover:    #0043CE;
        --ibm-dark:     #161616;
        --ibm-light:    #F4F4F4;
        --ibm-purple:   #6929C4;
        --ibm-teal:     #009D9A;
        --ibm-green:    #198038;
        --ibm-yellow:   #B28600;
        --ibm-red:      #DA1E28;
    }
    
    /* Card Panel matching .card-panel styling in main.css */
    .premium-card {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--border-color, rgba(0,0,0,0.1));
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,.04);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 20px;
    }
    
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: var(--ibm-blue);
        box-shadow: 0 8px 24px rgba(0, 98, 255, 0.15);
    }
    
    /* Title Gradient matching .text-gradient in main.css */
    .title-gradient {
        background: linear-gradient(135deg, var(--text-color) 0%, var(--ibm-blue) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: var(--text-muted, #8D8D8D);
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--ibm-blue);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: var(--text-muted, #8D8D8D);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    /* Button Custom styling matching .btn-ibm in main.css */
    div.stButton > button {
        background-color: var(--ibm-blue) !important;
        color: white !important;
        border: none !important;
        padding: 8px 24px !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 98, 255, 0.15) !important;
    }
    
    div.stButton > button:hover {
        background-color: var(--ibm-hover) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 98, 255, 0.3) !important;
    }
    
    div.stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Scrollbars styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.05);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--ibm-blue);
        border-radius: 4px;
        opacity: 0.5;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--ibm-hover);
    }
    
    /* Time Slot styling matching main.css slot borders */
    .time-slot-morn { border-left: 4px solid #F1C21B !important; }
    .time-slot-aft { border-left: 4px solid #FF832B !important; }
    .time-slot-eve { border-left: 4px solid #6929C4 !important; }
</style>
""", unsafe_allow_html=True)


# ── API Integration Helper Functions ─────────────────────────

def api_request(method, endpoint, json_data=None, headers=None, stream=False):
    """Generic backend request handler with error logging."""
    url = f"{BACKEND_URL}{endpoint}"
    
    # Merge default headers
    req_headers = {}
    if headers:
        req_headers.update(headers)
    if "token" in st.session_state and st.session_state.token:
        req_headers["Authorization"] = f"Bearer {st.session_state.token}"
        
    try:
        if method.upper() == "GET":
            res = requests.get(url, headers=req_headers, stream=stream, timeout=120)
        elif method.upper() == "POST":
            res = requests.post(url, json=json_data, headers=req_headers, timeout=120)
        elif method.upper() == "DELETE":
            res = requests.delete(url, headers=req_headers, timeout=120)
        else:
            return None
            
        return res
    except Exception as e:
        st.error(f"Failed to connect to backend server at {BACKEND_URL}. Exception: {e}")
        return None


# Geocoding & POI search functions (Local helper using free Nominatim)
@st.cache_data(show_spinner=False)
def geocode_city(city_name):
    """Retrieve latitude and longitude for a city name."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(city_name)}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent": "TravelPlannerStreamlit/1.0"}, timeout=10)
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


@st.cache_data(show_spinner=False)
def search_pois(city_name, center_lat, center_lon):
    """Search points of interest near the destination."""
    points = [{"lat": center_lat, "lon": center_lon, "name": f"📍 {city_name} (Center)", "type": "Center"}]
    poi_types = [
        {"query": "tourist attraction", "emoji": "🎯", "label": "Attraction"},
        {"query": "hotel", "emoji": "🏨", "label": "Hotel"},
        {"query": "restaurant", "emoji": "🍴", "label": "Restaurant"},
        {"query": "hospital", "emoji": "🏥", "label": "Hospital"}
    ]
    
    for item in poi_types:
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(item['query'] + ' in ' + city_name)}&format=json&limit=2"
            res = requests.get(url, headers={"User-Agent": "TravelPlannerStreamlit/1.0"}, timeout=10)
            data = res.json()
            for row in data:
                points.append({
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "name": f"{item['emoji']} {row['display_name'].split(',')[0]}",
                    "type": item["label"]
                })
            time.sleep(0.5)  # Respect nominatim policies
        except Exception:
            pass
            
    return pd.DataFrame(points)


# ── Session State Initialization ──────────────────────────────

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Welcome"
if "current_trip_id" not in st.session_state:
    st.session_state.current_trip_id = None


# ── Page Controller Functions ──────────────────────────────────

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()


# ── Render Pages ───────────────────────────────────────────────

# Page 1: Welcome & Authentication Portal
# Page 1: Welcome & Authentication Portal
def render_welcome_page():
    col1, col2 = st.columns([5, 4])
    
    with col1:
        # Hero Section matching local hero-section in home.html
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0043CE 0%, #6929C4 60%, #0062FF 100%); padding: 40px; border-radius: 16px; color: white; text-align: left; position: relative; overflow: hidden; margin-bottom: 25px; box-shadow: 0 8px 32px rgba(0,0,0,0.15);">
            <div style="display: inline-flex; align-items: center; background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.25); padding: 6px 16px; border-radius: 100px; font-size: 0.82rem; font-weight: 600; margin-bottom: 20px;">
                <span>🚀 Powered by IBM Granite AI</span>
            </div>
            <h1 style="font-size: clamp(2rem, 4vw, 3rem); font-weight: 900; line-height: 1.15; color: white; margin: 0 0 15px 0;">
                Plan Your Dream<br><span style="background: linear-gradient(135deg, #fff 0%, #b3cfff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Trip with AI</span>
            </h1>
            <p style="font-size: 1.05rem; opacity: .85; max-width: 580px; margin: 0 0 30px 0; font-weight: 300; line-height: 1.6;">
                Get personalized travel itineraries, real-time weather insights, hotel recommendations,
                and complete budget planning — all generated by IBM Granite through watsonx.ai.
            </p>
            <div style="display: inline-flex; gap: 15px; flex-wrap: wrap;">
                <div style="text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px; min-width: 90px;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #fff;">AI</div>
                    <div style="font-size: .72rem; opacity: .7; color: #fff;">Powered</div>
                </div>
                <div style="text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px; min-width: 90px;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #fff;">7+</div>
                    <div style="font-size: .72rem; opacity: .7; color: #fff;">Modules</div>
                </div>
                <div style="text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px; min-width: 90px;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #fff;">100%</div>
                    <div style="font-size: .72rem; opacity: .7; color: #fff;">Free</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Auth form matching card layout
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        auth_mode = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        # Login Form
        with auth_mode[0]:
            st.markdown("<h4 style='margin-bottom:15px; font-weight:700;'>Welcome Back!</h4>", unsafe_allow_html=True)
            login_email = st.text_input("Email Address", key="login_email_input")
            login_pwd = st.text_input("Password", type="password", key="login_pwd_input")
            
            if st.button("Log In", key="login_btn"):
                if login_email and login_pwd:
                    with st.spinner("Authenticating..."):
                        res = api_request("POST", "/api/auth/login", {"email": login_email, "password": login_pwd})
                        if res and res.status_code == 200:
                            body = res.json()
                            st.session_state.token = body.get("token")
                            st.session_state.user = body.get("user")
                            st.success(f"Logged in as {body['user']['name']}")
                            navigate_to("Dashboard")
                        else:
                            err_msg = res.json().get("error", "Invalid credentials") if res else "Connection failed"
                            st.error(err_msg)
                else:
                    st.warning("Please enter your email and password.")
                    
        # Register Form
        with auth_mode[1]:
            st.markdown("<h4 style='margin-bottom:15px; font-weight:700;'>Create an Account</h4>", unsafe_allow_html=True)
            reg_name = st.text_input("Full Name", key="reg_name_input")
            reg_email = st.text_input("Email Address", key="reg_email_input")
            reg_pwd = st.text_input("Password (Min. 8 characters)", type="password", key="reg_pwd_input")
            reg_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm_input")
            
            if st.button("Sign Up", key="signup_btn"):
                if reg_name and reg_email and reg_pwd:
                    if len(reg_pwd) < 8:
                        st.error("Password must be at least 8 characters long.")
                    elif reg_pwd != reg_pwd_confirm:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating account..."):
                            res = api_request("POST", "/api/auth/register", {
                                "name": reg_name,
                                "email": reg_email,
                                "password": reg_pwd
                            })
                            if res and res.status_code == 201:
                                body = res.json()
                                st.session_state.token = body.get("token")
                                st.session_state.user = body.get("user")
                                st.success("Account created successfully!")
                                navigate_to("Dashboard")
                            else:
                                err_msg = res.json().get("error", "Registration failed") if res else "Connection failed"
                                st.error(err_msg)
                else:
                    st.warning("Please fill in all the details.")

    # ── Features Grid Section matching home.html ──
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 35px 0 25px 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>Everything You Need for Perfect Travel</h3>", unsafe_allow_html=True)
    
    features_list = [
        ("🧠 AI Itinerary Generator", "IBM Granite creates detailed day-wise itineraries with morning, afternoon, and evening plans tailored to your style.", "#0062FF"),
        ("🌤️ Real-time Weather", "Live weather data from OpenWeatherMap with 7-day forecasts and travel-specific alerts.", "#0043CE"),
        ("🗺️ Interactive Maps", "MapLibre-powered maps showing attractions, hotels, restaurants, and transport hubs.", "#6929C4"),
        ("💰 Budget Planner", "Automatic cost breakdown across accommodation, food, transport, and activities.", "#009D9A"),
        ("🏨 Hotel Finder", "AI-curated budget, mid-range, and luxury hotel picks with pricing and amenities.", "#198038"),
        ("📄 PDF Export", "Download your complete itinerary as a professional PDF with all details.", "#B28600"),
        ("⭐ Saved Trips", "Save, edit, and manage multiple trip plans from your personal dashboard.", "#FA4D56"),
        ("🎒 Local Guide", "Food, customs, phrases, safety tips, and hidden gems — all AI generated.", "#FF832B"),
    ]
    
    for idx in range(0, len(features_list), 4):
        cols = st.columns(4)
        for j in range(4):
            if idx + j < len(features_list):
                title, desc, color = features_list[idx + j]
                with cols[j]:
                    st.markdown(f"""
                    <div class='premium-card' style='min-height: 220px; border-top: 4px solid {color};'>
                        <h5 style='margin:0 0 10px 0; color: {color}; font-weight: 700;'>{title}</h5>
                        <p style='font-size: 0.85rem; line-height: 1.5; margin: 0; color: var(--text-color);'>{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # ── How It Works Section matching home.html ──
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 35px 0 25px 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>How It Works</h3>", unsafe_allow_html=True)
    
    steps = [
        ("01", "📝 Fill the Form", "Enter destination, dates, budget, travel style, and preferences."),
        ("02", "🧠 IBM Granite Plans", "Our AI analyzes your inputs and generates a complete personalized itinerary."),
        ("03", "🗺️ Explore & Customize", "View your plan with maps, weather, hotels, and budget breakdown."),
        ("04", "✈️ Export & Go", "Download your PDF itinerary and travel with confidence.")
    ]
    
    cols_steps = st.columns(4)
    for idx, (num, title, desc) in enumerate(steps):
        with cols_steps[idx]:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px;'>
                <div style='font-size: 2.2rem; font-weight: 900; color: var(--ibm-blue); opacity: 0.15; line-height: 1;'>{num}</div>
                <h5 style='margin: 10px 0; font-weight: 700;'>{title}</h5>
                <p style='font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin: 0;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Built on IBM Technology Section matching home.html ──
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 35px 0 25px 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>Built on IBM Technology</h3>", unsafe_allow_html=True)
    
    col_tech1, col_tech2 = st.columns(2)
    with col_tech1:
        st.markdown("""
        <div class='premium-card' style='height: 100%; display: flex; flex-direction: column; justify-content: center;'>
            <h4 style='margin:0 0 12px 0; font-weight: 700;'>Enterprise-Grade Foundation</h4>
            <p style='font-size: 0.95rem; line-height: 1.6; margin: 0 0 20px 0; color: var(--text-color);'>
                This project uses <strong>IBM Granite</strong> — IBM's enterprise-grade foundation model —
                accessed through <strong>IBM watsonx.ai</strong> on <strong>IBM Cloud Lite</strong>.
            </p>
            <div style='display: flex; gap: 8px; flex-wrap: wrap;'>
                <span style='background: var(--ibm-blue); color: white; padding: 4px 12px; border-radius: 100px; font-size: 0.8rem; font-weight: 600;'>🧠 IBM Granite 13B</span>
                <span style='background: var(--ibm-blue); color: white; padding: 4px 12px; border-radius: 100px; font-size: 0.8rem; font-weight: 600;'>☁️ IBM watsonx.ai</span>
                <span style='background: var(--ibm-blue); color: white; padding: 4px 12px; border-radius: 100px; font-size: 0.8rem; font-weight: 600;'>🛡️ IBM Cloud Lite</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_tech2:
        st.markdown("""
        <div style='background: #1C1C1C; border-radius: 12px; overflow: hidden; font-family: monospace; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 16px rgba(0,0,0,0.2);'>
            <div style='background: #2D2D2D; padding: 10px 16px; display: flex; align-items: center; gap: 6px;'>
                <span style='width: 12px; height: 12px; border-radius: 50%; display: inline-block; background: #FF5F57;'></span>
                <span style='width: 12px; height: 12px; border-radius: 50%; display: inline-block; background: #FFBD2E;'></span>
                <span style='width: 12px; height: 12px; border-radius: 50%; display: inline-block; background: #28CA41;'></span>
                <span style='margin-left: 8px; color: #8D8D8D; font-size: 0.8rem;'>granite_service.py</span>
            </div>
            <div style='padding: 20px; margin: 0; color: #ABB2BF; font-size: 0.8rem; line-height: 1.6; overflow-x: auto;'>
                <span style="color: #5C6370;"># IBM Granite via watsonx.ai</span><br>
                <span style="color: #C678DD;">def</span> <span style="color: #61AFEF;">call_granite</span>(prompt):<br>
                &nbsp;&nbsp;&nbsp;&nbsp;token = <span style="color: #61AFEF;">get_ibm_iam_token</span>()<br>
                &nbsp;&nbsp;&nbsp;&nbsp;payload = {<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #98C379;">"model_id"</span>: <span style="color: #98C379;">"ibm/granite-13b-instruct-v2"</span>,<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #98C379;">"input"</span>: prompt,<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #98C379;">"parameters"</span>: {<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #98C379;">"max_new_tokens"</span>: <span style="color: #D19A66;">2000</span><br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}<br>
                &nbsp;&nbsp;&nbsp;&nbsp;}<br>
                &nbsp;&nbsp;&nbsp;&nbsp;response = requests.<span style="color: #61AFEF;">post</span>(<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;watsonx_url, headers=auth_headers, json=payload<br>
                &nbsp;&nbsp;&nbsp;&nbsp;)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #C678DD;">return</span> response[<span style="color: #98C379;">"results"</span>][<span style="color: #D19A66;">0</span>][<span style="color: #98C379;">"generated_text"</span>]
            </div>
        </div>
        """, unsafe_allow_html=True)


# Page 2: User Dashboard
def render_dashboard_page():
    st.markdown(f"<div class='title-gradient'>Welcome, {st.session_state.user['name']}!</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Manage your itineraries, track stats, and create new journeys.</div>", unsafe_allow_html=True)
    
    # Fetch user trips
    with st.spinner("Fetching dashboard stats..."):
        res = api_request("GET", "/api/trips")
        trips = res.json() if (res and res.status_code == 200) else []
        
        res_saved = api_request("GET", "/api/saved-trips")
        saved_trips = res_saved.json() if (res_saved and res_saved.status_code == 200) else []

    # Display Stats Grid
    total_trips = len(trips)
    total_saved = len(saved_trips)
    completed_trips = sum(1 for t in trips if t.get("status") == "completed")
    total_budget_spent = sum(t.get("budget", 0) for t in trips)
    
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>📂 Total Itineraries</div>
            <div class='metric-val'>{total_trips}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>❤️ Saved Plans</div>
            <div class='metric-val'>{total_saved}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>✅ Completed Trips</div>
            <div class='metric-val'>{completed_trips}</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol4:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>💰 Total Budget Pool</div>
            <div class='metric-val'>${total_budget_spent:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<h3 style='margin-top:20px; margin-bottom:15px;'>📋 Recent Itineraries</h3>", unsafe_allow_html=True)
    
    if not trips:
        st.info("You haven't planned any trips yet! Click on the 'Plan New Trip' button in the sidebar to start.")
        if st.button("🚀 Plan Your First Trip"):
            navigate_to("Plan New Trip")
    else:
        # Create a beautiful grid of trips
        for i in range(0, len(trips), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(trips):
                    trip = trips[i + j]
                    with cols[j]:
                        badge_color = "#10B981" if trip.get("status") == "completed" else "#6B7280"
                        st.markdown(f"""
                        <div class='premium-card' style='min-height: 230px; display: flex; flex-direction: column; justify-content: space-between;'>
                            <div>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <h4 style='margin:0; font-size:1.3rem; color:#F8FAFC;'>✈️ {trip['destination']}</h4>
                                    <span style='background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; text-transform: uppercase; font-weight: bold;'>
                                        {trip.get('status', 'draft')}
                                    </span>
                                </div>
                                <p style='color:#94A3B8; margin-top:8px; font-size:0.9rem;'>
                                    📅 {trip['start_date']} to {trip['end_date']} ({trip['num_days']} Days)<br>
                                    💵 Budget: <b>${trip['budget']:,}</b> | 👥 Travelers: <b>{trip['num_travelers']}</b><br>
                                    🎒 Style: <b>{trip['travel_style'].title()}</b>
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("👁️ View Details", key=f"view_trip_{trip['id']}"):
                                st.session_state.current_trip_id = trip["id"]
                                navigate_to("View Trip")
                        with btn_col2:
                            if st.button("🗑️ Delete", key=f"del_trip_{trip['id']}"):
                                with st.spinner("Deleting..."):
                                    res_del = api_request("DELETE", f"/api/trips/{trip['id']}")
                                    if res_del and res_del.status_code == 200:
                                        st.toast("Trip deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete trip.")


# Page 3: Plan New Trip
def render_planner_page():
    st.markdown("<div class='title-gradient'>Plan a New Trip</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Configure your destination details and let IBM Granite handle the rest.</div>", unsafe_allow_html=True)
    
    with st.form("new_trip_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input("Destination City / Country", placeholder="e.g. Tokyo, Japan", help="Enter the destination name.")
            start_date = st.date_input("Start Date", date.today())
            end_date = st.date_input("End Date", date.today() + timedelta(days=4))
            
            # Constraints validations
            num_days = (end_date - start_date).days
            if num_days <= 0:
                num_days = 1
            st.markdown(f"**Trip Duration**: {num_days} Day(s)")
            
            budget = st.number_input("Total Budget (USD)", min_value=100, max_value=100000, value=1500, step=100)
            
        with col2:
            num_travelers = st.number_input("Number of Travelers", min_value=1, max_value=20, value=1)
            travel_style = st.selectbox("Travel Style", ["budget", "mid-range", "luxury"], index=0)
            transport = st.selectbox("Primary Transportation", ["flight", "train", "bus", "car", "cruise"], index=0)
            
            interests = st.multiselect(
                "Interests & Themes",
                ["Adventure", "Culture & History", "Food & Dining", "Nature & Wildlife", "Shopping", "Relaxation", "Family-friendly", "Nightlife"],
                default=["Culture & History", "Food & Dining"]
            )
            
            special_requirements = st.multiselect(
                "Special Accommodations",
                ["Vegetarian/Vegan Food", "Wheelchair Accessibility", "Kid-friendly Activities", "Senior-citizen Friendly", "Pet-friendly"],
                default=[]
            )
            
        submit_button = st.form_submit_button("🔮 Generate AI Trip Plan")
        
        if submit_button:
            if not destination.strip():
                st.error("Please specify a travel destination.")
            else:
                progress_container = st.container()
                with progress_container:
                    with st.spinner("Connecting to watsonx.ai & invoking IBM Granite instruct models... (this takes ~15 seconds)"):
                        trip_data = {
                            "destination": destination,
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "num_days": num_days,
                            "budget": budget,
                            "num_travelers": num_travelers,
                            "travel_style": travel_style,
                            "transport": transport,
                            "interests": interests,
                            "special_requirements": special_requirements
                        }
                        
                        res = api_request("POST", "/api/trips", trip_data)
                        if res and res.status_code == 201:
                            new_trip_id = res.json().get("trip_id")
                            st.success("Itinerary generated successfully!")
                            time.sleep(1)
                            st.session_state.current_trip_id = new_trip_id
                            navigate_to("View Trip")
                        else:
                            st.error(res.json().get("error", "Error creating itinerary.") if res else "Server connection failed.")


# Page 4: Detailed Trip View
def render_trip_view_page():
    trip_id = st.session_state.current_trip_id
    if not trip_id:
        st.warning("No trip selected.")
        if st.button("Go to Dashboard"):
            navigate_to("Dashboard")
        return
        
    with st.spinner("Fetching trip details..."):
        res = api_request("GET", f"/api/trips/{trip_id}")
        if not res or res.status_code != 200:
            st.error("Failed to retrieve trip records.")
            return
        
        data = res.json()
        trip = data.get("trip", {})
        itinerary = data.get("itinerary", {})
        weather = data.get("weather", {})
        budget = data.get("budget", {})
        hotels = data.get("hotels", {})
        expenses = data.get("expenses", [])
        
    destination = trip.get("destination", "")
    
    # Itinerary Hero matching .itinerary-hero in main.css
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #0043CE 0%, #6929C4 100%); border-radius: 16px; padding: 32px; color: #fff; margin-bottom: 20px;'>
        <div style='display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 14px;'>
            <span style='background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.25); border-radius: 100px; padding: 4px 12px; font-size: .8rem; color: #fff;'>✈️ {trip.get('travel_style', '').title()} Style</span>
            <span style='background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.25); border-radius: 100px; padding: 4px 12px; font-size: .8rem; color: #fff;'>📅 {trip.get('num_days', '')} Days</span>
            <span style='background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.25); border-radius: 100px; padding: 4px 12px; font-size: .8rem; color: #fff;'>💰 ${trip.get('budget', 0):,} Budget</span>
            <span style='background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.25); border-radius: 100px; padding: 4px 12px; font-size: .8rem; color: #fff;'>👥 {trip.get('num_travelers', 1)} Travelers</span>
        </div>
        <h1 style='font-size: clamp(1.5rem, 4vw, 2.2rem); font-weight: 900; color: #fff; margin: 0 0 8px 0;'>📍 {destination}</h1>
        <p style='font-size: 0.92rem; opacity: 0.85; margin: 0;'>{trip.get('start_date', '')} → {trip.get('end_date', '')} &nbsp;|&nbsp; Generated by IBM Granite AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Control Actions Header bar
    col_act1, col_act2, col_act3, col_act4 = st.columns([2, 2, 2, 4])
    with col_act1:
        if st.button("⬅️ Back to Dashboard", key="back_dash_btn"):
            navigate_to("Dashboard")
    with col_act2:
        # Check if already saved
        res_saved = api_request("GET", "/api/saved-trips")
        saved_list = res_saved.json() if (res_saved and res_saved.status_code == 200) else []
        is_saved = any(item["trip_id"] == trip_id for item in saved_list)
        
        if is_saved:
            st.info("❤️ Saved to Favorites")
        else:
            if st.button("⭐ Save to Favorites", key="save_fav_btn"):
                res_save = api_request("POST", f"/api/trips/{trip_id}/save", {"notes": "Generated by Streamlit"})
                if res_save and res_save.status_code == 200:
                    st.toast("Trip saved to favorites!")
                    st.rerun()
                else:
                    st.error("Failed to save trip.")
    with col_act3:
        # PDF Download Button
        pdf_res = api_request("GET", f"/api/trips/{trip_id}/pdf", stream=True)
        if pdf_res and pdf_res.status_code == 200:
            st.download_button(
                label="📄 Download PDF Plan",
                data=pdf_res.content,
                file_name=f"TravelPlan_{destination.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        else:
            st.button("📄 PDF Generation Unavailable", disabled=True)
            
    st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'/>", unsafe_allow_html=True)
    
    # ── Master Tab System ──────────────────────────────────────────
    t_itinerary, t_hotels, t_transport, t_budget, t_weather, t_map, t_local = st.tabs([
        "📅 Day Itinerary", "🏨 Hotel Guide", "🚌 Transport Guide", 
        "💰 Budget & Expenses", "🌤️ Weather Forecast", "🗺️ Points of Interest", "ℹ️ Local Info & Safety"
    ])
    
    # Tab 1: Day Itinerary
    with t_itinerary:
        st.markdown(f"### 🗺️ Day-wise Itinerary for {destination}")
        st.write(f"*{itinerary.get('trip_summary', '')}*")
        
        days_list = itinerary.get("days", [])
        if not days_list:
            st.info("No day details generated.")
        else:
            for day in days_list:
                with st.expander(f"📅 **Day {day.get('day')} - {day.get('theme', 'Exploring')} ({day.get('date', '')})**"):
                    dcol1, dcol2, dcol3 = st.columns(3)
                    
                    # Safe dictionary key retrieval to prevent KeyError on old or malformed database entries
                    morning = day.get("morning") or {}
                    afternoon = day.get("afternoon") or {}
                    evening = day.get("evening") or {}
                    
                    m_place = morning.get("place", "")
                    m_activity = morning.get("activity", "")
                    m_duration = morning.get("duration", "")
                    m_fee = morning.get("entry_fee", "")
                    
                    a_place = afternoon.get("place", "")
                    a_activity = afternoon.get("activity", "")
                    a_duration = afternoon.get("duration", "")
                    a_fee = afternoon.get("entry_fee", "")
                    
                    e_place = evening.get("place", "")
                    e_activity = evening.get("activity", "")
                    e_duration = evening.get("duration", "")
                    e_fee = evening.get("entry_fee", "")
                    
                    with dcol1:
                        st.markdown(f"""
                        <div style='background: var(--secondary-background-color); border: 1px solid var(--border-color, rgba(0,0,0,0.1)); border-top: 3px solid #F1C21B; border-radius: 6px; padding: 14px; margin-bottom: 10px;'>
                            <div style='font-size: .78rem; font-weight: 700; text-transform: uppercase; color: #8D8D8D; margin-bottom: 6px;'>🌅 Morning</div>
                            <div style='font-size: 0.92rem;'>
                                <b>Place:</b> {m_place}<br>
                                <b>Activity:</b> {m_activity}<br>
                                <small style='color:#8D8D8D;'>⏱️ {m_duration} &nbsp;|&nbsp; 🎫 {m_fee}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with dcol2:
                        st.markdown(f"""
                        <div style='background: var(--secondary-background-color); border: 1px solid var(--border-color, rgba(0,0,0,0.1)); border-top: 3px solid #FF832B; border-radius: 6px; padding: 14px; margin-bottom: 10px;'>
                            <div style='font-size: .78rem; font-weight: 700; text-transform: uppercase; color: #8D8D8D; margin-bottom: 6px;'>☀️ Afternoon</div>
                            <div style='font-size: 0.92rem;'>
                                <b>Place:</b> {a_place}<br>
                                <b>Activity:</b> {a_activity}<br>
                                <small style='color:#8D8D8D;'>⏱️ {a_duration} &nbsp;|&nbsp; 🎫 {a_fee}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with dcol3:
                        st.markdown(f"""
                        <div style='background: var(--secondary-background-color); border: 1px solid var(--border-color, rgba(0,0,0,0.1)); border-top: 3px solid #6929C4; border-radius: 6px; padding: 14px; margin-bottom: 10px;'>
                            <div style='font-size: .78rem; font-weight: 700; text-transform: uppercase; color: #8D8D8D; margin-bottom: 6px;'>🌙 Evening</div>
                            <div style='font-size: 0.92rem;'>
                                <b>Place:</b> {e_place}<br>
                                <b>Activity:</b> {e_activity}<br>
                                <small style='color:#8D8D8D;'>⏱️ {e_duration} &nbsp;|&nbsp; 🎫 {e_fee}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("##### 🍽️ Food Recommendations")
                    for food in day.get("food_recommendations", []):
                        st.write(f"- **{food.get('meal', 'Lunch/Dinner')}**: {food.get('restaurant', '')} (Cuisine: *{food.get('cuisine', '')}* | Price Range: *{food.get('price_range', '')}*)")
                        
                    fcol1, fcol2 = st.columns(2)
                    with fcol1:
                        st.markdown(f"💡 **Local Tips**: {day.get('local_tips', '')}")
                    with fcol2:
                        gems = ", ".join(day.get("hidden_gems", []))
                        st.markdown(f"💎 **Hidden Gems**: {gems}")

    # Tab 2: Hotels
    with t_hotels:
        st.markdown("### 🏨 Recommended Accommodations")
        st.write(f"📍 *Recommended Area:* {hotels.get('recommended_area', 'City Centre')}")
        st.write(f"💡 *Booking Advice:* {hotels.get('booking_advice', '')}")
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Display hotels categorised
        for cat_name, key in [("Budget Accommodations", "budget_hotels"), ("Mid-Range Hotels", "mid_range_hotels"), ("Luxury Hotels", "luxury_hotels")]:
            st.markdown(f"#### 💳 {cat_name}")
            h_list = hotels.get(key, [])
            if not h_list:
                st.write("No recommendations generated for this category.")
            else:
                hcols = st.columns(len(h_list))
                for idx, h_item in enumerate(h_list):
                    with hcols[idx]:
                        amenities = ", ".join(h_item.get("amenities", []))
                        pros = ", ".join(h_item.get("pros", []))
                        cons = ", ".join(h_item.get("cons", []))
                        
                        st.markdown(f"""
                        <div class='premium-card' style='min-height: 280px;'>
                            <h5 style='margin:0 0 8px 0; font-size:1.05rem; font-weight:700; color:#0062FF;'>🏨 {h_item.get('name', 'Hotel')}</h5>
                            <hr style='margin: 8px 0;'/>
                            <p style='font-size:0.88rem; margin-bottom:5px;'>
                                💰 <b>Price:</b> ${h_item.get('price_per_night', 0)}/night<br>
                                ⭐ <b>Rating:</b> {h_item.get('rating', 'N/A')}/5<br>
                                🗺️ <b>Distance:</b> {h_item.get('distance_from_center', 'N/A')}
                            </p>
                            <p style='font-size:0.83rem; color:#525252; margin-bottom:5px;'>
                                ✨ <b>Amenities:</b> {amenities}<br>
                                👍 <b>Pros:</b> {pros}<br>
                                👎 <b>Cons:</b> {cons}
                            </p>
                            <div style='background: rgba(0,98,255,.05); border: 1px solid rgba(0,98,255,.2); font-size:0.8rem; padding:8px 10px; border-radius:6px; color:inherit;'>
                                🏷️ <b>Tip:</b> {h_item.get('booking_tip', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)

    # Tab 3: Transport Guide
    with t_transport:
        st.markdown("### 🚌 Transport Guide")
        transport_data = data.get("transport", {})
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("#### ✈️ Getting to Destination")
            to_dest = transport_data.get("to_destination", [])
            for mode in to_dest:
                st.markdown(f"""
                <div class='premium-card'>
                    <h5 style='margin:0 0 8px 0; font-weight:700; color:#0062FF;'>🚀 {mode.get('mode', 'Carrier')}</h5>
                    <p style='font-size:0.88rem; margin-bottom:4px;'>
                        💵 <b>Cost:</b> ${mode.get('estimated_cost', 0)} &nbsp;|&nbsp; ⏱️ <b>Duration:</b> {mode.get('duration', '')}<br>
                        🔄 <b>Frequency:</b> {mode.get('frequency', '')}
                    </p>
                    <p style='font-size:0.83rem; color:#525252; margin-bottom:5px;'>
                        ➕ <b>Pros:</b> {", ".join(mode.get('pros', []))}<br>
                        ➖ <b>Cons:</b> {", ".join(mode.get('cons', []))}
                    </p>
                    <div style='background:rgba(0,98,255,.05); border: 1px solid rgba(0,98,255,.15); border-radius:6px; padding: 6px 10px; font-size:0.8rem;'>💡 {mode.get('booking_tip', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with col_t2:
            st.markdown("#### 🚕 Local Transportation")
            local_t = transport_data.get("local_transport", [])
            for mode in local_t:
                st.markdown(f"""
                <div class='premium-card'>
                    <h5 style='margin:0 0 8px 0; font-weight:700; color:#6929C4;'>🚕 {mode.get('mode', 'Public transport')}</h5>
                    <p style='font-size:0.88rem; margin-bottom:4px;'>
                        💵 <b>Cost:</b> {mode.get('cost_range', '')} &nbsp;|&nbsp; ⏰ <b>Availability:</b> {mode.get('availability', '')}<br>
                        🎯 <b>For:</b> {mode.get('recommended_for', '')}
                    </p>
                    <small style='color:#525252;'>📱 <b>App/Service:</b> {mode.get('app_or_service', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("#### 💡 Travel Navigation Tips")
        for tip in transport_data.get("navigation_tips", []):
            st.write(f"- {tip}")
            
        st.markdown("#### ⚠️ Local Scam Alerts")
        for alert in transport_data.get("scam_alerts", []):
            st.write(f"- 🔴 {alert}")

    # Tab 4: Budget & Expenses
    with t_budget:
        st.markdown("### 💰 Budget & Expense Tracker")
        
        # Budget analysis charts
        if not budget or "breakdown" not in budget:
            st.info("No budget breakdown details found.")
        else:
            b_breakdown = budget["breakdown"]
            
            # Map database keys to visual labels
            labels = []
            values = []
            for key, val in b_breakdown.items():
                labels.append(key.replace("_", " ").title())
                values.append(val.get("amount", 0))
                
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.5,
                marker=dict(colors=["#0062FF","#6929C4","#009D9A","#198038","#B28600","#FA4D56","#FF832B"])
            )])
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=10, b=10, l=10, r=10),
                height=350
            )
            
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                st.markdown("#### 📊 Budgeted Allocations")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_b2:
                st.markdown("#### 📑 Budget Breakdown Table")
                df_budget = pd.DataFrame([
                    {"Category": k.replace("_", " ").title(), "Amount (USD)": f"${v['amount']:,}", "Percentage": f"{v['percentage']}%", "Details": v["details"]}
                    for k, v in b_breakdown.items()
                ])
                st.dataframe(df_budget, use_container_width=True, hide_index=True)
                
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)
            
            # Expense Tracker Section
            st.markdown("#### 🧮 Expense Logging & Actual Tracking")
            
            col_e1, col_e2 = st.columns([1, 2])
            
            with col_e1:
                st.markdown("##### 💵 Log an Expense")
                with st.form("add_expense_form"):
                    exp_cat = st.selectbox("Category", [
                        "accommodation", "food", "transportation", "activities_tickets", "shopping", "emergency_fund", "miscellaneous"
                    ])
                    exp_amount = st.number_input("Amount (USD)", min_value=1.0, value=20.0, step=5.0)
                    exp_desc = st.text_input("Description/Merchant", placeholder="e.g. Starbucks, Hotel booking")
                    
                    exp_submit = st.form_submit_button("➕ Log Expense")
                    if exp_submit:
                        res_exp = api_request("POST", f"/api/trips/{trip_id}/expenses", {
                            "category": exp_cat,
                            "amount": exp_amount,
                            "description": exp_desc
                        })
                        if res_exp and res_exp.status_code == 200:
                            st.toast("Expense logged successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to log expense.")
                            
            with col_e2:
                st.markdown("##### 📈 Budget vs Actual Spending")
                
                # Calculate actuals vs budget
                budget_map = {k: v.get("amount", 0) for k, v in b_breakdown.items()}
                actual_map = {k: 0.0 for k in budget_map.keys()}
                
                for exp in expenses:
                    cat = exp.get("category", "miscellaneous")
                    if cat in actual_map:
                        actual_map[cat] += exp.get("amount", 0)
                    else:
                        actual_map["miscellaneous"] = actual_map.get("miscellaneous", 0) + exp.get("amount", 0)
                        
                categories = [k.replace("_", " ").title() for k in budget_map.keys()]
                budget_vals = list(budget_map.values())
                actual_vals = [actual_map[k] for k in budget_map.keys()]
                
                fig_bar = go.Figure(data=[
                    go.Bar(name='Budgeted', x=categories, y=budget_vals, marker_color='#0062FF'),
                    go.Bar(name='Spent Actual', x=categories, y=actual_vals, marker_color='#FA4D56')
                ])
                fig_bar.update_layout(
                    barmode='group',
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif"),
                    margin=dict(t=20, b=20, l=10, r=10),
                    height=300
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
                total_spent = sum(actual_vals)
                remaining = trip["budget"] - total_spent
                
                rem_col1, rem_col2 = st.columns(2)
                with rem_col1:
                    st.metric("Total Spent", f"${total_spent:,.2f}")
                with rem_col2:
                    st.metric("Remaining Balance", f"${remaining:,.2f}", delta=f"{remaining:,.2f}")

    # Tab 5: Weather Forecast
    with t_weather:
        st.markdown(f"### 🌤️ Weather Forecast for {destination}")
        
        current_w = weather.get("current", {})
        forecast_w = weather.get("forecast", [])
        
        if not current_w:
            st.info("Weather data currently unavailable.")
        else:
            wcol1, wcol2, wcol3 = st.columns(3)
            
            with wcol1:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #0062FF 0%, #0043CE 100%); border-radius: 12px; padding: 24px; color: #fff; text-align: center; box-shadow: 0 4px 16px rgba(0,98,255,0.2);'>
                    <div style='font-size: 2.8rem;'>🌤️</div>
                    <div style='font-size: 0.8rem; opacity: 0.8; margin: 6px 0 4px 0; font-weight: 600; text-transform: uppercase; letter-spacing: .05em;'>Current Temp</div>
                    <div style='font-size: 2.4rem; font-weight: 800;'>{current_w.get('temp', 'N/A')}°C</div>
                    <div style='font-size: 0.88rem; opacity: 0.8; margin-top: 4px;'>Feels like {current_w.get('feels_like', 'N/A')}°C</div>
                </div>
                """, unsafe_allow_html=True)
                
            with wcol2:
                st.markdown(f"""
                <div class='premium-card' style='text-align: center; height: 100%;'>
                    <div style='font-size: 2.8rem;'>💧</div>
                    <div style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color:#8D8D8D; margin: 6px 0 10px 0;'>Humidity & Wind</div>
                    <p style='font-size: 0.95rem; margin: 0;'>
                        <b>Humidity:</b> {current_w.get('humidity', 'N/A')}%<br>
                        <b>Wind:</b> {current_w.get('wind_speed', 'N/A')} m/s<br>
                        <b>Condition:</b> {current_w.get('description', '').title()}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
            with wcol3:
                # Advice
                advice = weather.get("alerts", "Pack comfortable clothes depending on the weather conditions.")
                st.markdown(f"""
                <div class='premium-card' style='text-align: center; height:100%;'>
                    <div style='font-size: 2.8rem;'>🎒</div>
                    <div style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color:#8D8D8D; margin: 6px 0 10px 0;'>AI Packing Advice</div>
                    <p style='font-size:0.88rem; line-height: 1.5; margin: 0;'>{advice}</p>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### 📅 7-Day Forecast")
            if not forecast_w:
                st.write("Forecast data unavailable.")
            else:
                fcols = st.columns(len(forecast_w))
                for idx, day_f in enumerate(forecast_w):
                    with fcols[idx]:
                        # Format Date
                        f_date_str = day_f.get("date", "")
                        try:
                            f_date_obj = datetime.strptime(f_date_str, "%Y-%m-%d")
                            display_date = f_date_obj.strftime("%a, %b %d")
                        except Exception:
                            display_date = f_date_str
                            
                        st.markdown(f"""
                        <div class='premium-card' style='text-align: center; padding: 12px; min-height: 165px;'>
                            <small style='color:#8D8D8D; font-size:0.75rem;'>{display_date}</small>
                            <div style='font-size: 1.7rem; margin: 8px 0;'>🌦️</div>
                            <div style='font-size:1.05rem; font-weight: 800; color:#0062FF;'>{day_f.get('temp', 'N/A')}°C</div>
                            <p style='font-size:0.72rem; color:#525252; margin-top:5px; line-height:1.3;'>{day_f.get('description', '').title()}</p>
                        </div>
                        """, unsafe_allow_html=True)

    # Tab 6: Points of Interest / Map
    with t_map:
        st.markdown(f"### 🗺️ Interactive Maps & POI Geocoding")
        st.write("Plotting points of interest retrieved automatically from OpenStreetMap coordinates.")
        
        # Run Nominatim geocoding on Python side
        with st.spinner("Geocoding points of interest..."):
            lat, lon = geocode_city(destination)
            if lat is None:
                st.warning(f"Unable to geocode coordinates for '{destination}'. Point mapping disabled.")
            else:
                pois_df = search_pois(destination, lat, lon)
                
                # Render Streamlit Map
                st.map(pois_df, latitude="lat", longitude="lon", color="#0062ff", size=45)
                
                # Show POI Listing
                st.markdown("#### 🎯 Geocoded Locations List")
                for _, p_row in pois_df.iterrows():
                    st.write(f"- **{p_row['name']}** ({p_row['type']}) — *Lat: {p_row['lat']:.4f}, Lon: {p_row['lon']:.4f}*")

    # Tab 7: Local Info & Safety
    with t_local:
        st.markdown("### ℹ️ Local Insights & Safety Guidelines")
        
        lcol1, lcol2 = st.columns(2)
        with lcol1:
            st.markdown("#### 🚨 Emergency Numbers")
            nums = itinerary.get("emergency_numbers", {"police": "100", "ambulance": "108", "tourist_helpline": "1363"})
            st.write(f"- 📞 **Police:** {nums.get('police')}")
            st.write(f"- 📞 **Ambulance:** {nums.get('ambulance')}")
            st.write(f"- 📞 **Tourist Helpline:** {nums.get('tourist_helpline')}")
            
            st.markdown("#### 💼 Essential Packing List")
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.write("**Clothes**:")
                for item in itinerary.get("clothes", ["Comfortable walking shoes"]):
                    st.write(f"- {item}")
                st.write("**Documents**:")
                for item in itinerary.get("documents", ["Passport", "ID", "Tickets"]):
                    st.write(f"- {item}")
            with pcol2:
                st.write("**Electronics**:")
                for item in itinerary.get("electronics", ["Phone charger"]):
                    st.write(f"- {item}")
                st.write("**Medicines**:")
                for item in itinerary.get("medicines", ["Pain relief"]):
                    st.write(f"- {item}")
                    
        with lcol2:
            st.markdown("#### 🔤 Useful Phrases")
            phrases = itinerary.get("useful_phrases", [])
            if not phrases:
                st.write("- Hello: *Namaste*")
                st.write("- Thank you: *Dhanyavaad*")
            else:
                for phrase in phrases:
                    st.write(f"- **{phrase.get('phrase')}**: *{phrase.get('local')}* (Pronunciation: {phrase.get('pronunciation')})")
                    
            st.markdown("#### 🏺 Local Customs")
            customs = itinerary.get("local_customs", [])
            for c_item in customs:
                st.write(f"- {c_item}")
                
            st.markdown("#### 🛍️ Shopping & Souvenirs Guide")
            shop = itinerary.get("shopping_guide", {})
            if shop:
                st.write(f"- **Popular Markets:** {', '.join(shop.get('markets', []))}")
                st.write(f"- **Best Souvenirs:** {', '.join(shop.get('souvenirs', []))}")
                st.write(f"- **Negotiation Rule:** {shop.get('price_negotiation', '')}")


# Page 5: Saved Trips / Favorites
def render_saved_trips_page():
    st.markdown("<h2 style='font-weight:800; margin-bottom:4px;'>⭐ Saved Trips</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8D8D8D; margin-bottom:24px;'>Access your favorite travel planners and read custom log notes.</p>", unsafe_allow_html=True)
    
    with st.spinner("Fetching favorites..."):
        res = api_request("GET", "/api/saved-trips")
        saved = res.json() if (res and res.status_code == 200) else []
        
    if not saved:
        st.info("You haven't saved any travel plans yet. Plan a trip first and save it to favorites!")
    else:
        for idx, s_item in enumerate(saved):
            with st.container():
                st.markdown(f"""
                <div class='premium-card'>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;'>
                        <div>
                            <h4 style='margin:0 0 4px 0; font-weight:700; color:#0062FF;'>✈️ {s_item['destination']}</h4>
                            <span style='background: rgba(0,98,255,.08); border: 1px solid rgba(0,98,255,.2); border-radius: 100px; padding: 2px 10px; font-size: .78rem; color:#0062FF; font-weight:600;'>{s_item.get('travel_style','').title()} Style</span>
                        </div>
                        <small style='color:#8D8D8D;'>Saved {s_item['saved_at'][:10]}</small>
                    </div>
                    <p style='margin-top:12px; font-size:0.9rem; line-height:1.5;'>
                        📝 <b>Notes:</b> {s_item.get('notes') or 'No custom notes.'}<br>
                        💰 <b>Budget:</b> ${s_item.get('budget', 0):,}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 2, 8])
                with col1:
                    if st.button("👁️ View Itinerary", key=f"view_saved_{s_item['trip_id']}"):
                        st.session_state.current_trip_id = s_item["trip_id"]
                        navigate_to("View Trip")
                with col2:
                    if st.button("❌ Remove Favorite", key=f"unsave_{s_item['saved_id']}"):
                        res_rem = api_request("DELETE", f"/api/saved-trips/{s_item['saved_id']}")
                        if res_rem and res_rem.status_code == 200:
                            st.toast("Removed from favorites.")
                            st.rerun()
                        else:
                            st.error("Failed to remove saved trip.")
                st.markdown("<br/>", unsafe_allow_html=True)


# Page 6: Admin Dashboard
def render_admin_page():
    st.markdown("<div class='title-gradient'>Administrator Panel</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>System analytics, platform usage metrics, and user management.</div>", unsafe_allow_html=True)
    
    with st.spinner("Fetching admin stats..."):
        res_an = api_request("GET", "/api/admin/analytics")
        analytics = res_an.json() if (res_an and res_an.status_code == 200) else {}
        
        res_usr = api_request("GET", "/api/admin/users")
        users = res_usr.json() if (res_usr and res_usr.status_code == 200) else []
        
    if not analytics:
        st.error("Admin credentials authorization failed.")
        return
        
    # Stats metrics
    acol1, acol2 = st.columns(2)
    with acol1:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>👥 Total Registered Users</div>
            <div class='metric-val'>{analytics.get('users', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with acol2:
        st.markdown(f"""
        <div class='premium-card' style='text-align: center;'>
            <div class='metric-label'>📂 Total System Trips</div>
            <div class='metric-val'>{analytics.get('trips', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    col_g1, col_g2 = st.columns([3, 2])
    with col_g1:
        st.markdown("#### 👥 User Management Directory")
        df_users = pd.DataFrame(users)
        if not df_users.empty:
            # Display user records
            st.dataframe(
                df_users[["id", "name", "email", "role", "created_at", "last_login"]], 
                use_container_width=True, 
                hide_index=True
            )
            
            # Simple Delete User Form
            with st.expander("⚠️ Remove a User Account"):
                del_user_id = st.number_input("Enter User ID to delete", min_value=1, step=1)
                if st.button("Delete User Account"):
                    res_del = api_request("DELETE", f"/api/admin/users/{del_user_id}")
                    if res_del and res_del.status_code == 200:
                        st.toast("User deleted successfully!")
                        st.rerun()
                    else:
                        st.error(res_del.json().get("error", "Error deleting user.") if res_del else "Server connection error.")
        else:
            st.write("No users registered.")
            
    with col_g2:
        st.markdown("#### 🗺️ Top Planned Destinations")
        top_dest = analytics.get("top_destinations", [])
        if not top_dest:
            st.write("No trip data found.")
        else:
            df_dest = pd.DataFrame(top_dest)
            fig_dest = px.bar(
                df_dest, 
                x="destination", 
                y="count", 
                labels={"destination": "City", "count": "Plans Count"},
                color_discrete_sequence=["#6929C4"]
            )
            fig_dest.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=300
            )
            st.plotly_chart(fig_dest, use_container_width=True)


# ── Render Page Sidebars ───────────────────────────────────────

def render_sidebar():
    st.sidebar.markdown("""
    <div style='text-align: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(0,0,0,0.08);'>
        <div style='font-size: 1.4rem;'>✈️</div>
        <div style='font-weight: 800; font-size: 1rem; margin-top: 4px;'>AI <strong>Travel</strong> Planner</div>
        <span style='background: #0062FF; color: white; font-size: 0.6rem; font-weight: 700; letter-spacing: .05em; border-radius: 4px; padding: 2px 7px;'>IBM Granite</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.token:
        user = st.session_state.user
        initials = user['name'][0].upper() if user.get('name') else 'U'
        st.sidebar.markdown(f"""
        <div style='background: var(--secondary-background-color); border: 1px solid var(--border-color, rgba(0,0,0,0.08)); border-radius: 10px; padding: 14px; margin-bottom: 16px; text-align: center;'>
            <div style='width: 38px; height: 38px; background: #0062FF; color: white; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700; margin-bottom: 8px;'>{initials}</div><br>
            <b style='font-size: 0.9rem;'>{user['name']}</b><br>
            <small style='color:#8D8D8D;'>{user['email']}</small><br>
            <span style='background: #0062FF; color: white; font-size: 0.65rem; padding: 2px 7px; border-radius: 10px; font-weight: 700; text-transform: uppercase; margin-top: 6px; display: inline-block;'>{user.get('role', 'user')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Options
        if st.sidebar.button("📂 My Dashboard", use_container_width=True):
            navigate_to("Dashboard")
        if st.sidebar.button("🚀 Plan New Trip", use_container_width=True):
            navigate_to("Plan New Trip")
        if st.sidebar.button("⭐ Saved Trips", use_container_width=True):
            navigate_to("Saved Trips")
            
        # Admin menu
        if st.session_state.user.get("role") == "admin":
            st.sidebar.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)
            if st.sidebar.button("🛡️ Admin Panel", use_container_width=True):
                navigate_to("Admin Panel")
                
        st.sidebar.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.current_trip_id = None
            navigate_to("Welcome")
    else:
        st.sidebar.markdown("""
        <div style='background: rgba(0,98,255,.05); border: 1px solid rgba(0,98,255,.2); border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.5;'>
            👋 <b>Welcome!</b><br>Login or create an account to start planning your personalized AI travel itineraries.
        </div>
        """, unsafe_allow_html=True)


# Main Application Loop
def main():
    render_sidebar()
    
    # Authenticate route state
    if st.session_state.token is None:
        render_welcome_page()
    else:
        if st.session_state.current_page == "Welcome":
            st.session_state.current_page = "Dashboard"
            
        if st.session_state.current_page == "Dashboard":
            render_dashboard_page()
        elif st.session_state.current_page == "Plan New Trip":
            render_planner_page()
        elif st.session_state.current_page == "View Trip":
            render_trip_view_page()
        elif st.session_state.current_page == "Saved Trips":
            render_saved_trips_page()
        elif st.session_state.current_page == "Admin Panel":
            render_admin_page()
        else:
            render_welcome_page()

if __name__ == "__main__":
    main()
