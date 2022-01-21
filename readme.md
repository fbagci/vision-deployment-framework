# Vision Deployment Framework

## Quick start

To start framework run:
```
cd /project/path
./run.sh
```

## Project description
### Project Structure
This framework consist of 4 services named ```deployment```, ```inference```, ```mmdetection``` and ```tensorflow(tf)``` api. <br/>

```Deployment``` and ```inference``` apis are designed for endusers whereas ```mmdetection api``` and ```tensorflow api``` are used in application internally. ```mmdetection service``` is responsible from inference with mmdetection models similarly ```tensorflow service``` is responsible from inference with tensorflow models. ```Deployment api``` lets us deploy our models and we can make inference with deployed model using ```inference api```. 
### Deployment
Endusers utilizes deployment api to deploy their models. Deployment api has one endpoint which is ```deploy```.
Users make ```POST``` request to ```localhost:5003/deploy``` with request body shown below.
```
{
    "type": "tf" # or "mmdetection",
    "checkpoint_url": "https://www..." # the model checkpoint address,
    "deployment_name": "my_object_detection_model_1" # this is unique name and will be used in inference
    "config": "/faster_rcnn/faster_rcnn_1x_rpn.py" # if model is mmdetection, you need to add config path from original mmdetection repo(https://github.com/open-mmlab/mmdetection)
}
```
If everything is OK, the backend starts deployment asynchronously(download checkpoint, save informations in db(postgres)) and returns,
```
{
    "result": "success"
}
```
### Inference
Endusers utilizes inference api to use their models. Inference api has one endpoint which is ```infer```.
Users make ```GET``` request to ```localhost:5004/infer``` with request body shown below.
```
{
    "deployment_name": "my_object_detection_model_1" # this is unique name it was set at deployment time
    "image": "5aWDj..." # The base64 image that we apply inference on",
    "ground_truth_boxes": [
                            {
                                "class": "dog",
                                "bbox": [123, 235, 432, 45]
                            },
                            {
                                "class": "cat",
                                "bbox": [53, 35, 49, 25]
                            }
                          ]
}
```
If everything is OK, the backend starts inference and returns,
```
{
    "objects":[
        {
            "class": "dog",
            "bbox": [123, 235, 432, 45]
        },
        {
            "class": "cat",
            "bbox": [53, 35, 49, 25]
        }
        ...
    ],
    "AP": 0.5,
    ...
}
```