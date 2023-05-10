# -*- coding: utf-8 -*-
import time

import streamlit as st
from boltons.strutils import slugify

from kiara.api import KiaraAPI

import kiara_plugin.streamlit as kst

from util import load_and_parse_file, serialize_workflow_to_github


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

    edit = st.button("load existing workflow for editing?")
    if edit:
        load_and_parse_file(workflow_pipeline_path)

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

    st.write("## Workflow steps")
    st.write("Describe the individual steps you do in your workflow at the moment.")

    # TODO give example steps in an expander and/or placeholders here?

    for idx, step in steps.items():
        title, desc, inputs, outputs = (
            step["title"],
            step["desc"],
            step["inputs"],
            step["outputs"],
        )
        st.write(f"### Step {idx + 1}")
        steps[idx]["title"] = st.text_input(
            "What does this step do?",
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
            "Any technical details about how you do this step currently? (optional)",
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
        serialize_workflow_to_github(workflow_pipeline_path)
        toast = st.empty()
        toast.success("Saved workflow")
        time.sleep(3)
        toast.write("")

    st.warning(
        "Don't refresh the page or close this tab until you've saved your workflow!"
    )
