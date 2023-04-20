# -*- coding: utf-8 -*-
import datetime
import json
import time
from typing import Optional

import streamlit as st
from boltons.strutils import slugify

# pip install PyGithub
from github import Github, UnknownObjectException
from github.ContentFile import ContentFile
from github.InputGitAuthor import InputGitAuthor
from kiara.api import KiaraAPI

import kiara_plugin.streamlit as kst
from kiara_plugin.streamlit.modules import DummyModuleConfig

# Write a secrets file that looks like
# github_api_key = "ghp_XXXXXXXXXXXXXX"
# ^^ a personal access token with at least repo:write permissions on the repo below
# github_repo_path = "caro401/kiara-workflow-test"
REPO_NAME = st.secrets.get("github_repo_path")
GITHUB_API_KEY = st.secrets.get("github_api_key")

COMMITTER = InputGitAuthor("kiara-streamlit", "streamlit@example.com")
# TODO are there better details we could use here ^^?

github_client = Github(GITHUB_API_KEY)
repo = github_client.get_repo(REPO_NAME)

kst.init()


def fetch_existing_file_from_github(path: str) -> Optional[ContentFile]:
    try:
        file = repo.get_contents(path)
    except UnknownObjectException:
        return None
    return file


def write_file_to_github(path: str, data) -> None:
    existing_file = fetch_existing_file_from_github(path)
    if existing_file:
        repo.update_file(
            path=existing_file.path,
            message=f"update data {datetime.datetime.utcnow()}",
            content=data,
            sha=existing_file.sha,
            branch="main",
            committer=COMMITTER,
            author=COMMITTER,
        )
    else:
        repo.create_file(
            path,
            message="create workflow",
            content=data,
            branch="main",
            committer=COMMITTER,
            author=COMMITTER,
        )


api: KiaraAPI = st.kiara.api

# example of how to do introspection of kiara environment
# data_types = api.list_data_type_names()
# st.selectbox("Select data type", data_types, key="data_type")
# ops = api.list_operation_ids()
# op = st.selectbox("Select operations", ops, key="ops")
# st.kiara.item_info(op)

st.write("# Kiara workflow form")
st.error(
    "TODO: explain what Kiara is and give a link to docs, explain what we mean by a workflow."
)
st.write(
    "Please tell us your email address to help us save and identify your workflows. We may get in touch for "
    "follow-up questions, but we won't share your data at all."
)
contact_email = st.text_input("Email address")
workflow_title = st.text_input(
    "Short title for your workflow",
    placeholder="Topic modelling in Italian newspaper articles",
)

placeholder = st.empty()
placeholder.info("Please enter your email and workflow title, then press enter.")
if workflow_title and contact_email:
    workflow_path = f"{contact_email}/{slugify(workflow_title)}.json"

    if "workflow_description" not in st.session_state:
        placeholder.write("Looking for existing workflow data")
        workflow_file = fetch_existing_file_from_github(workflow_path)
        if workflow_file:
            existing_data = json.loads(workflow_file.decoded_content.decode("utf-8"))
            st.session_state.workflow_description = existing_data["doc"]["description"]

    with placeholder.container():
        workflow_description = st.text_area(
            "Describe your workflow, in as much detail as you can",
            key="workflow_description",
            height=100,
        )
        with st.expander("What should I write here?"):
            st.write(
                """You could (but don't have to) include things like: 
- What is the research question you are working on with the data you produce from this workflow? 
- Are there any special concepts or details of your research domain that are relevant to this workflow?
- Where does your input data come from, what format is it in and how large is it?
- What are the steps in your workflow, what kind of tasks do you do at each step? 
- Who currently does these tasks, what tools or software do you use?
- What is the format of the data you get at the end of your workflow? What do you do next with this data?
- Is anything particularly difficult, time-consuming or annoying in your workflow?

Don't worry if you don't know, or don't want to share, any of these things. 
Any information you can give is useful and will help guide the Kiara roadmap.
"""
            )

        # TODO collect individual step information
        # step_details = st.button('Add internal step')
        # if step_details:
        #     st.write('## some steps here')
        # do some caching here
        # req1 = st.kiara.step_requirements(key="req1")
        # req2 = st.kiara.step_requirements(key="req2")

        create = st.button("Save workflow")
        if create:
            pc = DummyModuleConfig.create_pipeline_config(
                workflow_title, workflow_description, contact_email
            )
            # st.kiara.pipeline_graph(pc)
            write_file_to_github(workflow_path, pc.json())

            toast = st.empty()
            toast.success("Saved workflow")
            time.sleep(3)
            toast.write("")

        st.warning(
            "Don't refresh the page or close this tab until you've saved your workflow!"
        )
