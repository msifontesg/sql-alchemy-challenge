# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect the tables
base = automap_base()

# Save references to each table
measurement = base.classes.measurement
station = base.classes.station

# Create our session (link) from Python to the DB


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

def first_last_dates(session):
    
    # Calculate first date in range
    first_date = session.query(func.min(measurement.date)).first()[0]
    
    # Calculate last date in range
    last_date = session.query(func.max(measurement.date)).first()[0]
    
    return first_date, last_date

def last_year(session):

    # Find the most recent date in the data set.
    _,last_date = first_last_dates(session)
    
    year = int(last_date[0:4])              #Get year from first four digits of date and convert to integer
    last_year = str(year - 1)                 #Get the previous year and assign it to a variable as a string
    year_ago = last_year + last_date[4:]    #Define the date one year ago
    
    return year_ago

def is_valid_datetime(datetime_str):
    try:
        dt.datetime.strptime(datetime_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
    
def datetime_format(datetime_str):
    
    # Convert string to datetime
    datetime_object = dt.datetime.strptime(datetime_str, "%Y-%m-%d")
    
    # Convert datetime back to string
    formatted_datetime = datetime_object.strftime("%Y-%m-%d")
    
    return formatted_datetime
    
#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    

    session = Session(engine)
    

    first_date, last_date = first_last_dates(session)
    
    session.close()
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/YYYY-MM-DD<br/>"
        f"/api/v1.0/YYYY-MM-DD/YYYY-MM-DD<br/>"
        f"<br/>Notes on last two routes:<br/>"
        f"Using one date in the URL defines a start date<br/>"
        f"Using two dates in the URL (separated by a '/') defines a start (first) and end date (second) <br/>"
        f"Dates must be between {first_date} and {last_date}"
    )

@app.route("/api/v1.0/precipitation")
def rain():

    session = Session(engine)

    """Return a year's worth of precipitation data as a list"""

    year_ago = last_year(session)


    rain_data = session.query(measurement.date,measurement.prcp).filter(measurement.date >= year_ago).all()

    session.close()


    all_rain = dict(rain_data)

    return jsonify(all_rain)

@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)

    """Return a list of all station names"""

    station_list = session.query(station.station).all()

    session.close()


    station_names = [row[0] for row in station_list]

    return jsonify(station_names)

@app.route("/api/v1.0/tobs")
def temperature():
    

    session = Session(engine)

    """Return a year's worth of temperature data (from the most active station) as a list"""

    station_query = session.query(measurement.station).\
    group_by(measurement.station).order_by(desc(func.count(measurement.station)))
    

    station_max = station_query.first()[0]
    

    year_ago = last_year(session)
    
    temp_data = session.query(measurement.date,measurement.tobs).\
    filter(measurement.date >= year_ago).filter(measurement.station == station_max).all()

    session.close()


    temp_list = dict(temp_data)
    
    return jsonify(most_active_station = station_max, temperatures_by_date = temp_list)

@app.route("/api/v1.0/<start>")
def start(start):
    

    if not is_valid_datetime(start):
        return "Invalid Date or API Route"

    else:
        start = datetime_format(start)
    

    session = Session(engine)

    first_date, last_date = first_last_dates(session)
    

    if start < first_date or start > last_date:
        return f"Date is outside of valid date range. Try a date between {first_date} and {last_date}"

    """Return the minimum, maximum, and average temperatures over a timeframe define by user-inputed start date"""

    temp_data = session.query(func.min(measurement.tobs),func.max(measurement.tobs),func.avg(measurement.tobs))\
    .filter(measurement.date >= start).all()[0]

    session.close()


    temp_keys = ("Minimum Temperature","Maximum Temperature","Average Temperature")


    temp_dict = {key: value for key, value in zip(temp_keys, temp_data)}

    return jsonify(start_date = start, temperature_data = temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):
    

    if not (is_valid_datetime(start) and is_valid_datetime(end)):
        return "Invalid Date Combination"

    else:
        start = datetime_format(start)
        end = datetime_format(end)
    

    session = Session(engine)
    

    first_date, last_date = first_last_dates(session)
    

    if (start < first_date or end < first_date ) or (start > last_date or end > last_date) :
        return f"One or more dates outside of valid date range. Try start and end dates between {first_date} and {last_date}"
    elif start > end:
        return "The start date must come before (or be the same as) the end date"

    """Return the minimum, maximum, and average temperatures over a timeframe define by user-inputed start and end dates"""

    temp_data = session.query(func.min(measurement.tobs),func.max(measurement.tobs),func.avg(measurement.tobs))\
    .filter(measurement.date >= start).filter(measurement.date <= end).all()[0]

    session.close()


    temp_keys = ("Minimum Temperature","Maximum Temperature","Average Temperature")


    temp_dict = {key: value for key, value in zip(temp_keys, temp_data)}


    date_range = {"Start Date" : start, "End Date" : end}

    return jsonify(date_range = date_range, temperature_data = temp_dict)

if __name__ == '__main__':
    app.run(debug=True)