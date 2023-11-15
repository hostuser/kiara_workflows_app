# kiara_workflows_app

Streamlit app to help collect researcher workflows.

## Deployed versions

The `main` branch of this repo is deployed [here on streamlit cloud](https://workflows.streamlit.app/), and writes the responses to [this repo on GitHub](https://github.com/DHARPA-Project/collected_workflows)

The `develop` branch of this repo is deployed [here on streamlit cloud](https://workflows-dev.streamlit.app/), and writes results to [this repo on Github](https://github.com/hostuser/workflows-dev).

## Local development

### Prepare github secrets

To develop locally, you'll need to create a file `.streamlit/secrets.toml`, and write some secrets into it:

```toml
github_repo_path = "<your org>/<your repo name>"
github_api_key = "github_pat_XXXXXXXXXX"
```

`github_repo_path` is where the streamlit app will read and write responses.

`github_api_key` is a GitHub [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token), created for the account/organization which owns the repo you specified in `github_repo_path`, and with permissions to read and write files in that repo .


### Setup local Python enviornment

#### Using pixi (recommended)

##### macOS and Linux

To install Pixi on macOS and Linux, open a terminal and run the following command:
```bash
curl -fsSL https://pixi.sh/install.sh | bash
# or with brew
brew install pixi
```
The script will also update your ~/.bash_profile to include ~/.pixi/bin in your PATH, allowing you to invoke the pixi command from anywhere.
You might need to restart your terminal or source your shell for the changes to take effect.

##### Windows
To install Pixi on Windows, open a PowerShell terminal (you may need to run it as an administrator) and run the following command:

```powershell
iwr -useb https://pixi.sh/install.ps1 | iex
```
The script will inform you once the installation is successful and add the ~/.pixi/bin directory to your PATH, which will allow you to run the pixi command from any location.


##### Initialize environemnt and run the app

The following command needs to be run only once, to initialize the environment:

```
pixi run install-env
```

After this, you can always run the app with:

```
pixi run workflows-app
```


#### Using conda / virtualenv

Setup a Python environemnt as you usually do, and install the requirements from `requirements.txt`.

Then, run the app:

```
streamlit run workflows.py
```
