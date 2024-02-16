## Developing with Visual Studio Code + devcontainer

The easiest way to get started with custom integration development is to use Visual Studio Code with devcontainers. This approach will create a preconfigured development environment with all the tools you need.

**Prerequisites**

- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Docker
  -  For Linux, macOS, or Windows 10 Pro/Enterprise/Education use the [current release version of Docker or Podman](https://docs.docker.com/install/)
  -   Windows 10 Home requires [WSL 2](https://docs.microsoft.com/windows/wsl/wsl2-install) and the current Edge version of Docker Desktop (see instructions [here](https://docs.docker.com/docker-for-windows/wsl-tech-preview/)). This can also be used for Windows Pro/Enterprise/Education.
- [Visual Studio code](https://code.visualstudio.com/)
- [Remote - Containers (VSC Extension)][extension-link]

[More info about requirements and devcontainer in general](https://code.visualstudio.com/docs/remote/containers#_getting-started)

[extension-link]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers

**Getting started:**

1. Fork the repository.
2. Clone the repository to your computer.
3. Copy the devcontainer-template.json to .devcontainer.json in the root directory
4. Edit the .devcontainer.json depending on podman or docker (instructions in the json file)
5. Re-Open the repository using Visual Studio code.

NOTE: Podman requires additional setup to tell VS Code that you are using Podman and not Docker.

When you open this repository with Visual Studio code you are asked to "Reopen in Container", this will start the build of the container.

_If you don't see this notification, open the command palette and select `Remote-Containers: Reopen Folder in Container`._

When starting the program scripts/setup will auto run and generate a self signed ssl certificate.


### Running Home Assistant

To run home assistant edit the devcontainer.json file and change the BUILD_TYPE to "run".  Rebuild the container and then in a terminal start home assistant using scripts/run.

NOTE: This will take a while to start and give lots of errors, once started up I suggest stopping it CTRL-C, re open visual code and restart home assistant with scripts/run.

Once Started you can access by: https://localhost:8123


### Versioning

To bump version we can use the tool bumpver, this should only be done by the repo owner, this will update all version requirements, These will auto submitted and a tag created ready to create a release.

All examples include -d which is test mode it does not commit, remove the -d to perform the update and commit/ create tag.

* Bump Patch (Beta)           - bumpver update -d -p -t beta
* Bump Patch (Beta Increment) - bumpver update -d --tag-num
* Bump Patch (Final)          - bumpver update -d -t final

* Bump Minor (same as above)  - bumpver update -d -m (extra Opts as above)
* Bump Major (same as above)  - bumpver update -d -major (extra opts as above)


### Unit Testing

Not currently set up.


### Step by Step debugging

To Setup debugging in run mode you need to create or add to the .vscode/launch.json file the following from the section "configruations":

```
{
  // Use IntelliSense to learn about possible attributes.
  // Hover to view descriptions of existing attributes.
  // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
  "version": "0.2.0",
  "configurations": [
    {
      // Debug by attaching to local Home Assistant server using Remote Python Debugger.
      // See https://www.home-assistant.io/integrations/debugpy/
      "name": "Home Assistant: Attach Local",
      "type": "python",
      "request": "attach",
      "port": 5678,
      "host": "localhost",
      "justMyCode": false,
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "."
        }
      ]
    }
  ]
}
```

In Addition you have to setup home assistant to start debugpy, the configuration.yaml file is auto created and looks as follows:

```
# https://www.home-assistant.io/integrations/default_config/
default_config:

homeassistant:
  external_url: "http://localhost:8123"
  internal_url: "http://localhost:8123"

http:
  ssl_certificate: ./ssl/fullchain.pem
  ssl_key: ./ssl/privkey.pem

# Enable to initiate debugging in Home Assistant Runtime
debugpy:
  start: false
  wait: false

# https://www.home-assistant.io/integrations/logger/
logger:
  default: warning
  logs:
    custom_components.miele: debug
```

You can change the section debugpy to start debug and optionally wait until you connect a debugger before continuing:

```
# Enable to initiate debugging in Home Assistant Runtime
debugpy:
  start: true
  wait: true
```

You need to restart vs code and then start home assistant to continue.
