import datetime
import json
import os
import time
from datetime import datetime

from bson import json_util
from pydoc import cli
from pymongo import MongoClient
from flask import Flask, request, jsonify, Response

from src.deployment.deployment import start_deployment, delete_deployment
from src.utils.utils import get_config, get_mongo_conn_str


# initialize flask app
app = Flask(__name__)

# get config dir from env var
APPCONFIGDIR = os.environ["APPCONFDIR"]

# read app config
app_config = get_config(APPCONFIGDIR)

# initialize db client
conn_str = get_mongo_conn_str(app_config["mongo"])
client = MongoClient(conn_str)
db_framework = client["framework"]
col_dep = db_framework["deployment"]

# initialize required data for deployment
required_deployment_keys = ('type',
                            'checkpoint_url',
                            'deployment_name')

@app.route('/')
def base():
    """
    Get status of app
    """
    return Response(response=json.dumps({"Status": "UP"}),
                    status=200,
                    mimetype='application/json')

@app.route("/deploy", methods=["GET"])
def get_all_deployments():
    """
    Get all deployments
    """
    # if no record, return empty dict
    num_of_doc = col_dep.count_documents({})
    if num_of_doc == 0:
        return jsonify({})
    
    # else return records
    result = list()
    docs = col_dep.find({})
    for doc in docs:
        result.append(doc)
    return json_util.dumps(result)

@app.route("/deploy/status", methods=["GET"])
def get_status():
    """
    Get status of deployment
    """
    # parse request body
    body = json.loads(request.data)

    # raise if deployment name is missing
    if not all (key in body for key in ('deployment_name')):
        return jsonify({"error": 'Please provide your deployment name!'})

    doc = col_dep.find_one({'_id':body["deployment_name"]})
    return jsonify({"status": doc["status"]})

@app.route("/deploy", methods=["POST"])
def deploy_model():
    """
    Deploy a model
    """
    # parse request body
    body = json.loads(request.data)

    # raise for missing data
    if not all (key in body for key in required_deployment_keys):
        return jsonify({"error": "Request body is incomplete!"})
    
    if body['type'] == 'mmdetection' and not 'config_path' in body.keys():
        return jsonify({"error": "MMdetection deployment needs config!"})

    if col_dep.find_one({"_id":body['deployment_name']}):
        return jsonify({"error": "Deployment with same name exists!"})
    
    post = {
            '_id'           : body['deployment_name'],
            'checkpoint_url': body['checkpoint_url'],
            'type'          : body['type'],
            'strftime'      : datetime.now().strftime("%m_%d_%Y__%H_%M_%S"),
            'status'        : "RUNNING",
           }

    if body['type'] == 'mmdetection':
        post['config_path'] = body['config_path']

    col_dep.insert_one(post)
    response = jsonify({'result': 'success'})
    
    @response.call_on_close
    def on_close():
        resp = start_deployment(col_dep, post)
        col_dep.update_one({"_id":post["_id"]}, 
                           {"$set":{"status":resp["result"]}})
        col_dep.update_one({"_id":post["_id"]}, 
                           {"$set":{"model_path":resp["model_path"]}})
    return response


@app.route("/deploy", methods=["DELETE"])
def delete_deploy():
    """
    Delete deployment by id
    """
    # parse request body
    body = json.loads(request.data)

    if len(body) == 0:
        col_dep.delete_many({})
        return jsonify({"status": "success"})

    if not 'deployment_name' in body.keys():
        return jsonify({"error": "Deployment name is needed!"})

    record = col_dep.find_one({"_id":body['deployment_name']})
    
    if not record:
        return jsonify({"error": 'No such deployment!'})    

    resp = delete_deployment(record)

    if resp["result"] == "success":
        col_dep.delete_one({"_id":body['deployment_name']})

    return jsonify({"status": resp["result"]})


if __name__ == "__main__":
    runapp = app.run(host = "0.0.0.0",
                     threaded = True,
                     port = app_config["port"])