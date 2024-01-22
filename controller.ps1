$CONTAINERS = @("lab", "ctx", "uxo", "tbd", "ipf", "pet", "bit")
$MODELS = @("src", "aura", "frame", "ode", "mind", "heart", "soul", "envy", "chaos", "ghost", "malice", "toe")

# Check for docker
if (!(Test-Path -Path "docker.exe")) {
  Write-Error "Error: docker is not installed or not in PATH."
  exit 1
}

# Check for docker-compose
if (!(Test-Path -Path "docker-compose.exe")) {
  Write-Error "Error: docker-compose is not installed or not in PATH."
  exit 1
}

# If defined, use the TASK variable.
if ($env:TASK) {
    $action = $env:TASK
} else {
    # Prompt for input.
    Write-Host "Use keywords to control the VTX:"
    Write-Host "(ps)      View a list of all running containers."
    Write-Host "(stats)   View live Docker stats."
    Write-Host "(logs)    View logs for all services."
    Write-Host "(exec)    Open an interactive shell in the specified container."
    Write-Host "(build)   Build this project in Docker."
    Write-Host "(test)    Run all tests."
    Write-Host "(eval)    Run evaluation harness."
    Write-Host "(push)    Push the newly-built Docker image to a registry."
    Write-Host "(pull)    Pull the latest Docker images required by this project."
    Write-Host "(up)      Bring the stack online."
    Write-Host "(down)    Stop the service in Docker."
    Write-Host "(fetch)   Download a dataset."
    Write-Host "(prepare) Prepare a dataset."
    Write-Host "(train)   Train a model."
    Write-Host "(trial)   Search for optimal hyperparameters."
    Write-Host "(prune)   Prune all unused images, networks, and volumes."
    Write-Host "(key)     Fetch your Urbit access key."

    $action = Read-Host "Enter the keyword corresponding to your desired action"
}

# Import variables
if (-not (Test-Path '.env')) {
    New-Item -Path '.env' -ItemType 'file' -Force
}

. '.env'

# Setup config file
if (-not (Test-Path 'config.yml')) {
    New-Item -Path 'config.yml' -ItemType 'file' -Force
}

# Set GPU mode
if ($env:DEVICE -ne "cpu") {
    $GPU = '-f compose.gpu.yml'
}

# Implement the controller
switch ($action) {
    "ps" {
        docker compose ps
    }
    "logs" {
        docker compose logs --follow
    }
    "stats" {
        docker stats
    }
    "exec" {
        if (-not $env:CONTAINER) {
            $CONTAINER = Read-Host "Which container should we enter? $($CONTAINERS -join ', ')"
        }
        docker compose exec $CONTAINER /bin/bash
    }
    "test" {
        docker compose exec lab robot --outputdir /book/static/tests /src/tests
    }
    "eval" {
        docker compose exec lab sh tests/eval.sh
    }
    "build" {
        docker compose build
        docker images | Select-String "/lab"
    }
    "push" {
        docker compose push
    }
    "pull" {
        docker compose -f compose.yml -f compose.services.yml pull
    }
    "up", "auto" {
        if (-not $env:FOCUS) {
            $FOCUS = Read-Host "Which model should we focus on? $($MODELS -join ', ')"
        }
        if ($action -eq "auto") {
            $DETACHED = $true
        }
        if ($DETACHED) {
            $ARG1 = '-d'
        }
        $env:FOCUS = $FOCUS
        # Start-Process docker compose -f compose.yml -f compose.dev.yml -f compose.services.yml watch --no-up -NoNewWindow -RedirectStandardOutput /dev/null -RedirectStandardError /dev/null
        docker compose -f compose.yml -f compose.dev.yml -f compose.services.yml $GPU up $ARG1
    }
    "train", "trial" {
        if (-not $env:FOCUS) {
            $FOCUS = Read-Host "Which model should we train? $($MODELS -join ', ')"
        }
        docker compose -f compose.yml -f compose.services.yml up -d tbd ipf opt
        docker compose -f compose.yml -f compose.dev.yml -f compose.train.yml $GPU run -e FOCUS=$FOCUS -e TASK=$action lab python3 harness.py
    }
    "prepare" {
        if (-not $env:DATASET) {
            $DATASET = Read-Host "Which dataset should we prepare?"
        }
        docker compose -f compose.yml -f compose.dev.yml run lab python3 /lab/$DATASET/prepare.py
    }
    "fetch" {
        if (-not $env:DATASET) {
            $DATASET = Read-Host "Which dataset should we fetch?"
        }
        docker compose -f compose.yml -f compose.dev.yml run lab python3 /lab/$DATASET/fetch.py
    }
    "prune" {
        docker system prune -f
        docker volume prune -f
    }
    "key" {
        docker compose exec urb /bin/get-urbit-code
    }
    "down" {
        docker compose down --remove-orphans
    }
    Default {
        Write-Host "Invalid selection."
    }
}
