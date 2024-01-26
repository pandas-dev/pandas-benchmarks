import socket
from dotenv import load_dotenv
import os
from pathlib import Path
from dataclasses import dataclass

class Environment:
     
    def __init__(self):
        if socket.gethostname().startswith('Deas'):
            load_dotenv(dotenv_path= './local_env.yml')
        else:
            load_dotenv(dotenv_path= './server_env.yml')
    
        self.PANDAS_ASV_RESULTS_PATH = os.getenv("PANDAS_ASV_RESULTS_PATH")
        self.BENCHMARKS_FILE_PATH = os.getenv("BENCHMARKS_FILE_PATH")
        self.GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
        self.CONBENCH_RUN_REASON = os.getenv("CONBENCH_RUN_REASON")
        self.ASV_PROCESSED_FILES = os.getenv("ASV_PROCESSED_FILES")
        self.ALERT_PROCESSED_FILES = os.getenv("ALERT_PROCESSED_FILES")
    
def check_new_files(env):
    
    benchmarks_path = Path(env.PANDAS_ASV_RESULTS_PATH)
    all_files = [str(file) for file in benchmarks_path.glob('*.json')]
    with open(env.ASV_PROCESSED_FILES, "r+") as f:
        processed_files = f.read().split('\n')
        
    return all_files, processed_files

def alerts_done_file(env):

    _ , processed_files = check_new_files(env)
    with open(env.ALERT_PROCESSED_FILES, "r+") as f:
        alert_sent_files = f.read().split('\n')
    
    return alert_sent_files
