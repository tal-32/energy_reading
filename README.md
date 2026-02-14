# energy_reading

## srvices
*redis*  
remote directory service 

*producer*  
push enery consumption info to a redis-service

*consumer*  
pull enery consumption info from a redis-service

## tests
run `uv pytest` for unit tests
there is a e2e script for manual test, decided not to automate it
the e2e uses docker compose file

## docker
builder is `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
since it contains `uv` and other build requirements
runtime is `python:3.12-slim` since this is lightweight distro

*how to improve?*
We could build the app using `Nuitka` with a small refactor (unicorn under main)
or go all the way with `MonolithPy`, though I don't think this will be worth it

## helm
used version 4.1.1: https://get.helm.sh/helm-v4.1.1-linux-amd64.tar.gz
