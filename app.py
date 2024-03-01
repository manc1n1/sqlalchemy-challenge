# Import the dependencies.
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)


# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/measurements'>/api/v1.0/measurements</a><br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/>"
        f"/api/v1.0/{{start_date}}<br/>"
        f"/api/v1.0/{{start_date}}/{{end_date}}"
    )


@app.route("/api/v1.0/stations")
def stations():

    # Query all stations
    stations = session.query(station).all()

    data = [
        {
            "station": station.station,
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "elevation": station.elevation,
        }
        for station in stations
    ]

    session.close()

    return jsonify({"stations": data})


@app.route("/api/v1.0/measurements")
def measurements():

    # Query all measurements
    measurements = session.query(measurement).all()

    data = [
        {
            "station": measurement.station,
            "date": measurement.date,
            "prcp": measurement.prcp,
            "tobs": measurement.tobs,
        }
        for measurement in measurements
    ]

    session.close()

    return jsonify({"measurements": data})


@app.route("/api/v1.0/precipitation")
def prcp():

    # Query the most recent date value
    recent_date = (
        session.query(measurement.date).order_by(measurement.date.desc()).first()
    )

    # Most recent date as String
    recent_date_str = recent_date[0]

    # Convert recent date to datetime
    this_year = dt.datetime.strptime(recent_date_str, "%Y-%m-%d").date()

    # Calculate the date one year from the last date in data set.
    last_year = this_year.replace(year=this_year.year - 1)

    # Perform a query to retrieve the data and precipitation scores
    prcp = (
        session.query(measurement.date, measurement.prcp)
        .filter(measurement.date <= this_year)
        .filter(measurement.date >= last_year)
    )

    data = [{"date": p.date, "prcp": p.prcp} for p in prcp]

    session.close()

    return jsonify({"precipitation": data})


@app.route("/api/v1.0/tobs")
def tobs():

    # Query the most recent date value
    recent_date = (
        session.query(measurement.date).order_by(measurement.date.desc()).first()
    )

    # Most recent date as String
    recent_date_str = recent_date[0]

    # Convert recent date to datetime
    this_year = dt.datetime.strptime(recent_date_str, "%Y-%m-%d").date()

    # Calculate the date one year from the last date in data set.
    last_year = this_year.replace(year=this_year.year - 1)

    # Query the most active stations
    most_active_id = (
        session.query(measurement.station, func.count().label("count"))
        .group_by(measurement.station)
        .order_by(func.count().desc())
        .first()
    )

    most_active_data = (
        session.query(measurement.date, measurement.tobs)
        .filter(measurement.station == most_active_id[0])
        .filter(measurement.date <= this_year)
        .filter(measurement.date >= last_year)
        .all()
    )

    data = [{"date": d.date, "tobs": d.tobs} for d in most_active_data]

    session.close()

    return jsonify({most_active_id[0]: data})


@app.route("/api/v1.0/<start_date>")
def fromDate(start_date):
    try:
        # Parse the date string into a datetime object
        start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")

        # Query the most active stations
        most_active_id = (
            session.query(measurement.station, func.count().label("count"))
            .group_by(measurement.station)
            .order_by(func.count().desc())
            .first()
        )

        most_active_data = (
            session.query(measurement.tobs)
            .filter(measurement.station == most_active_id[0])
            .filter(measurement.date >= start_date)
            .all()
        )

        # Clean list of temps
        temps = [data[0] for data in most_active_data]

        tmin = min(temps)
        tmax = max(temps)
        tavg = np.mean(temps)

        data = [{"tmin": tmin, "tmax": tmax, "tavg": tavg}]

        session.close()

        return jsonify({"temperatures": data})
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."


@app.route("/api/v1.0/<start_date>/<end_date>")
def betweenDates(start_date, end_date):
    try:
        # Parse the date string into a datetime object
        start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")

        # Query the most active stations
        most_active_id = (
            session.query(measurement.station, func.count().label("count"))
            .group_by(measurement.station)
            .order_by(func.count().desc())
            .first()
        )

        most_active_data = (
            session.query(measurement.tobs)
            .filter(measurement.station == most_active_id[0])
            .filter(measurement.date >= start_date)
            .filter(measurement.date <= end_date)
            .all()
        )

        # Clean list of temps
        temps = [data[0] for data in most_active_data]

        tmin = min(temps)
        tmax = max(temps)
        tavg = np.mean(temps)

        data = [{"tmin": tmin, "tmax": tmax, "tavg": tavg}]

        session.close()

        return jsonify({"temperatures": data})
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."


if __name__ == "__main__":
    app.run(debug=True)
