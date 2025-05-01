#!/bin/bash

DOCKER_COMPOSE_FRONTEND=false

# Variables
STACK_NAME="CdkStack"
OUTPUT_FILE="../angular/public/stack-outputs.json"
SHARED_OUTPUT_FILE="../shared/stack-outputs.json"
LOCALSTACK_URL="http://localhost:4566"

if [ "$DOCKER_COMPOSE_FRONTEND" = true ] ;
  then
    echo "Starting both localstack and angular app with docker-compose"
    docker-compose down -v
    docker pull localstack/localstack-pro:4.0.3
    docker-compose --profile enable_frontend up -d --build
  else
    echo "Starting only localstack with docker-compose"
    docker-compose down -v
    docker pull localstack/localstack-pro:4.0.3
    docker-compose up -d --build
fi

cd cdk

echo "Deploying local-stack"

cdklocal bootstrap

cdklocal deploy --require-approval never --outputs-file $OUTPUT_FILE

if [ "$DOCKER_COMPOSE_FRONTEND" = false ]; then
    cd ../angular
    npm run start
fi