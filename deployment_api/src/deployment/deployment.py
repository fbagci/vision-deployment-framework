import requests
import time
import json

def send_request(url, type, post):
    data={'body': post}
    headers = {'Content-Type': "application/json", 'Accept': "application/json"}
    if type == "post":
        res = requests.post(url, 
                            json=data, 
                            headers=headers)
    elif type == "delete":
        res = requests.delete(url, 
                              json=data, 
                              headers=headers)
    return res

def start_deployment(col_dep, post):
    req_type = "post"
    if post["type"] == "mmdetection":
        url = "http://mmdetection-api:5002/deploy"
        resp = send_request(url, req_type, post)
        return resp.json()
    else:
        # tf will be implemented
        pass

def delete_deployment(post):
    req_type = "delete"
    if post["type"] == "mmdetection":
        url = "http://mmdetection-api:5002/deploy"
        resp = send_request(url, req_type, post)
        return resp.json()
    else:
        # tf will be implemented
        pass
