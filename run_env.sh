echo "Build images"
docker-compose -f ./docker-compose-dev.yml build

echo "Start containers"
docker-compose -f ./docker-compose-dev.yml up -d --remove-orphans

echo "Install deps inside deployment container"
docker exec -w / deployment-api sh -c 'pip install -r /deployment_api/requirements.txt'

echo "Install deps inside inference container"
docker exec -w / inference-api sh -c 'pip install -r /inference_api/requirements.txt'

echo "Remove unnecessary folder and install deps inside mmdet container"
docker exec -w / mmdetection-api sh -c 'rm -r /mmdetection && pip install -r /mmdetection_api/requirements.txt'