# Transit Optimizer

A web application designed to help users optimize their transit times. This tool allows you to compare departure times, view specific transit routes, and coordinate work schedules from multiple origins.

## Features

- **Route Optimization**: Find the best transit routes and departure times. Ever wanted to know the best time to leave your house to get to work? One the Best Departure mode, enter your starting destination, work address and the time you're willing to leave at, and the app will calculate the best time to leave your house.
- **Compare Origins**: Compare travel times from different starting locations.
- **Work Schedule Coordination**: Plan commute times for work schedules involving multiple origins. Provide a list of possible departure locations (like your home address or a GO station), the earliest time you're willing to leave at, and the latest time you're willing to leave at, and the app will calculate the best time to leave for work considering the amount of hours you need to work.
- **Trip Itineraries**: View departure times for buses/subways and the route to take.

## Prerequisites

- Python 3.8+
- `pip` (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TransitOptimizer
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   ./start.sh
   # Or manually:
   # python3 app.py
   ```

2. Open your web browser and navigate to:
   `127.0.0.1:5000` (or the port specified in the console output)

## Project Structure

- `app.py`: Main Flask application entry point.
- `transit_engine.py`: Core logic for transit optimization and route calculation.
- `templates/`: HTML templates for the web interface.
- `static/`: Static assets (CSS, JS, images).
- `requirements.txt`: Python package dependencies.
- `start.sh`: Shell script to launch the application.

## License

[License Name]
