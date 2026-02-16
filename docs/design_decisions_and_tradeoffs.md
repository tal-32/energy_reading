## structure:
├── charts                    # helm
├── docker-compose.yaml       # podman-compose for easier quick and dirty debug
├── docs                      # information could place pydoc here
├── manual_tests              # these tests require some env configuration. They should be automated. But wanted to speed things up
├── services                  # apps
│   ├── consumer
│   ├── producer
├── shared_lib                # model and utils
├── tests                     # unit tests

- I chose to separate the app dependencies. separation make it easier to work on each component and do a sync only when working on shared info

## work process
I worked in the following order
- planning and tool setup (linter, debug and pre-commit-config)
- producer
- consumer
- docker-compose
- helm
- autoscaling
- ui
- ci

this allows to work on each component with little change to other, but comes with some tradeoff that 2e2 got delayed and some redis syntax was missed until later

## tests
unit tests were fairly easy to add. there were manual test that are worth moving to automation but decided not to for now since I wanted to speed things up and thought it would take longer to setup an env with the required tools 

## podman
use podman since it is free regardless of scale but has it's quirks
example how podman and kind handle images
It caused me issue with some testing and I ended up validating with Azure VM and docker

*KEDA scaling*  
encountered issue with testing this
was not straight forward as I thought
I had to move on, because it took too much time 

## container image
The build image is python slim + building tools
I made 2 stages dependencies and build for cache layers 
`unicorn` was only included in the container

*exec on import*  
`fastapi` recommendation is to call on import, which bugged me
I would liked to make it a lazy call since so many dev tools relay on import
I would probably change it for real production

## TODO
- `version` should be centrlized. there should be one place that will affect all. 
  docker tag, app version etc. It should also be auto incremented when comitting to main
- for external api calls I added a verion as optional param. The idea is that the
  program evolves and api might change at some point. this is backward compadibility 
  call
- add additional `check` api, like testing connections.it should be separated from `/health_check`
- add trace log
- automate manual tests

## overkill
Since I assumed this is going to the cloud I fiddled with `Nuitka` to see the tradeoff
goining all out to  `MonolithPy`, is nice but very hard to maintain
