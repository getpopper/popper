from datetime import datetime, timedelta

from popper.airflow import make_airflow_dag

# assume AIRFLOW_HOME/dags/ looks like the following
#
# AIRFLOW_HOME/
#   airflow.db
#   airflow.cfg
#   dags/
#     myrepo/
#       wf.yml
#       input.json
#       another_input.txt
#       ...
#
# in the above, myrepo/ is a repository that has popper workflows in. In order to run
# a popper workflow as an airflow pipeline, we drop this popper_dag.py file inside the
# AIRFLOW_HOME/dags/ folder.
#
# An alternative is to make the entire AIRFLOW_HOME/dags a mono repository, and thus
# this popper_dag.py would also live in Git. There are many other ways in which the
# dags/ folder gets synchronized depending on the infrastructure where Airflow is
# running, thus we treat it as an orthogonal issue. From the point of view of Popper,
# what it matters is that all the files that the pipeline is referencing are available
# in the dags/ folder.

default_args = {
    "owner": "me",
    "description": "run popper workflow",
    "depend_on_past": False,
    "start_date": datetime(2015, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=0),
    # parameters for popper
    "wf_file": "myrepo/wf.yml",
    "workspace_dir": "myrepo/",
}

# configuring the wf_file and workspace_dir as shown above is equivalent to doing:
#
#   cd $AIRFLOW_HOME/dags
#   popper run -f myrepo/wf.yml -w myrepo/
#

dag_id = "mytest"
schedule_interval = "5 8 0 0 3"

dag, tasks = make_airflow_dag(dag_id, schedule_interval, default_args=default_args)
