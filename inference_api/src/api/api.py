import datetime
import json
import os
import requests
import time
from datetime import datetime
from itertools import chain

from bson import json_util
from pydoc import cli
from pymongo import MongoClient
from flask import Flask, request, jsonify, Response

from src.utils.utils import get_config, get_mongo_conn_str


# initialize flask app
app = Flask(__name__)

# read app config
app_config = get_config(os.environ["APPCONFDIR"])

# initialize db client
conn_str = get_mongo_conn_str(app_config["mongo"])
client = MongoClient(conn_str)
db_framework = client["framework"]
col_dep = db_framework["deployment"]
col_image = db_framework["images"]
col_inf = db_framework["predictions"]

# initialize required data for deployment
required_inference_keys = ('deployment_name',
                           'img_name')

@app.route('/')
def base():
    """
    Get status of app
    """
    return Response(response=json.dumps({"Status": "UP"}),
                    status=200,
                    mimetype='application/json')

@app.route("/image", methods=["GET"])
def get_all_images():
    """
    Get all images
    """
    # if no record, return empty dict
    num_of_doc = col_image.count_documents({})
    if num_of_doc == 0:
        return jsonify({})
    
    # else return records
    result = list()
    docs = col_image.find({})
    for doc in docs:
        result.append(doc)
    return json_util.dumps(result)

@app.route("/infer", methods=["GET"])
def get_all_inferences():
    """
    Get all inferences
    """
    # if no record, return empty dict
    num_of_doc = col_inf.count_documents({})
    if num_of_doc == 0:
        return jsonify({})
    
    # else return records
    result = list()
    docs = col_inf.find({})
    for doc in docs:
        result.append(doc)
    return json_util.dumps(result)

@app.route("/image", methods=["DELETE"])
def delete_all_image():
    """
    Delete all images
    """
    # if no record, return empty dict
    col_image.delete_many({})
    return jsonify({"result":"success"})

@app.route("/infer", methods=["DELETE"])
def delete_all_inferences():
    """
    Delete all inferences
    """
    # if no record, return empty dict
    col_inf.delete_many({})
    return jsonify({"result":"success"})

@app.route("/infer", methods=["POST"])
def infer():
    """
    Apply inference
    """
    # parse request body
    body = json.loads(request.data)

    # raise for missing data
    if not all (key in body for key in required_inference_keys):
        return jsonify({"error": "Request body is incomplete!"})
    
    # if image not exists in db
    img_exists = col_image.count_documents({"_id":body["img_name"]})
    if img_exists == 0:
        # if b64 does not provided then raise
        if not 'img_b64' in body.keys():
            return jsonify({"error": 'Base64 encoded image is required!'})
        # save to db
        col_image.insert_one({"_id":body["img_name"], 'img_b64': body['img_b64']})
    img_post = col_image.find_one({"_id":body["img_name"]})
    
    dep_post = col_dep.find_one({"_id":body["deployment_name"]})
    
    # if deployment does not exists in db
    if len(dep_post) == 0:
        return jsonify({"error": 'Deployment does not exists!'})

    data={'body': dict(chain(img_post.items(), dep_post.items()))}
    headers = {'Content-Type': "application/json", 'Accept': "application/json"}
    url = "http://mmdetection-api:5002/infer"
    res = requests.post(url, 
                        json=data, 
                        headers=headers).json()
    inference_dict = {
                        'image_id'      : img_post['_id'],
                        'deployment_id' : dep_post['_id'],
                        'strftime'      : datetime.now().strftime('%m_%d_%Y__%H_%M_%S'),
                        'predictions'   : res["result"]
                     }
    result = inference_dict.copy()
    col_inf.insert_one(inference_dict)
    
    return jsonify({'result': result})

if __name__ == "__main__":
    runapp = app.run(host = "0.0.0.0",
                     threaded = True,
                     port = app_config["port"])