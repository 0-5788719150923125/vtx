$CONTAINERS = @("lab", "ctx", "uxo", "tbd", "ipf", "pet", "bit")
$MODELS = @("src", "genus", "frame", "mind", "heart", "soul", "envy", "chaos", "malice", "wisdom", "pain", "toe", "rot")

# Function to check if a command exists
function Test-Command($cmdName) {
    return $null -ne (Get-Command -Name $cmdName -ErrorAction Ignore)
}

# Check for docker
if (-not (Test-Command "docker")) {
    throw "Error: docker is not installed or not in PATH."
}

# Check for docker compose and set $DOCKERCOMPOSE
if (Test-Command "docker compose") {
    $DOCKERCOMPOSE = @("docker", "compose")
    Write-Host "'docker compose' command is available."
} elseif (Test-Command "docker-compose") {
    $DOCKERCOMPOSE = @("docker-compose")
    Write-Host "'docker-compose' command is available."
} else {
    throw "Error: Neither 'docker-compose' nor 'docker compose' is installed or in PATH."
}

Write-Host "Docker and Docker Compose are properly set up."

# Function to create and execute docker compose command
function Get-DockerComposeCommand {
    param (
        [string[]]$AdditionalArgs
    )
    $baseCommand = $DOCKERCOMPOSE + @(
        "-f", "compose.yml",
        "-f", "compose.dev.yml",
        "-f", "compose.services.yml"
    )
    if ($GPU) {
        $baseCommand += $GPU.Split()
    }
    $fullCommand = $baseCommand + $AdditionalArgs
    
    # Join the command parts into a single string
    $commandString = $fullCommand -join ' '
    
    Write-Host "Executing command: $commandString" -ForegroundColor Yellow
    
    # Execute the command
    Invoke-Expression $commandString
}

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
    Write-Host "(auto)    Turn on autopilot."
    Write-Host "(repair)  Force-fix this workspace."
    Write-Host "(update)  Pull all updates from git."

    $action = Read-Host "Enter the keyword corresponding to your desired action"
}

# Import variables
if (-not (Test-Path '.env')) {
    New-Item -Path '.env' -ItemType 'file' -Force
}

# Function to read .env file and set environment variables
function Set-EnvFromFile {
    param (
        [string]$EnvFile = ".env"
    )
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove surrounding quotes if present
                $value = $value -replace '^["''](.*)["'']$', '$1'
                # Set as environment variable
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "Set $name=$value"
            }
        }
    } else {
        Write-Host "Warning: .env file not found. Creating an empty one."
        New-Item -Path $EnvFile -ItemType File -Force
    }
}

# Import variables from .env file
Set-EnvFromFile

# Setup config file
if (-not (Test-Path 'config.yml')) {
    New-Item -Path 'config.yml' -ItemType 'file' -Force
}

function Get-UserFocus {
    $userFocus = $env:FOCUS
    if ([string]::IsNullOrWhiteSpace($userFocus)) {
        $userFocus = Read-Host "Which model should we focus on? $($MODELS -join ', ')"
        $env:FOCUS = $userFocus
    }
    return $userFocus
}

# Set GPU mode
if ($env:ARCH -eq "ARM") {
    $GPU = '-f compose.ARM.yml'
} elseif ($env:DEVICE -eq "amd") {
    $GPU = '-f compose.amd.yml'
} elseif ($env:DEVICE -eq "intel") {
    $GPU = '-f compose.intel.yml'
} elseif ($env:DEVICE -eq "cpu") {
    $GPU = ''
} else {
    $GPU = '-f compose.nvidia.yml'
}

# Implement the controller
switch ($action) {
    {$_ -in "repair","init","update"} {
        git pull
        git submodule update --init --recursive
        git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'
        & Get-DockerComposeCommand "pull"
    }
    "ps" {
        & Get-DockerComposeCommand "ps"
    }
    "logs" {
        & Get-DockerComposeCommand "logs" "--follow"
    }
    "stats" {
        docker stats
    }
    "exec" {
        if (-not $env:CONTAINER) {
            $env:CONTAINER = Read-Host "Which container should we enter? $($CONTAINERS -join ', ')"
        }
        & Get-DockerComposeCommand "exec" $env:CONTAINER "/bin/bash"
    }
    "test" {
        & Get-DockerComposeCommand "exec" "lab" "robot" "--outputdir" "/book/static/tests" "/src/tests"
    }
    "eval" {
        & Get-DockerComposeCommand "exec" "lab" "sh" "tests/eval.sh"
    }
    "build" {
        & Get-DockerComposeCommand "build"
        docker images | Select-String "/lab"
    }
    "push" {
        & Get-DockerComposeCommand "push"
    }
    "pull" {
        & Get-DockerComposeCommand "pull"
    }
    {$_ -in "up","auto"} {
        $focus = Get-UserFocus
        $upArgs = @("up")
        if ($action -eq "auto") {
            $upArgs += "-d"
        }
        & Get-DockerComposeCommand $upArgs
    }
    {$_ -in "train","trial"} {
        if (-not $env:FOCUS) {
            $env:FOCUS = Read-Host "Which model should we train? $($MODELS -join ', ')"
        }
        & Get-DockerComposeCommand "up" "-d" "tbd" "ipf"
        & Get-DockerComposeCommand "run" "-e" "FOCUS=$env:FOCUS" "-e" "TASK=$action" "lab" "python3" "harness.py"
    }
    "prepare" {
        if (-not $env:DATASET) {
            $env:DATASET = Read-Host "Which dataset should we prepare?"
        }
        & Get-DockerComposeCommand "run" "lab" "python3" "/lab/$env:DATASET/prepare.py"
    }
    "fetch" {
        if (-not $env:DATASET) {
            $env:DATASET = Read-Host "Which dataset should we fetch?"
        }
        & Get-DockerComposeCommand "run" "lab" "python3" "/lab/$env:DATASET/fetch.py"
    }
    "prune" {
        docker system prune -f
        docker volume prune -f
    }
    "clean" {
        & Get-DockerComposeCommand "exec" "lab" "python3" "/src/edge/clean.py"
    }
    "down" {
        & Get-DockerComposeCommand "down" "--remove-orphans"
    }
    Default {
        Write-Host "Invalid selection."
    }
}