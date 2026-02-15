all commands are meant to be run from project root

## build
`uv sync --all-groups --all-packages`

## test
*unit test*
`uv run pytest`

## docker
*single app*  
`podman build -t energy_reading/producer:latest -f services/producer/Dockerfile .`

*stack*  
`podman-compose up -d`

## helm
`.helm/helm upgrade --install energy-reading ./charts/enery_reading`
