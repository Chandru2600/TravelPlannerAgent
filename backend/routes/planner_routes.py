"""
TravelPlannerAgent - Travel Planner Routes (Blueprint)
IBM SkillsBuild Internship Project
"""

import json
from datetime import date
from flask import (
    Blueprint, request, render_template, redirect,
    url_for, session, flash, jsonify, current_app, send_file
)
from backend.routes.auth_routes import login_required
from backend.models.trip import (
    create_trip, get_trip_by_id, get_trips_by_user,
    update_trip_itinerary, delete_trip, save_trip,
    get_saved_trips, unsave_trip, add_expense, get_expenses
)
from backend.services.granite.granite_service import generate_complete_travel_plan
from backend.services.weather.weather_service import (
    get_current_weather, get_forecast, get_travel_weather_advice
)
from backend.services.pdf.pdf_service import generate_trip_pdf

planner_bp = Blueprint("planner", __name__, url_prefix="/planner")


@planner_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_trip():
    """Travel Planner form — collect trip details."""
    today = date.today().isoformat()
    if request.method == "POST":
        # ── Collect form data ──────────────────────────────────
        destination   = request.form.get("destination", "").strip()
        start_date    = request.form.get("start_date")
        end_date      = request.form.get("end_date")
        num_days      = int(request.form.get("num_days", 1))
        budget        = float(request.form.get("budget", 1000))
        num_travelers = int(request.form.get("num_travelers", 1))
        travel_style  = request.form.get("travel_style", "budget")
        transport     = request.form.get("transport", "flight")
        interests     = request.form.getlist("interests")
        special_reqs  = request.form.getlist("special_requirements")

        if not destination:
            flash("Please enter a destination.", "danger")
            return render_template("planner/new_trip.html")

        trip_data = {
            "destination":           destination,
            "start_date":            start_date,
            "end_date":              end_date,
            "num_days":              num_days,
            "budget":                budget,
            "num_travelers":         num_travelers,
            "travel_style":          travel_style,
            "transport":             transport,
            "interests":             interests,
            "special_requirements":  special_reqs
        }

        # ── Save initial trip record ───────────────────────────
        trip_id = create_trip(session["user_id"], trip_data)

        # ── Call IBM Granite ───────────────────────────────────
        flash("Generating your AI itinerary with IBM Granite…", "info")
        try:
            ai_result = generate_complete_travel_plan(trip_data)
        except Exception as e:
            ai_result = {
                "itinerary": {"error": str(e)},
                "budget":    {}, "hotels": {}, "transport": {}, "food": {}
            }
            flash(f"AI generation warning: {e}", "warning")

        # ── Fetch weather ──────────────────────────────────────
        weather_current  = get_current_weather(destination)
        weather_forecast = get_forecast(destination)
        weather_advice   = get_travel_weather_advice(weather_current)
        weather_data = {
            "current":  weather_current,
            "forecast": weather_forecast.get("forecast", []),
            "alerts":   weather_advice
        }

        # ── Persist AI results ─────────────────────────────────
        update_trip_itinerary(
            trip_id,
            ai_result.get("itinerary", {}),
            weather_data,
            ai_result.get("budget", {}),
            ai_result.get("hotels", {})
        )

        return redirect(url_for("planner.view_trip", trip_id=trip_id))

    return render_template("planner/new_trip.html", today=today)


@planner_bp.route("/<int:trip_id>")
@login_required
def view_trip(trip_id: int):
    """Full itinerary view for a trip."""
    trip = get_trip_by_id(trip_id)
    if not trip or trip["user_id"] != session["user_id"]:
        flash("Trip not found.", "warning")
        return redirect(url_for("main.dashboard"))

    itinerary  = json.loads(trip["itinerary_json"] or "{}")
    weather    = json.loads(trip["weather_json"]   or "{}")
    budget     = json.loads(trip["budget_json"]    or "{}")
    hotels     = json.loads(trip["hotels_json"]    or "{}")
    expenses   = get_expenses(trip_id)

    return render_template("planner/view_trip.html",
        trip=trip,
        itinerary=itinerary,
        weather=weather,
        budget=budget,
        hotels=hotels,
        expenses=expenses
    )


@planner_bp.route("/<int:trip_id>/delete", methods=["POST"])
@login_required
def delete_trip_route(trip_id: int):
    """Delete a user's trip."""
    delete_trip(trip_id, session["user_id"])
    flash("Trip deleted.", "success")
    return redirect(url_for("main.dashboard"))


@planner_bp.route("/<int:trip_id>/save", methods=["POST"])
@login_required
def save_trip_route(trip_id: int):
    """Save a trip to favourites."""
    notes = request.form.get("notes", "")
    save_trip(session["user_id"], trip_id, notes)
    flash("Trip saved!", "success")
    return redirect(url_for("planner.view_trip", trip_id=trip_id))


@planner_bp.route("/saved")
@login_required
def saved_trips():
    """List saved/favourite trips."""
    trips = get_saved_trips(session["user_id"])
    return render_template("planner/saved_trips.html", trips=trips)


@planner_bp.route("/saved/<int:saved_id>/remove", methods=["POST"])
@login_required
def remove_saved(saved_id: int):
    """Remove a trip from saved."""
    unsave_trip(saved_id, session["user_id"])
    flash("Removed from saved trips.", "info")
    return redirect(url_for("planner.saved_trips"))


@planner_bp.route("/<int:trip_id>/pdf")
@login_required
def download_pdf(trip_id: int):
    """Generate and serve a PDF report for the trip."""
    trip = get_trip_by_id(trip_id)
    if not trip or trip["user_id"] != session["user_id"]:
        flash("Trip not found.", "warning")
        return redirect(url_for("main.dashboard"))

    itinerary = json.loads(trip["itinerary_json"] or "{}")
    budget    = json.loads(trip["budget_json"]    or "{}")
    hotels    = json.loads(trip["hotels_json"]    or "{}")
    weather   = json.loads(trip["weather_json"]   or "{}")

    try:
        pdf_path = generate_trip_pdf(trip, itinerary, budget, hotels, weather)
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"TravelPlan_{trip['destination'].replace(' ', '_')}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"PDF generation failed: {e}", "danger")
        return redirect(url_for("planner.view_trip", trip_id=trip_id))


@planner_bp.route("/<int:trip_id>/expense", methods=["POST"])
@login_required
def add_expense_route(trip_id: int):
    """Add a manual expense entry."""
    category    = request.form.get("category", "miscellaneous")
    amount      = float(request.form.get("amount", 0))
    description = request.form.get("description", "")
    add_expense(trip_id, category, amount, description)
    flash("Expense added.", "success")
    return redirect(url_for("planner.view_trip", trip_id=trip_id))


# ── API Endpoints ─────────────────────────────────────────────

@planner_bp.route("/api/weather/<city>")
def weather_api(city: str):
    """JSON weather endpoint for frontend fetch."""
    current  = get_current_weather(city)
    forecast = get_forecast(city)
    alerts   = get_travel_weather_advice(current)
    return jsonify({"current": current, "forecast": forecast, "alerts": alerts})
