import datetime
import json

from typing import Optional, List, Dict, Any

import streamlit as st
from boltons.strutils import slugify

from github import Github, UnknownObjectException
from github.ContentFile import ContentFile
from github.InputGitAuthor import InputGitAuthor
from githublfs import commit_lfs_file
from streamlit.elements.file_uploader import SomeUploadedFiles

from kiara_plugin.streamlit.modules import DummyModuleConfig


REPO_NAME = st.secrets.get("github_repo_path")
GITHUB_API_KEY = st.secrets.get("github_api_key")
BRANCH = "main"
COMMITTER = InputGitAuthor("kiara-streamlit", "streamlit@example.com")
# TODO are there better details we could use here ^^?

RESEARCH_QUESTIONS_DELIMITER = "\n## Research Questions\n"

github_client = Github(GITHUB_API_KEY)
repo = github_client.get_repo(REPO_NAME)


def fetch_existing_file_from_github(path: str) -> Optional[ContentFile]:
    try:
        file = repo.get_contents(path)
    except UnknownObjectException:
        return None
    return file


def write_existing_pipeline_data_to_state(data: Dict[Any, Any]) -> None:
    docs = f'{data["doc"]["description"]}\n{data["doc"]["doc"]}'.split(
        RESEARCH_QUESTIONS_DELIMITER
    )
    st.session_state.workflow_description = docs[0]
    if len(docs) > 1:
        st.session_state.workflow_research = docs[1]

    for i in range(len(data["steps"])):
        step_data = data["steps"][i]["module_config"]
        st.session_state["steps"][i] = {
            "title": step_data["title"].replace("_", " "),
            "desc": step_data["desc"],
            "inputs": step_data["inputs_schema"]["default"]["doc"],
            "outputs": step_data["outputs_schema"]["default"]["doc"],
        }


def state_steps_to_module_config() -> List[DummyModuleConfig]:
    steps_config = []
    for s in st.session_state.steps:
        step_data = st.session_state.steps[s]
        step_example = DummyModuleConfig(
            title=slugify(step_data["title"]),
            desc=step_data["desc"],
            inputs_schema={
                "default": {
                    "type": "any",
                    "optional": "true",
                    "doc": step_data["inputs"],
                },
            },
            outputs_schema={
                "default": {
                    "type": "any",
                    "optional": "true",
                    "doc": step_data["outputs"],
                },
            },
        )

        steps_config.append(step_example)
    return steps_config


def write_file_to_github(path: str, data) -> None:
    existing_file = fetch_existing_file_from_github(path)
    if existing_file:
        repo.update_file(
            path=existing_file.path,
            message=f"update data {datetime.datetime.utcnow()}",
            content=data,
            sha=existing_file.sha,
            branch=BRANCH,
            committer=COMMITTER,
            author=COMMITTER,
        )
    else:
        repo.create_file(
            path,
            message="create workflow",
            content=data,
            branch=BRANCH,
            committer=COMMITTER,
            author=COMMITTER,
        )


def write_example_data_file_to_github(target_directory: str, files: SomeUploadedFiles):
    for f in files:
        commit_lfs_file(
            repo=REPO_NAME,
            token=GITHUB_API_KEY,
            branch=BRANCH,
            path=f"{target_directory}/{f.name}",
            content=f.getvalue(),
            message=f"add input data: {f.name}",
        )


def load_and_parse_file(filepath: str):
    workflow_file = fetch_existing_file_from_github(filepath)
    if workflow_file:
        existing_data = json.loads(workflow_file.decoded_content.decode("utf-8"))
        write_existing_pipeline_data_to_state(existing_data)
        st.success("Loaded existing workflow")
    else:
        st.warning("No saved workflow found")


def serialize_workflow_to_github(filepath: str):
    pc = DummyModuleConfig.create_pipeline_config(
        st.session_state["workflow_title"],
        f"{st.session_state['workflow_description']}{RESEARCH_QUESTIONS_DELIMITER}{st.session_state['workflow_research']}",
        st.session_state["contact_email"],
        *state_steps_to_module_config(),
    )
    # st.kiara.pipeline_graph(pc) #  TODO connect step input to previous step output in order to make the graph useful?
    write_file_to_github(filepath, json.dumps(pc.dict(), indent=2))
    # TODO is there a way to exclude some of the duplicated info about steps here?
