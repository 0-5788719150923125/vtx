#!/bin/bash

CONTAINERS='["lab", "ctx", "tbd", "fil", "pet", "bit"]'
MODELS='["src", "ode", "frame", "aura", "mind", "heart", "soul", "envy", "chaos", "malice", "ghost", "toe"]'

# If defined, use the TASK variable.
if [[ -n "$TASK" ]]; then
    action="$TASK"
else
    # Prompt for input.
    echo "Use keywords to control the VTX:"
    echo "(ps)      View a list of all running containers."
    echo "(stats)   View live Docker stats."
    echo "(logs)    View logs for all services."
    echo "(exec)    Open an interactive shell in the specified container."
    echo "(build)   Build this project in Docker."
    echo "(test)    Run all tests."
    echo "(eval)    Run evalutation harness."
    echo "(push)    Push the newly-built Docker image to a registry."
    echo "(pull)    Pull the latest Docker images required by this project."
    echo "(up)      Bring the stack online."
    echo "(down)    Stop the service in Docker."
    echo "(fetch)   Download a dataset."
    echo "(prepare) Prepare a dataset."
    echo "(train)   Train a model."
    echo "(trial)   Search for optimal hyperparameters."
    echo "(prune)   Prune all unused images, networks, and volumes."
    echo "(key)     Fetch your Urbit access key."
    echo "(auto)    Turn on autopilot."
    read -p "Enter the keyword corresponding to your desired action: " action
fi

# Import variables
if [ ! -f '.env' ]; then
    touch .env
fi

. './.env'

# Setup config file
if [ ! -f 'config.yml' ]; then
    touch config.yml
fi

# Set GPU mode
if [[ "$DEVICE" != "cpu" ]]; then
    GPU='-f docker-compose.gpu.yml'
fi

# Implement the controller
case $action in
    "ps") 
        docker compose ps ;;
    "logs") 
        docker compose logs --follow ;;
    "stats")
        docker stats ;;
    "exec") 
        if [[ -z "$CONTAINER" ]]; then
            read -p "Which container should we enter? ${CONTAINERS} " CONTAINER
        fi
        docker compose exec ${CONTAINER} /bin/bash ;;
    "test") 
        docker compose exec lab robot --outputdir /book/static/tests /src/tests ;;
    "eval") 
        docker compose exec lab sh tests/eval.sh ;;
    "build") 
        docker compose build ;;
    "push") 
        docker compose push ;;
    "pull") 
        docker compose -f docker-compose.yml -f docker-compose.services.yml pull ;;
    "up" | "auto")
        if [[ -z "$FOCUS" ]]; then
            read -p "Which model should we focus on? ${MODELS} " FOCUS
        fi
        if [[ "$action" == "auto" ]]; then
            DETACHED="true"
        fi
        if [[ "$DETACHED" == "true" ]]; then
            ARG1='-d'
        fi
        FOCUS=${FOCUS} docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.services.yml $GPU up ${ARG1} ;;
    "train" | "trial") 
        if [[ -z "$FOCUS" ]]; then
            read -p "Which model should we train? ${MODELS} " FOCUS
        fi
        docker compose -f docker-compose.yml -f docker-compose.services.yml up -d tbd fil && docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.train.yml $GPU run -e FOCUS=${FOCUS} -e JOB=${action} lab python3 harness.py ;;
    "prepare") 
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we prepare? " DIRECTORY
        fi
        docker compose -f docker-compose.yml -f docker-compose.dev.yml run lab python3 /lab/${DATASET}/prepare.py ;;
    "fetch")
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we fetch? " DIRECTORY
        fi
        docker compose  -f docker-compose.yml -f docker-compose.dev.yml run lab python3 /lab/${DATASET}/fetch.py ;;
    "prune")
        docker system prune -f && docker volume prune -f ;;
    "key")
        docker compose exec bit /bin/get-urbit-code ;;
    "down")
        docker compose down --remove-orphans ;;
    *) 
        echo "Invalid selection." ;;
esac