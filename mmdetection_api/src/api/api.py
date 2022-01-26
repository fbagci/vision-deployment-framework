import json
import os
import shutil
import base64

import cv2
from flask import Flask, request, jsonify
import mmcv
import numpy as np
from pymongo import MongoClient
import wget

from mmdet.apis import init_detector, inference_detector, show_result_pyplot
from src.utils.utils import get_config, get_mongo_conn_str
from src.utils.numpy_encoder import NumpyEncoder

# get model and config dir from env vars
MODELDIR = os.environ["MODELDIR"]
APPCONFIGDIR = os.environ["APPCONFDIR"]

# read app config
app_config = get_config(os.environ["APPCONFDIR"])

# initialize db client
conn_str = get_mongo_conn_str(app_config["mongo"])
client = MongoClient(conn_str)
db_framework = client["framework"]
col_dep = db_framework["deployment"]

# initialize flask app
app = Flask(__name__)

# read app config
app_config = get_config(APPCONFIGDIR)

# read models from files
post_deps = col_dep.find({})
models={}
for dep in post_deps:
    conf_path = os.path.join("/mmdetection_api/mmdetection/configs", dep["config_path"])
    models[dep["_id"]]= init_detector(conf_path, dep["model_path"], device='cpu')

@app.route("/deploy", methods=["POST"])
def deploy_model():
    """
    Deploy model
    """
    try:
        # parse request body
        body = json.loads(request.data)['body']
        # make model dir
        model_folder_path = os.path.join(MODELDIR, body['_id'])
        os.mkdir(model_folder_path)
        # Beginning file download with wget module
        model_file_path = os.path.join(model_folder_path, body['_id'])
        wget.download(body['checkpoint_url'], model_file_path)
        result = "success"
    except:
        result = "fail"
        model_file_path = "/"
    return jsonify({"result":result, "model_path":model_file_path})

@app.route("/deploy", methods=["DELETE"])
def delete_deployment():
    """
    Delete deployment
    """
    try:
        # parse request body
        body = json.loads(request.data)['body']
        # remove model dir
        model_folder_path = os.path.join(MODELDIR, body['_id'])
        shutil.rmtree(model_folder_path)
        result = "success"
    except:
        result = "fail"
    return jsonify({"result":result, "model_path":model_folder_path})

@app.route("/infer", methods=["POST"])
def infer():
    """
    Apply detection on single image
    """
    # parse request body
    body = json.loads(request.data)["body"]
    img = cv2.imdecode(np.fromstring(base64.b64decode(body["img_b64"]),np.uint8),cv2.IMREAD_UNCHANGED)
    # run detector
    result = inference_detector(models[body["_id"]], img)
    return jsonify({"result":json.dumps(result, cls=NumpyEncoder)})

if __name__ == "__main__":
    runapp = app.run(host = "0.0.0.0",
                     threaded = True,
                     port = app_config["port"])