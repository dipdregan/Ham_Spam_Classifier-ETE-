import os
from pathlib import Path

project_name = 'src'

list_of_files = [
    ".github/workflows/.gitkeep",
    f"{project_name}/__init__.py",
    f"{project_name}/constant/__init__.py",
    f"{project_name}/constant/constants.py",
    f"{project_name}/entity/config_entity.py",
    f"{project_name}/entity/artifact_entity.py",
    f"{project_name}/components/__init__.py",
    f"{project_name}/components/data_ingetion.py",
    f"{project_name}/components/data_validation.py",
    f"{project_name}/components/data_trasnformation.py",
    f"{project_name}/components/model_trainer.py",
    f"{project_name}/components/model_evaluation.py",
    f"{project_name}/pipeline/__init__.py",
    f"{project_name}/pipeline/data_pipeline.py",
    f"{project_name}/pipeline/model_pipeline.py",
    f"{project_name}/logging.py",
    f"{project_name}/exception.py",
    "config/config.yaml",
    "dvc.yaml",
    "params.yaml",
    "requirements.txt",
    "research/testing.py",
    "setup.py",
    "model/.gitkeep",
    "templates/index.html",
    "init_setup.sh",
]


for filepath in list_of_files:
    filepath=Path(filepath)
    filedir,filename=os.path.split(filepath)
    
    if filedir !="":
        os.makedirs(filedir,exist_ok=True)
        
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath)==0):
        with open(filepath,"w") as f:
            pass
    else:
        print(f"{filepath} already exists")