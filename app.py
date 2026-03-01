import os
import time
import io
from dotenv import load_dotenv
import streamlit as st
import googlemaps
import openpyxl

load_dotenv()

st.set_page_config(page_title="Shop Finder", layout="wide")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    password = st.text_input("Enter password", type="password")
    if password:
        if password == st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "")):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

st.title("Car & Tire Shop Finder")

API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", os.getenv("GOOGLE_MAPS_API_KEY"))

if not API_KEY:
    st.error("Google Maps API key not found.")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

SEARCH_TYPES = {
    "Car Repair": "car repair",
    "Tire Shop": "tire shop",
    "Car Dealer": "car dealer",
}

with st.sidebar:
    st.header("Search Filters")
    location = st.text_input("Location (city or address)", placeholder="e.g. Prague")
    radius_km = st.number_input("Radius (km)", min_value=1, max_value=50, value=5)
    selected_types = st.multiselect(
        "Place types",
        options=list(SEARCH_TYPES.keys()),
        default=list(SEARCH_TYPES.keys()),
    )
    search_btn = st.button("Search", type="primary", use_container_width=True)


def fetch_places(lat, lng, radius_m, keyword):
    results = []
    response = gmaps.places_nearby(
        location=(lat, lng),
        radius=radius_m,
        keyword=keyword,
    )
    results.extend(response.get("results", []))

    while "next_page_token" in response and len(results) < 60:
        time.sleep(2)
        response = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius_m,
            keyword=keyword,
            page_token=response["next_page_token"],
        )
        results.extend(response.get("results", []))

    return results


def get_details(place_id):
    details = gmaps.place(
        place_id=place_id,
        fields=["formatted_phone_number", "website"],
    )
    result = details.get("result", {})
    return {
        "phone": result.get("formatted_phone_number", ""),
        "website": result.get("website", ""),
    }


def build_excel(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Name", "Address", "Phone", "Website", "Contact Person"])
    for col in ws[1]:
        col.font = openpyxl.styles.Font(bold=True)
    for row in rows:
        ws.append([row["name"], row["address"], row["phone"], row["website"], row["contact_person"]])
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = min(max_len, 60)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


if search_btn:
    if not location:
        st.warning("Please enter a location.")
        st.stop()
    if not selected_types:
        st.warning("Please select at least one place type.")
        st.stop()

    with st.spinner("Geocoding location..."):
        geocode = gmaps.geocode(location)
        if not geocode:
            st.error(f"Could not find location: {location}")
            st.stop()
        loc = geocode[0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
        st.info(f"Searching around: {geocode[0]['formatted_address']}")

    radius_m = radius_km * 1000
    all_places = []
    seen_ids = set()

    for label in selected_types:
        keyword = SEARCH_TYPES[label]
        with st.spinner(f"Searching for {label}..."):
            places = fetch_places(lat, lng, radius_m, keyword)
            for p in places:
                pid = p["place_id"]
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_places.append(p)

    if not all_places:
        st.warning("No results found. Try a larger radius or different location.")
        st.stop()

    rows = []
    progress = st.progress(0, text="Fetching details...")
    for i, place in enumerate(all_places):
        details = get_details(place["place_id"])
        rows.append({
            "name": place.get("name", ""),
            "address": place.get("vicinity", ""),
            "phone": details["phone"],
            "website": details["website"],
            "contact_person": "",
        })
        progress.progress((i + 1) / len(all_places), text=f"Fetching details {i+1}/{len(all_places)}")
    progress.empty()

    st.success(f"Found {len(rows)} places.")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    excel_buf = build_excel(rows)
    st.download_button(
        label="Download Excel",
        data=excel_buf,
        file_name="shop_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
