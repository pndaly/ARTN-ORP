from flask import request, jsonify
from sqlalchemy import func
import flask_sqlalchemy as fsq
import os, json, datetime
import random, math
import numpy as np
import io
from src.models.Models import *

from src.orp import app

@app.route('/orp/orp/api/v0/test')
@app.route('/orp/api/v0/test')
@app.route('/api/v0/test')
def orp_api():
    return jsonify('henlo')


#Endpoint to get ObsReqs
@app.route('/orp/orp/api/v0/obsreq', methods=['GET'])
@app.route('/orp/api/v0/obsreq', methods=['GET'])
@app.route('/api/v0/obsreq', methods=['GET'])
def orp_api_getobsreq():
    try:
        args = request.get_json()
    except:
        return("Whoaaaa that JSON is a little wonky")

    if args is None:
        args = request.args

    if args is None:
        return("Invalid Arguments.")

    if "api_token" in args:
        apitoken = args['api_token']
        user = db.session.query(User).filter(User.api_token ==  apitoken).first()
        if user is None:
            return jsonify("invalid api_token")
    else:
        return jsonify("api_token is required")

    filter = []
    if 'obsreqid' in args:
        if isinstance(args['obsreqid']):
            obsreqid = int(args['obsreqid'])
            filter.append(ObsReq2.id == obsreqid)
    if 'object_name' in args:
        pass

    return "meh"



#Endpoint to post ObsReqs w/ ObsExposures
@app.route('/orp/orp/api/v0/obsreq', methods=['POST'])
@app.route('/orp/api/v0/obsreq', methods=['POST'])
@app.route('/api/v0/obsreq', methods=['POST'])
def orp_api_postobsreq():
    return jsonify('henlo')

#Endpoint to get exposurereqs
@app.route('/orp/orp/api/v0/obsexp', methods=['GET'])
@app.route('/orp/api/v0/obsexp', methods=['GET'])
@app.route('/api/v0/obsexp', methods=['GET'])
def orp_api_getobsexp():
    return jsonify('henlo')


#Endpoint to update obsexposures for an obsreq
#   will overwrite the current set of obsexposures
@app.route('/orp/orp/api/v0/obsexp', methods=['POST'])
@app.route('/orp/api/v0/obsexp', methods=['POST'])
@app.route('/api/v0/obsexp', methods=['POST'])
def orp_api_postobsexp():
    return jsonify('henlo')


#Endpoint to update Obsreqs (status = inProgress/Completed)
@app.route('/orp/orp/api/v0/obsreq', methods=['UPDATE'])
@app.route('/orp/api/v0/obsreq', methods=['UPDATE'])
@app.route('/api/v0/obsreq', methods=['UPDATE'])
def orp_api_updateobsreq():
    return jsonify('henlo')