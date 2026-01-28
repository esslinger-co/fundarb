from flask import Flask, request, jsonify, send_from_directory
from typing import Dict, Any, List
from funding_arb import Leg, funding_arb   # dein Modul

app = Flask(__name__, static_folder="static", template_folder="static")


def validate_legs(data: Dict[str, Any]) -> tuple[List[Leg], float]:
    interval = data.get("interval_hours", 8.0)
    if not isinstance(interval, (int, float)) or interval <= 0:
        raise ValueError("interval_hours muss > 0 sein")

    raw_legs = data.get("legs")
    if not isinstance(raw_legs, list):
        raise ValueError("'legs' muss eine Liste sein")

    legs: List[Leg] = []
    for entry in raw_legs:
        legs.append(
            Leg(
                name=str(entry["name"]),
                position=str(entry["position"]),
                funding_rate=float(entry["funding_rate"]),
                notional=float(entry["notional"]),
            )
        )
    return legs, float(interval)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/arb", methods=["POST"])
def arb():
    try:
        json_data = request.get_json(force=True)
        legs, interval = validate_legs(json_data)
        result = funding_arb(legs, interval)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=False)
