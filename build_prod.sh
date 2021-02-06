#! /bin/bash
source env.prod
docker build -t asterisk_cdr .
docker tag smsgateway ${DOCKER_REGISTRY}/asterisk_cdr:latest
docker push ${DOCKER_REGISTRY}/asterisk_cdr:latest
python deploy/deploy.py
