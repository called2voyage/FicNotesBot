#!/bin/sh

DIR=$1
cd "$DIR"

python3 manage.py rundiscordbot
