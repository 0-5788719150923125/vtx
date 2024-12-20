#!/bin/bash

CONTAINERS='["lab", "ctx", "uxo", "tbd", "ipf", "pet", "bit"]'
MODELS='["src", "genus", "frame", "mind", "heart", "soul", "wisdom", "envy", "chaos", "malice", "pain", "rot", "sick", "toe"]'

# Check for docker
if ! command -v docker &> /dev/null; then
  echo "Error: docker is not installed or not in PATH."
  exit 1
fi

# Check for docker-compose or docker compose
if command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE_COMMAND="docker-compose"
elif command -v docker compose &> /dev/null; then
  DOCKER_COMPOSE_COMMAND="docker compose"
else
  echo "Error: docker-compose or docker compose is not installed or not in PATH."
  exit 1
fi

# If defined, use the TASK variable.
if [[ -n "$TASK" ]]; then
    action="$TASK"
else
    # Prompt for input.
    echo "Use keywords to control the VTX:"
    echo "(init)    Prepare this workspace."
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
    echo "(clean)   Delete all checkpoints."
    echo "(auto)    Turn on autopilot."
    echo "(repair)  Force-fix this workspace."
    echo "(update)  Pull all updates from git."
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

CONTEXT='default'
if test "$(docker context show)" = "one"; then
    CONTEXT='one'
    eval "$(ssh-agent -s)"
    ssh-add one.key
fi

# Set GPU mode
GPU=''
if [[ "$CONTEXT" == "one" ]]; then
    GPU='-f compose.ARM.yml'
elif [[ "$ARCH" == "ARM" ]]; then
    GPU='-f compose.ARM.yml'
elif [[ "$DEVICE" == "amd" ]]; then
    GPU='-f compose.amd.yml'
elif [[ "$DEVICE" == "intel" ]]; then
    GPU='-f compose.intel.yml'
elif [[ "$DEVICE" == "cpu" ]]; then
    GPU=''
else
    GPU='-f compose.nvidia.yml'
fi

# Implement the controller
case $action in
    "repair" | "init" | "update")
        git pull
        git submodule update --init --recursive
        git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'
        docker compose -f compose.yml -f compose.services.yml pull
        ;;
    "ps") 
        $DOCKER_COMPOSE_COMMAND ps ;;
    "logs") 
        $DOCKER_COMPOSE_COMMAND logs --follow ;;
    "stats")
        docker stats ;;
    "exec") 
        if [[ -z "$CONTAINER" ]]; then
            read -p "Which container should we enter? ${CONTAINERS} " CONTAINER
        fi
        $DOCKER_COMPOSE_COMMAND exec ${CONTAINER} /bin/bash ;;
    "test") 
        $DOCKER_COMPOSE_COMMAND exec lab robot --outputdir /book/static/tests /src/tests ;;
    "eval") 
        $DOCKER_COMPOSE_COMMAND exec lab sh tests/eval.sh ;;
    "build") 
        $DOCKER_COMPOSE_COMMAND -f compose.yml $GPU build && docker images | grep /lab ;;
        # docker history <image>
    "push") 
        $DOCKER_COMPOSE_COMMAND push ;;
    "pull") 
        $DOCKER_COMPOSE_COMMAND -f compose.yml -f compose.services.yml pull ;;
    "up" | "auto")
        if [[ -z "$FOCUS" ]]; then
            echo "MODELS = ${MODELS}"
            read -p "Which model should we focus on? " FOCUS
        fi
        if [[ "$action" == "auto" ]]; then
            DETACHED="true"
        fi
        if [[ "$DETACHED" == "true" ]]; then
            ARG1='-d'
        fi

        if test "$(docker context show)" = "one"; then
            # FOCUS=${FOCUS} docker compose up
            FOCUS=${FOCUS} $DOCKER_COMPOSE_COMMAND -f compose.yml -f compose.watch.yml $GPU watch
            exit 1
        fi
        # nohup docker compose -f compose.yml -f compose.dev.yml -f compose.services.yml watch --no-up >/dev/null 2>&1 &
        FOCUS=${FOCUS} $DOCKER_COMPOSE_COMMAND \
            -f compose.yml \
            -f compose.dev.yml  \
            -f compose.services.yml \
            $GPU up ${ARG1} ;;
    "train" | "trial") 
        if [[ -z "$FOCUS" ]]; then
            echo "MODELS = ${MODELS}"
            read -p "Which model should we train? " FOCUS
        fi
        $DOCKER_COMPOSE_COMMAND \
            -f compose.yml \
            -f compose.services.yml up tbd ipf -d
        $DOCKER_COMPOSE_COMMAND \
            -f compose.yml \
            -f compose.dev.yml \
            $GPU run -e FOCUS=${FOCUS} -e TASK=${action} lab python3 harness.py ;;
    "prepare") 
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we prepare? " DIRECTORY
        fi
        $DOCKER_COMPOSE_COMMAND -f compose.yml -f compose.dev.yml run lab python3 /lab/${DATASET}/prepare.py ;;
    "fetch")
        if [[ -z "$DATASET" ]]; then
            read -p "Which dataset should we fetch? " DIRECTORY
        fi
        $DOCKER_COMPOSE_COMMAND  -f compose.yml -f compose.dev.yml run lab python3 /lab/${DATASET}/fetch.py ;;
    "prune")
        docker system prune -f && docker volume prune -f ;;
    "clean") 
        $DOCKER_COMPOSE_COMMAND \
            -f compose.yml \
            -f compose.dev.yml \
            exec lab python3 /src/edge/clean.py ;;
    "down")
        $DOCKER_COMPOSE_COMMAND down --remove-orphans ;;
    *) 
        echo "Invalid selection." ;;
esac
