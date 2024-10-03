#!/bin/bash

# Update this to what you are using - finch or docker

TOOL='finch'
#TOOL='docker'

echo "Using $TOOL for container operations"

$TOOL compose -p local-postgres -f postgres.yaml up