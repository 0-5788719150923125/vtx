*** Settings ***
Library    ../common.py

*** Test Cases ***
Create hash from string
    ${result}    deterministic_short_hash   myString
    SHOULD BE EQUAL     ${result}         907da3a

Run a shell command
    ${result}    run_shell_command    echo "hello world"
    SHOULD BE TRUE    ${result[0]} 

Get a NIST beacon
    ${result}    nist_beacon
    SHOULD BE TRUE    ${result[0]}

Remove emojis and symbols
    ${result}    strip_emojis    I'm sorry, but "REMpty Syndrome" is a brilliant pun.🤣
    SHOULD BE EQUAL    ${result}    I'm sorry, but "REMpty Syndrome" is a brilliant pun.

Generate a random string
    ${result}    random_string    10
    ${length}    GET LENGTH    ${result}
    SHOULD BE EQUAL AS INTEGERS    ${length}    10

Generate a daemon name
    ${result}    get_daemon    Ryan
    SHOULD BE EQUAL    ${result}    Amorsus

List every file in a directory recursively
    ${result}    list_full_paths    '/src'
    LOG MANY    ${result}