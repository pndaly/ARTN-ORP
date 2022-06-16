from flask import request, jsonify
from sqlalchemy import func
import flask_sqlalchemy as fsq
import os, json, datetime
import random, math
import numpy as np
import io
from src.models.Models import *

from src.orp import app

'''
    work to be done:
        add ability for users to generate their api_token (verification I guess)
        write the api_end points
        have rts2 update values in the target_script
'''

VALID_OBSREQ_STATUS = ['inqueue', 'unscheduled', 'inprogress', 'completed']

@app.route('/orp/orp/api/v0/test')
@app.route('/orp/api/v0/test')
@app.route('/api/v0/test')
def orp_api():
    user = db.session.query(User).filter(User.username == 'artn').first()
    user.set_apitoken()
    db.session.commit()
    return user.api_token


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
        if isinstance(args['obsreqid'], int):
            obsreqid = int(args['obsreqid'])
            filter.append(ObsReq2.id == obsreqid)
        else:
            return jsonify('invalid obsreqid')
    if 'rts2id' in args:
        if isinstance(args['rts2id'], int):
            rts2id = int(args['rts2id'])
            filter.append(ObsReq2.rts2_id == rts2id)
        else:
            return jsonify('invalid rts2id')

    if len(filter):
        obs = db.session.query(ObsReq2).filter(*filter).all()
        ret = [x.serialized() for x in obs]
        return jsonify(ret)
    
    return jsonify('Must specify a filter')


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
@app.route('/orp/orp/api/v0/obsreq', methods=['PUT'])
@app.route('/orp/api/v0/obsreq', methods=['PUT'])
@app.route('/api/v0/obsreq', methods=['PUT'])
def orp_api_updateobsreq():

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


    query_filter = []
    if 'rts2id' in args:
        rts2id = args.get('rts2id')
        query_filter.append(ObsReq2.rts2_id == rts2id)

    if 'obsreqid' in args:
        obsreqid = args.get('obsreqid')
        query_filter.append(ObsReq2.id == obsreqid)

    if len(query_filter) == 0:
        return jsonify('Obsreq must be specified by fields \'rts2id\' or \'obsreqid\'')

    if 'status' not in args:
        return jsonify('status is required')
    status = args.get('status')
    if status not in VALID_OBSREQ_STATUS:
        return jsonify('invalid status, can only be updated to \'inqueue\', \'unscheduled\', \'inprogress\', \'completed\'')

    obsreq = db.session.query(ObsReq2).filter(*query_filter).all()
    if len(obsreq):
        obsreq_update = obsreq[0]
        obsreq_update.obs_status = status

        if status == 'inprogress' and 'percent_completed' in args:
            percent_completed = args.get('percent_completed')
            if isinstance(percent_completed, float) and float(percent_completed) > 0.0 and float(percent_completed) < 100:
                obsreq_update.percent_completed = percent_completed
            else:
                return jsonify('\'percent_completed\' is required')

        elif status == 'completed':

            obsreq_update.percent_completed = 100.0
            obsreq_update.completed = True
            obsreq_update.completed_iso = get_iso()
            obsreq_update.completed_mjd = iso_to_mjd(obsreq_update.completed_iso)

        else:
            obsreq_update.percent_completed = 0.0

        db.session.commit()

        return jsonify('Observation Request {} status updated to \'{}\''.format(obsreq_update.id, status))

    return jsonify('ObsReq query yielded no results')