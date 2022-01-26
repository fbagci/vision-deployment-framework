import yaml

def get_config(config_fpath):
    """
    Read config from yml
    """
    with open(config_fpath, "r") as stream:
        conf = yaml.safe_load(stream)
    return conf

def get_mongo_conn_str(config_mongo):
    uri = "mongodb://{}:{}@{}:{}/{}?authSource=admin".format(config_mongo["MONGO_USER"], 
                                                             config_mongo["MONGO_PASS"], 
                                                             config_mongo["MONGO_HOST"], 
                                                             config_mongo["MONGO_PORT"], 
                                                             config_mongo["MONGO_DB"])
    return uri