import os, docker, os.path

def up(folder):
    file_path=f"{folder}/docker-compose.yml"
    os.popen(f"docker-compose -f {file_path} up -d")

def down(folder):
    file_path=f"{folder}/docker-compose.yml"
    os.system(f"docker-compose -f {file_path} down")

def exec(container_name, command):
    os.system(f"docker-compose exec {container_name} {command}")

def list(path):
    containers = {}
    folders = os.popen(f"ls -d {path}/*/").read().split("\n")
    folders.remove("")
    for folder in folders:
        if os.path.isfile(f"{folder}/docker-compose.yml"):
            #Service
            name = os.popen(f"cat {folder}/docker-compose.yml | grep container_name | cut -d '\"' -f2").read()[:-1]
            port = os.popen(f"cat {folder}/docker-compose.yml | grep 25565 |cut -d':' -f1 | cut -d '\"' -f2").read()[:-1]
            #Environment
            version = os.popen(f"cat {folder}/docker-compose.yml | grep VERSION |cut -d ':' -f2").read()[:-1]
            if version == '':
                version = "latest"
            memory = os.popen(f"cat {folder}/docker-compose.yml | grep MEMORY |cut -d':' -f2").read()[:-1]
            if memory == '':
                memory = "1G(default)"
            image = os.popen(f"cat {folder}/docker-compose.yml | grep image |cut -d':' -f2").read()[:-1]
            if "minecraft" in image:
                containers[name] = {
                    "port": port,
                    "version": version,
                    "memory": memory,
                    "folder": folder,
                    "image": image
                }
    return containers

def ps(path): #path for the containers
    client = docker.from_env()
    containers = client.containers.list()
    status_dict = {}
    container_list = list(path)
    for container in containers:
        if container.name in str(container_list):
            print("check")
            container_id = container.short_id
            container_name = container.name
            port = container_list[container_name]['port']
            status_dict[container_id] = {
                "name": container_name,
                "status": container.status,
                "port": port
            }
    return status_dict

