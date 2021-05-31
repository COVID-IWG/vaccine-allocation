import datetime
import json
import os

import requests
from airflow import models
from airflow.models.connection import Connection
from airflow.hooks.http_hook import HttpHook
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.dummy_operator import DummyOperator

AUDIENCE_ROOT = os.environ["GCF_URL"]
METADATA_ROOT = os.environ["METADATA"]

class CloudRun(SimpleHttpOperator):
    ui_color = "#175AE1"
    template_fields = ["branch"]
    
    def __init__(self,
        run_url = "vaccine-allocation-sipjq3uhla-uc.a.run.app", 
        conn_id = "vaccine-allocation-cloud-run", 
        branch = "{{ dag_run.conf.get('branch', '') }}",
        *args, **kwargs
    ):
        conn = Connection(
            conn_id   = conn_id,
            conn_type = "http",
            host      = run_url,
            schema    = "https"
        )
        kwargs["http_conn_id"] = conn_id
        super(CloudRun, self).__init__(*args, **kwargs)
        self.run_url = run_url
        self.branch  = branch

    def get_metadata_url(self):
        prefix = self.branch + "---" if self.branch else ""
        return f"{METADATA_ROOT}https://{prefix}{self.run_url}"
    
    def execute(self, context):
        token = requests.get(self.get_metadata_url(), headers = {"Metadata-Flavor": "Google"}).text
        HttpHook(self.method, http_conn_id = self.http_conn_id)\
            .run(self.endpoint, self.data, {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, self.extra_options)

def epi_step(state, district):
    pass 

def econ_step(state, district):
    pass 

def figures(state = None, district = None):
    pass

with models.DAG("vaccine-allocation", schedule_interval = None, catchup = False) as dag:
    root = DummyOperator(task_id = "root")
    natl_figures = figures()
    
    for state in []:
        state_root = DummyOperator(task_id = state)
        root >> state_root

        state_figures = figures(state = state)

        for district in []:
            state_root >> epi_step(state, district) >> econ_step(state, district) >> [
                natl_figures,
                state_figures, 
                figures(state = state, district = district)
            ]
