# kiara_workflows_app

Streamlit app to help collect researcher workflows.

## Live version

The `main` branch of this repo is deployed [here on streamlit cloud](https://workflows.streamlit.app/), and writes the responses to [this repo on GitHub](https://github.com/DHARPA-Project/collected_workflows)

## Development

The `develop` branch of this repo is deployed [here on streamlit cloud](https://workflows-dev.streamlit.app/), and writes results to [this repo on Github](https://github.com/hostuser/workflows-dev).

To develop locally, you'll need to create a file `.streamlit/secrets.toml`, and write some secrets into it:

```toml
github_repo_path = "<your org>/<your repo name>"
github_api_key = "github_pat_XXXXXXXXXX"
```

`github_repo_path` is where the streamlit app will read and write responses.

`github_api_key` is a GitHub [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) with permissions to read and write files in the repo you specified in `github_repo_path`.

To run the app, install the requirements from `requirements.txt`, then run `streamlit run workflows.py`
