#!/bin/bash

CONTAINERS='["lab", "ctx", "uxo", "tbd", "ipf", "pet", "bit"]'
MODELS='["src", "aura", "frame", "ode", "mind", "heart", "soul", "envy", "chaos", "ghost", "malice", "toe"]'

# Check for docker
if ! command -v docker &> /dev/null; then
  echo "Error: docker is not installed or not in PATH."
  exit 1
fi

# Check for docker-compose
if ! command -v docker compose &> /dev/null; then
  echo "Error: docker compose is not installed or not in PATH."
  exit 1
fi

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
GPU=''
if [[ "$ARCH" == "ARM" ]]; then
    echo "building for ARM"
    GPU='-f compose.ARM.yml'
elif [[ "$DEVICE" == "amd" ]]; then
    GPU='-f compose.amd.yml'
elif [[ "$DEVICE" == "intel" ]]; then
    GPU='-f compose.intel.yml'
else
    GPU='-f compose.nvidia.yml'
fi

if test "$(docker context show)" = "one"; then
    eval "$(ssh-agent -s)"
    ssh-add one.key
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
        docker compose -f compose.yml $GPU build && docker images | grep /lab ;;
        # docker history <image>
    "push") 
        docker compose push ;;
    "pull") 
        docker compose -f compose.yml -f compose.services.yml pull ;;
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

        if test "$(docker context show)" = "one"; then
            FOCUS=${FOCUS} docker compose up
            exit 1
        fi

        # nohup docker compose -f compose.yml -f compose.dev.yml -f compose.services.yml watch --no-up >/dev/null 2>&1 &
        FOCUS=${FOCUS} docker compose -f compose.yml -f compose.dev.yml -f compose.services.yml $GPU up ${ARG1} ;;
    "train" | "trial") 
        if [[ -z "$FOCUS" ]]; then
            read -p "Which model should we train? ${MODELS} " FOCUS
        fi
        docker compose -f compose.yml -f compose.services.yml up -d tbd ipf opt && docker compose -f compose.yml -f compose.dev.yml -f compose.train.yml $GPU run -e FOCUS=${FOCUS} -e TASK=${action} lab python3 harness.py ;;
    "prepare") 
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we prepare? " DIRECTORY
        fi
        docker compose -f compose.yml -f compose.dev.yml run lab python3 /lab/${DATASET}/prepare.py ;;
    "fetch")
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we fetch? " DIRECTORY
        fi
        docker compose  -f compose.yml -f compose.dev.yml run lab python3 /lab/${DATASET}/fetch.py ;;
    "prune")
        docker system prune -f && docker volume prune -f ;;
    "key")
        docker compose exec urb /bin/get-urbit-code ;;
    "down")
        docker compose down --remove-orphans ;;
    *) 
        echo "Invalid selection." ;;
esac