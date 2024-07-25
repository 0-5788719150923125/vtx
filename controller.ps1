$CONTAINERS = @("lab", "ctx", "uxo", "tbd", "ipf", "pet", "bit")
$MODELS = @("src", "aura", "genus", "frame", "mind", "heart", "soul", "envy", "chaos", "malice", "wisdom", "toe", "rot")

# Function to check if a command exists
function Test-Command($cmdName) {
    return $null -ne (Get-Command -Name $cmdName -ErrorAction Ignore)
}

# Check for docker
if (-not (Test-Command "docker")) {
    throw "Error: docker is not installed or not in PATH."
}

# Check for docker compose
if (Test-Command "docker-compose") {
    if (-not (Test-Command "docker compose")) {
        # Create a function to handle 'docker compose' commands
        function global:docker {
            param([Parameter(ValueFromRemainingArguments)]$params)
            if ($params[0] -eq "compose") {
                $composePlaceholder, $restParams = $params
                & docker-compose $restParams
            } else {
                & $env:COMSPEC /c "docker $params"
            }
        }
        Write-Host "Created function: 'docker compose' now routes to 'docker-compose'"
    } else {
        Write-Host "'docker compose' command is already available."
    }
} elseif (Test-Command "docker compose") {
    Write-Host "'docker compose' command is available."
} else {
    throw "Error: Neither 'docker-compose' nor 'docker compose' is installed or in PATH."
}

Write-Host "Docker and Docker Compose are properly set up."

# If defined, use the TASK variable.
if ($env:TASK) {
    $action = $env:TASK
} else {
    # Prompt for input.
    Write-Host "Use keywords to control the VTX:"
    Write-Host "(init)    Prepare this workspace."
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
    Write-Host "(clean)   Delete all checkpoints."
    Write-Host "(key)     Fetch your Urbit access key."
    Write-Host "(auto)    Turn on autopilot."
    Write-Host "(repair)  Force-fix this workspace."
    Write-Host "(update)  Pull all updates from git."

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
if ($env:ARCH -eq "ARM") {
    $GPU = '-f compose.ARM.yml'
} elseif ($env:DEVICE -eq "amd") {
    $GPU = '-f compose.amd.yml'
} elseif ($env:DEVICE -eq "intel") {
    $GPU = '-f compose.intel.yml'
} else {
    $GPU = '-f compose.nvidia.yml'
}

# Implement the controller
switch ($action) {
    {"repair","init","update" -contains $_} {
        git pull
        git submodule update --init --recursive
        git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'
        docker compose -f compose.yml -f compose.services.yml pull
    }
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
    {"up","auto" -contains $_} {
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
        $composeCommand = @(
            "docker", "compose",
            "-f", "compose.yml",
            "-f", "compose.dev.yml",
            "-f", "compose.services.yml"
        )
        if ($GPU) {
            $composeCommand += $GPU.Split()
        }
        $composeCommand += @("up", $ARG1)
        & $composeCommand
    }
    {"train","trial" -contains $_} {
        if (-not $env:FOCUS) {
            $FOCUS = Read-Host "Which model should we train? $($MODELS -join ', ')"
        }
        docker compose -f compose.yml -f compose.services.yml up -d tbd ipf
        docker compose -f compose.yml -f compose.dev.yml $GPU run -e FOCUS=$FOCUS -e TASK=$action lab python3 harness.py
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
    "clean" {
        docker compose -f compose.yml -f compose.dev.yml exec lab python3 /src/edge/clean.py
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