import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#####################################
#           Flask Setup
#####################################
app = Flask(__name__)

#####################################
#           Flask Routes
#####################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the Climate API!<br/>"
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'> Precipitation </a><br/>"
        f"<a href='/api/v1.0/stations'> Stations </a><br/>"
        f"<a href='/api/v1.0/tobs'> TOBS </a><br/>"
        f"<a href='/api/v1.0/2016-01-01'>'YYYY-MM-DD' (change default start date in browser after click the link)</a><br/>"
        f"<a href='/api/v1.0/2016-01-01/2017-01-01'>'YYYY-MM-DD'/'YYYY-MM-DD' (change default start/end date in browser after click the link)</a>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
   
    """Return a list of all precipitation data"""
    # Query all prcps + date
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()

    # Create a dictionary from results and append to a list of all_values
    all_values = []
    for date, prcp in results:
        precipitation_dict = {}
        precipitation_dict["date"] = date
        precipitation_dict["prcp"] = prcp
        all_values.append(precipitation_dict)

    return jsonify(all_values)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    
    """Return a list of all stations"""
    # Query all stations
    results = session.query(Station.station).all()

    session.close()

    # Convert into normal list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # Get the most recent date & 12-mo-prior date
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = most_recent_date[0]
    year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days = 365)

    # Get Most Active Station
    stations_mostactive_desc = (session.query(Measurement.station, func.count(Measurement.station)).
    group_by(Measurement.station).
    order_by(func.count(Measurement.station).desc()).all())
    most_active_station = stations_mostactive_desc[0][0]
    
    """Return a list of tobs + date for the last 12 months"""
    # Query all tobs + date for most active station for last 12 months
    results = (session.query(Measurement.date, Measurement.tobs).
    filter(Measurement.station == most_active_station).
    filter(Measurement.date >= year_ago).
    filter(Measurement.date <= most_recent_date).all())

    session.close()

    # Create a dictionary from results and append to a list of all_tobs
    all_tobs = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

@app.route("/api/v1.0/<start>")
def start_search(start):
    session = Session(engine)

    # Get MIN AVG MAX values of tobs filtered by 'start' date
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    results = session.query(*sel).filter(Measurement.date >= start).all()  

    session.close()
    
    # Get the 'most recent' & 'latest' dates in the db
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = most_recent_date[0]
    latest_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
    latest_date = latest_date[0]
    
    # Return the result OR return error if 'date' isn't found 
    if start >= latest_date and start <= most_recent_date:
        show_min_avg_max = {"MIN":results[0][0], "AVG":results[0][1], "MAX":results[0][2]}
        return jsonify(show_min_avg_max)
    return jsonify({"ERROR": f"Date {start} is not found. Please try again."}), 404

@app.route("/api/v1.0/<start>/<end>")
def start_end_search(start,end):
    session = Session(engine)

    # Get MIN AVG MAX values of tobs filtered by 'start' & 'end' date
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    session.close()
    
    # Get the 'most recent' & 'latest' dates in the db
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_date = most_recent_date[0]
    latest_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
    latest_date = latest_date[0]
    
    # Return the result OR return error if 'start' or/and 'end' dates aren't found 
    if start >= latest_date and end <= most_recent_date:
        show_min_avg_max = {"MIN":results[0][0], "AVG":results[0][1], "MAX":results[0][2]}
        return jsonify(show_min_avg_max)
    elif start < latest_date and end <= most_recent_date:
        return jsonify({"ERROR": f"Date {start} is not found. Please check the START date and try again."}), 404
    elif start >= latest_date and end > most_recent_date:
        return jsonify({"ERROR": f"Date {end} is not found. Please check the END date and try again."}), 404
    else:
        return jsonify({"ERROR": f"Dates {start} and {end} are not found. Please try again."}), 404


if __name__ == '__main__':
    app.run(debug=True)