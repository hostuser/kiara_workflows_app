import datetime
import json
import string

from typing import Optional, List, Dict, Any

import streamlit as st
from boltons.strutils import slugify

from github import Github, UnknownObjectException
from github.ContentFile import ContentFile
from github.InputGitAuthor import InputGitAuthor
from githublfs import commit_lfs_file
from kiara.models.module.pipeline import PipelineConfig

from kiara_plugin.streamlit.modules import DummyModuleConfig
from streamlit.elements.widgets.file_uploader import SomeUploadedFiles

REPO_NAME = st.secrets.get("github_repo_path")
GITHUB_API_KEY = st.secrets.get("github_api_key")
BRANCH = "main"
COMMITTER = InputGitAuthor("kiara-streamlit", "streamlit@example.com")
# TODO are there better details we could use here ^^?

RESEARCH_QUESTIONS_DELIMITER = "\n## Research Questions\n"
INPUT_METADATA_FILENAME = "README.md"

github_client = Github(GITHUB_API_KEY)


def fetch_existing_file_from_github(
    path: str, repo
) -> Optional[ContentFile | List[ContentFile]]:
    try:
        file = repo.get_contents(path)
    except UnknownObjectException:
        return None
    return file


def pipeline_config_to_session_state(data: Dict[Any, Any]) -> None:
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


def session_state_to_pipeline_config() -> PipelineConfig:
    return DummyModuleConfig.create_pipeline_config(
        st.session_state["workflow_title"],
        f"{st.session_state['workflow_description']}{RESEARCH_QUESTIONS_DELIMITER}{st.session_state['workflow_research']}",
        st.session_state["contact_email"],
        *state_steps_to_module_config(),
    )


def write_file_to_github(path: str, data) -> None:
    repo = github_client.get_repo(REPO_NAME)
    existing_file = fetch_existing_file_from_github(path, repo)
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


def load_and_parse_workflow_file(filepath: str):
    repo = github_client.get_repo(REPO_NAME)
    workflow_file = fetch_existing_file_from_github(filepath, repo)
    if workflow_file:
        existing_data = json.loads(workflow_file.decoded_content.decode("utf-8"))
        pipeline_config_to_session_state(existing_data)
        st.success("Loaded existing workflow")
    else:
        st.warning("No saved workflow found")


def write_input_metadata_file_to_github(workflow_data_path: str, input_details: str):
    write_file_to_github(
        f"{workflow_data_path}/{INPUT_METADATA_FILENAME}", input_details
    )


def serialize_workflow_to_github(filepath):
    workflow_doc = f"{st.session_state['workflow_description']}{RESEARCH_QUESTIONS_DELIMITER}{st.session_state['workflow_research']}"
    author = f'{st.session_state["contact_email"]} - contact consent given: {st.session_state["contact_consent"]}'
    pc = DummyModuleConfig.create_pipeline_config(
        st.session_state["workflow_title"],
        workflow_doc,
        author,
        *state_steps_to_module_config(),
    )
    # st.kiara.pipeline_graph(pc) #  TODO connect step input to previous step output in order to make the graph useful?
    write_file_to_github(filepath, json.dumps(pc.dict(), indent=2))
    # TODO is there a way to exclude some of the duplicated info about steps here?


def write_example_data_files_to_github(target_directory: str, files: SomeUploadedFiles):
    for f in files:
        commit_lfs_file(
            repo=REPO_NAME,
            token=GITHUB_API_KEY,
            branch=BRANCH,
            path=f"{target_directory}/{f.name}",
            content=f.getvalue(),
            message=f"add input data: {f.name}",
        )


def list_input_data_dir(directory_path: str) -> List[str]:
    """Return a list of markdown bullet points for each file in the input data directory for that workflow"""
    repo = github_client.get_repo(REPO_NAME)
    response = fetch_existing_file_from_github(directory_path, repo)
    if response:
        return [
            f"- {f.path.replace(directory_path + '/', '')}\n"
            for f in response
            if f.path.replace(directory_path + "/", "") != INPUT_METADATA_FILENAME
        ]
    return []


def input_metadata_to_session_state(directory_path: str) -> None:
    repo = github_client.get_repo(REPO_NAME)
    response: Optional[ContentFile] = fetch_existing_file_from_github(
        directory_path + "/" + INPUT_METADATA_FILENAME, repo
    )
    if response:
        st.session_state["input_details"] = response.decoded_content.decode("utf-8")


def string_to_safe_directory_name(inp: str) -> str:
    """Naive way to turn an arbitrary string into something that can be used as a directory name"""
    safe_chars = string.ascii_letters + string.digits + " -_.@"
    filtered = "".join([c for c in inp if c in safe_chars]).strip()
    return filtered if 0 < len(filtered) < 128 else "unknown_user"


def session_state_to_txt() -> str:
    summary = f'# {st.session_state.get("workflow_title")}\n\n{st.session_state.get("workflow_description").strip()}'
    about = f'## Research questions\n\n{st.session_state.get("workflow_research")}'
    inputs = f'## Input data\n\n{st.session_state.get("input_details")}'
    sections = [summary, about, inputs, "## Steps"]
    for step_idx in st.session_state.get("steps").keys():
        step = st.session_state.get("steps")[step_idx]
        sections.append(
            f"""### {step['title']}\n{step.get('desc') if step.get('desc') else ''}
- Inputs: {step.get('inputs') if step.get('inputs') else 'not specified'}
- Outputs: {step.get('outputs') if step.get('outputs') else 'not specified'}"""
        )
    return "\n\n".join(sections)
