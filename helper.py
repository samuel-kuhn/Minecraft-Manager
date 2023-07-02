import docker, shutil
client = docker.from_env()

#client.containers.list(all=True, filters={"name": 'webserver'})[0].start()

def port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def create(user, container_name, port, path, mode, version='latest', memory='1G', Type='PAPER', motd = 'a simple minecraft server'):
    environment = ["EULA=TRUE", f"TYPE={Type}", f"VERSION={version}", f"MEMORY={memory}", f"MOTD={motd}", f"MODE={mode}"] #, "FORGEVERSION=40.1.0", "MODE=creative"
    try:
        client.containers.create('itzg/minecraft-server:latest', name=f'{user}.{container_name}', ports={'25565/tcp': port}, 
            environment=environment, volumes=[f'{path}:/data'])
    except Exception:
        return "error"

def update_port(user, container_name, port):
    container = client.containers.get(f'{user}.{container_name}')
    environment = container.attrs['Config']['Env']
    path = container.attrs['HostConfig']['Binds'][0].split(':')[0]
    mode = environment[5].split('=')[1]
    version = environment[2].split('=')[1]
    memory = environment[3].split('=')[1]
    Type = environment[1].split('=')[1]
    motd = environment[4].split('=')[1]
    container.remove()
    create(user, container_name, port, path, mode, version, memory, Type, motd)

def start(user, container_name):
    container = client.containers.get(f'{user}.{container_name}')
    container.start()

def stop(user, container_name):
    container = client.containers.get(f'{user}.{container_name}')
    container.stop()

def reset(user, path, container_name):
    stop(user, container_name)
    try:
        shutil.rmtree(f"{path}/{container_name}/world")
        shutil.rmtree(f"{path}/{container_name}/world_nether")
        shutil.rmtree(f"{path}/{container_name}/world_the_end")
    except Exception:
        pass

def remove(user, path, container_name):
    stop(user, container_name)
    container = client.containers.get(f'{user}.{container_name}')
    container.remove()
    try:
        shutil.rmtree(f"{path}/{container_name}")
    except Exception:
        pass

def exec(user, container_name, command):
    container = client.containers.get(f'{user}.{container_name}')
    container.exec_run("mc-send-to-console " + command)

def ps(user):
    running = {}
    all_containers = {}
    containers = client.containers.list(filters={'name': f'{user}.'}, all=True)
    for container in containers:
        container_name = container.name.replace(f'{user}.', '')
        public_port = container.attrs['HostConfig']['PortBindings']['25565/tcp'][0]['HostPort']
        status = container.status
        environment_list = container.attrs['Config']['Env']
        environment = dict(item.split('=', 1) for item in environment_list)
        memory = "1G (default)"
        if 'MEMORY' in environment:
            memory = environment['MEMORY']
        if status == 'running':
            running[container.short_id] = {
                "name": container_name,
                "port": public_port
            }
        all_containers[container_name] = {
            "port": public_port,
            "status": status,
            "version": environment['VERSION'],
            "memory": memory
        }
    return [running, all_containers]

#create('clytox', 'creative', 25565, "/home/clytox", '1.18.2', '6G')
#create("clytox", "creative", 25567, "/home/clytox", "creative", "1.18.2", "6G", "FORGE", "40.1.0", "creative server") create a forge server


