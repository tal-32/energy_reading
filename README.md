# energy_reading

## srvices
*redis*  
remote directory service 

*producer*  
push enery consumption info to a redis-service

*consumer*  
pull enery consumption info from a redis-service

*frontend*  
pretty ui

## tests
run `uv pytest` for unit tests
there is a e2e script for manual test, decided not to automate it
the e2e uses docker compose file

## docker
builder is `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
since it contains `uv` and other build requirements
runtime is `python:3.12-slim` since this is lightweight distro
