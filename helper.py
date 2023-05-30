import docker
client = docker.from_env()

#client.containers.run('nginx', name='webserver', ports={'80/tcp': 8080}, detach=True) #exposes the port 8080
#client.containers.list(all=True, filters={"name": 'webserver'})[0].start()

def port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def used_minecraft_ports():
    ports = []
    for i in range(25560, 25571):
        if port_in_use(i):
            ports.append(i)
    return ports

def create(user, container_name, port, path, version='latest', memory='1G'):
    environment = ["EULA=TRUE", "TYPE=PAPER", f"VERSION={version}", f"MEMORY={memory}"]
    client.containers.create('itzg/minecraft-server:latest', name=f'{user}.{container_name}', ports={'25565/tcp': port}, 
        environment=environment, volumes=[f'{path}/{container_name}:/data'])

def start(user, container_name):
    container = client.containers.get(f'{user}.{container_name}')
    container.start()

def stop(user, container_name):
    container = client.containers.get(f'{user}.{container_name}')
    container.stop()

def ps(user):
    running = {}
    all_containers = {}
    containers = client.containers.list(filters={'name': f'{user}:*'}, all=True)
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



        

#create('user', 'test', 25565, "/home/samuel/docker-monitor/containers/user", '1.18', '2G')