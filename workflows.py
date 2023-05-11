# -*- coding: utf-8 -*-
import json
import time

import streamlit as st
from boltons.strutils import slugify

from kiara.api import KiaraAPI
from kiara.exceptions import InvalidPipelineStepConfig
import kiara_plugin.streamlit as kst

from util import (
    input_metadata_to_session_state,
    list_input_data_dir,
    load_and_parse_workflow_file,
    session_state_to_pipeline_config,
    write_example_data_files_to_github,
    write_file_to_github,
    write_input_metadata_file_to_github,
)

kst.init()

api: KiaraAPI = st.kiara.api

if "steps" in st.session_state.keys():
    steps = st.session_state["steps"]
else:
    steps = {}
    st.session_state["steps"] = steps

st.write("# Kiara workflow collection")
# TODO: explain what Kiara is and give a link to docs, explain what we mean by a workflow.

st.write(
    "Please tell us your email address to help us save and identify your workflows."
)
contact_email = st.text_input("Email address", key="contact_email")
workflow_title = st.text_input(
    "Short title for your workflow",
    key="workflow_title",
    placeholder="Topic modelling in Italian newspaper articles",
)

if not (workflow_title and contact_email):
    st.info("Please enter your email and workflow title, then press enter.")
else:
    workflow_base_path = f"{contact_email}/{slugify(workflow_title)}"
    workflow_pipeline_path = f"{workflow_base_path}/pipeline.json"
    workflow_data_path = f"{workflow_base_path}/data"
    already_uploaded_filenames = []

    edit = st.button("load existing workflow for editing?")
    if edit:
        with st.empty():
            st.info("Looking for existing workflow")
            try:
                load_and_parse_workflow_file(workflow_pipeline_path)
                already_uploaded_filenames = list_input_data_dir(workflow_data_path)
                input_metadata_to_session_state(workflow_data_path)
            except Exception as e:
                print(e)
                st.error(
                    "Something went wrong with loading your workflow. Please let the Kiara team know, and try again later."
                )

    st.write("## About your workflow")
    st.text_area(
        "Describe what your workflow achieves",
        key="workflow_description",
        height=100,
        placeholder="Performing text analysis tasks on a corpus of documents",
    )
    st.text_area(
        "What research questions does this workflow could help with?",
        key="workflow_research",
        height=100,
    )

    st.write("## Input data samples")
    input_details = st.text_area(
        label="Tell us about the input data for your workflow", key="input_details"
    )
    with st.expander("What should I write here?"):
        st.write(
            """Tell us as much as you can about the data you use as input for your workflow. This could include things like:
- Where does the data come from?
- What license does it have?
- What file format(s) is it in? How big are the files, how many files?
- What structural properties do these files have?
    - do the filenames mean something?
    - if there's a spreadsheet, what are the column headers?
    - if it represents network data, how many nodes and edges, does it have self-loops etc
"""
        )

    st.write(
        "If the data you use as input to your workflows is freely licensed, please upload a sample of it here."
    )
    input_data = st.file_uploader("Choose file(s)", accept_multiple_files=True)
    if already_uploaded_filenames:
        st.info(
            f"You've already uploaded these files:\n{''.join(already_uploaded_filenames)}"
        )

    save_input_data = st.button("Save input data information", type="primary")
    if save_input_data:
        with st.empty():
            st.info("Saving...")
            try:
                write_input_metadata_file_to_github(workflow_data_path, input_details)
                write_example_data_files_to_github(workflow_data_path, input_data)
                st.success("Saved input data information")
            except Exception as e:
                print(e)
                st.error(
                    "Something went wrong with saving your input data. Please let the Kiara team know, and try again later"
                )

    st.write("## Workflow steps")
    st.write("Describe the individual steps you do in your workflow at the moment.")
    for idx, step in steps.items():
        title, desc, inputs, outputs = (
            step["title"],
            step["desc"],
            step["inputs"],
            step["outputs"],
        )
        st.write(f"### Step {idx + 1}")
        steps[idx]["title"] = st.text_input(
            "What does this step do? (required)",
            value=title,
            key=f"title_step_{idx}",
            placeholder="Load network data into a Python data structure",
        )
        steps[idx]["inputs"] = step_input = st.text_area(
            "What are the inputs for this step?",
            value=inputs,
            key=f"inputs_step_{idx}",
            placeholder="Network data from journals, stored in 3 CSV files, which come from...",
        )
        steps[idx]["outputs"] = step_output = st.text_area(
            "What are the outputs of this step?",
            value=outputs,
            key=f"outputs_step_{idx}",
            placeholder="A networkX graph structure from ",
        )
        steps[idx]["desc"] = st.text_area(
            "Any technical details about how you do this step currently?",
            value=desc,
            key=f"desc_step_{idx}",
            placeholder="What existing software or packages do you use?",
        )

    add_step = st.button("Add step")
    if add_step:
        new_step_id = len(steps.keys())
        steps[new_step_id] = {"title": "", "desc": "", "inputs": "", "outputs": ""}
        st.write(st.session_state)
        st.experimental_rerun()

    create = st.button("Save workflow", type="primary")
    if create:
        with st.empty():
            st.info("Saving...")
            pipeline_config = None
            try:
                pipeline_config = session_state_to_pipeline_config()
                write_file_to_github(
                    workflow_pipeline_path, json.dumps(pipeline_config.dict(), indent=2)
                )
                st.success("Saved workflow")
                time.sleep(3)
                st.write("")
            except InvalidPipelineStepConfig:
                st.error(
                    "Couldn't save workflow. Please make sure all your steps have something in the required field 'What does this step do?'"
                )
            except Exception as e:
                print(e)
                st.error(
                    f"Something went wrong with saving your workflow. Please let the Kiara team know, and try again later.\nHere's a representation of your workflow, which you can send to the Kiara team: \n {pipeline_config.dict() if pipeline_config else st.session_state}"
                )

    st.warning(
        "Don't refresh the page or close this tab until you've saved your workflow!"
    )
