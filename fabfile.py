from fabric import Connection, task

def sudo_put(c, local, remote):
    c.put(local, remote="/tmp/tmp-fabric-file-transfer")
    c.run("sudo mv /tmp/tmp-fabric-file-transfer "+remote)
    c.run("sudo chown root:root "+remote)

@task
def configure(c, domains, deploy_key):
    install_dependencies(c)
    configure_nginx(c, domains)
    configure_certbot(c, domains)
    configure_online_town(c, deploy_key)
    configure_tmux(c)

@task
def install_dependencies(c):
    c.run("sudo apt update")
    c.run("sudo apt -y install make build-essential software-properties-common")
    c.run("sudo add-apt-repository universe")
    c.run("sudo add-apt-repository ppa:certbot/certbot")
    c.run("curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -")
    c.run("sudo apt update")
    c.run("sudo apt -y install nginx nodejs certbot python-certbot-nginx")

@task
def configure_nginx(c, domains):
    sudo_put(c, "sites-available/BLANK", remote="/etc/nginx/sites-available/BLANK")
    c.run("sudo ln -sf /etc/nginx/sites-available/BLANK /etc/nginx/sites-enabled/BLANK")
    c.run(f"sed -e 's/<domain>/{domains}/' < /etc/nginx/sites-available/BLANK > /tmp/tmp-sites-available-BLANK")
    c.run("sudo mv /tmp/tmp-sites-available-BLANK /etc/nginx/sites-available/BLANK")
    
@task
def configure_certbot(c, domains):
    domains_comma_separated=",".join(domains.split(" "))
    c.run("sudo certbot --agree-tos --email BLANK --nginx --reinstall --redirect --domains="+domains_comma_separated)
    c.run("sudo systemctl restart nginx")
    c.run("sudo mkdir -p /srv/BLANK/")
    c.run("sudo mkdir -p /srv/BLANK/cert/")
    reflect_certs(c)
   
@task
def configure_online_town(c, deploy_key):
    sudo_put(c, deploy_key, remote="/root/.ssh/id_rsa")
    sudo_put(c, "sshconfig", remote="/root/.ssh/config")
    c.run("sudo rm -rf /srv/BLANK/online-town")
    c.run("cd /srv/BLANK && sudo git clone git@github.com:BLANK/online-town.git")
    c.run("cd /srv/BLANK/online-town && sudo npm install --unsafe-perm=true")
   
@task
def configure_tmux(c):
    c.run("sudo tmux has-session -t online-town || sudo tmux new -d -s online-town")
    c.run("sudo test $(sudo tmux list-panes -t online-town | wc -l) -eq 2 || sudo tmux split-window -h -t online-town.0")

@task
def restart_online_town(c):
    c.run("sudo tmux send -t online-town.0 C-c")
    c.run("sudo tmux send -t online-town.1 C-c")
    c.run("sudo tmux send -t online-town.0 cd SPACE /srv/BLANK/online-town ENTER")
    c.run("sudo tmux send -t online-town.1 cd SPACE /srv/BLANK/online-town ENTER")
    c.run("sudo tmux send -t online-town.0 PROD=true SPACE PORT=4000 SPACE npm SPACE run SPACE start-http-keepalive ENTER")
    c.run("sudo tmux send -t online-town.1 PROD=true SPACE node SPACE src/video-server.js ENTER")

@task
def restart_game_server(c):
    c.run("sudo tmux send -t online-town.0 C-c")
    c.run("sudo tmux send -t online-town.1 C-c")
    c.run("sudo tmux send -t online-town.0 cd SPACE /srv/BLANK/online-town ENTER")
    c.run("sudo tmux send -t online-town.0 PORT=true SPACE npm SPACE run SPACE start-game-keepalive ENTER")

@task
def update_client(c):
    c.run("cd /srv/BLANK/online-town/ && sudo git pull")
    c.run("cd /srv/BLANK/online-town/ && sudo npm install --unsafe-perm=true")
    c.run("cd /srv/BLANK/online-town/ && PROD=true sudo npm run build-prod")

@task 
def update_online_town(c):
    update_client(c)
    restart_online_town(c)

@task
def update_game_server(c):
    update_client(c)
    restart_game_server(c)

@task
def switch_to_develop(c):
    c.run("cd /srv/BLANK/online-town/ && git checkout develop")

@task
def switch_to_master(c):
    c.run("cd /srv/BLANK/online-town/ && git checkout master")

@task
def switch_to(c, branch):
    c.run("cd /srv/BLANK/online-town/ && sudo git checkout "+branch)

@task
def reflect_certs(c):
    c.run("sudo bash -c 'ln -sf /etc/letsencrypt/live/*/* /srv/BLANK/cert/'")
