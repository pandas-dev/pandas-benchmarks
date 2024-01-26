from asvbench import AsvBenchmarkAdapter
from pathlib import Path
import os
import time
import alert
from utilities import Environment, check_new_files

env = Environment()

def adapter_instance(file_to_read) -> None:
    adapter = AsvBenchmarkAdapter(
    command=["echo", str(file_to_read)],
    result_file=Path(file_to_read),
    result_fields_override={
        "run_reason": env.CONBENCH_RUN_REASON,
    },
    benchmarks_file_path=env.BENCHMARKS_FILE_PATH,
    )
    adapter.run()
    adapter.post_results()


def post_data() -> None:
   
   while True:
       all_files, processed_files = check_new_files(env)
       for new_file in (set(all_files) - set(processed_files)):
           adapter_instance(new_file)
           with open(env.ASV_PROCESSED_FILES, "a") as f:
               f.write(new_file)
               f.write("\n") 
       time.sleep(30) #adjust this on server

if __name__=="__main__":
    post_data()
        
