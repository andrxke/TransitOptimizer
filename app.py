from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
from dotenv import load_dotenv
import transit_engine

load_dotenv()

app = Flask(__name__)

# Basic Route to serve the frontend
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/optimize-trip', methods=['POST'])
def optimize_trip():
    data = request.json
    api_key = data.get('api_key') or os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return jsonify({"error": "API Key is required"}), 400
        
    try:
        origin = data['origin']
        destination = data['destination']
        window_start = datetime.fromisoformat(data['window_start'])
        window_end = datetime.fromisoformat(data['window_end'])
        
        # Ensure UTC/Offset awareness if needed, but simplisticiso format usually works for local time assumes
        # Ideally frontend sends ISO strings.
        
        result = transit_engine.find_best_departure(
            api_key, origin, destination, window_start, window_end
        )
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/optimize-work', methods=['POST'])
def optimize_work():
    data = request.json
    api_key = data.get('api_key') or os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return jsonify({"error": "API Key is required"}), 400
        
    try:
        origins = data['origins']
        destination = data['destination']
        work_duration = float(data['work_duration_hours'])
        window_start = datetime.fromisoformat(data['window_start'])
        window_end = datetime.fromisoformat(data['window_end'])
        
        result = transit_engine.optimize_work_schedule(
            api_key, origins, destination, work_duration, window_start, window_end
        )
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
