All the material was given to me by my professor Timothée RAVIER at INSA Centre Val de Loire


The process was done in a virtual environment and I would reccomend doing the same (i use fedora virtual machine to test SELinux functions)
Except the SELinux part that should only exist on Fedora/CentOS, you can do other parts in any Linux machine (replace `dnf update` and `dnf install` with your own version of Linux, i.e : `apt-get install` on Ubuntu/Debian,...)


# Getting started
Prepare the dependencies needed 
```
sudo dnf update -y
sudo dnf install -y tree bash-completion docker podman selinux-policy-devel setools-console
sudo systemctl enable --now docker
sudo reboot 
```

Create your own http service
Create your own Python script for the server or copy from my `httpserver.py`
```
mkdir /srv/httpserver
sudo nano /srv/httpserver/httpserver.py
```

Create a user httpuser without privilege for our service to run the program
```
useradd --home-dir / --no-create-home --system --shell /sbin/nologin --user-group httpuser
```

Go to /etc/systemd/system and create your own service or copy from my `myserver.service`
```
cd /etc/systemd/system
sudo nano myserver.service
```
Launch your service
```
systemctl daemon-reload
systemctl start myserver.service
```
Check your server on port 7272
```
curl localhost:7272
```
You should see this
```
<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Directory listing for /</title>
</head>
<body>
<h1>Directory listing for /</h1>
<hr>
<ul>
<li><a href="httpserver.py">httpserver.py</a></li>
</ul>
<hr>
</body>
</html>
```
If you see this assertion raised
```
Assertion failed on job for myserver.service.
```
It means that the system could not find the directory `/srv/httpserver`
Create the directory by using the command above
If you see this status
```
(code=exited, status=217/USER)
```
It means that the user with whom the service should be started could not be found.
Check if the user/group exists and if the user/group in your file is spelled correct
```
cat /etc/passwd | grep httpuser
cat /etc/group | grep httpuser
```
It should show something like
```
httpuser:x:992:991::/:/sbin/nologin
```
and 
```
httpuser:x:991:
```
If it does not exist, create the user and the usergroup


# Host your server on a Docker container
If you are not logged in as `root` user , you need to grant access to your user or log in as root
```
sudo su -
```
Create a directory for your Dockerfile and move to it
```
mkdir docker
cd docker
sudo cp /srv/httpserver/httpserver.py .
touch Dockerfile
```
Build a Dockerfile for you container
This container use the latest Fedora image
```
FROM registry.fedoraproject.org/fedora:latest
```
Set PORT on which the container listens for connection (default 8080). This value can be changed via `docker run --env` 
```
ENV PORT=8080
EXPOSE $PORT
```
Install python
```
RUN dnf -y update && dnf -y install python3 && dnf clean all
```
Create `/srv/httpserver` directory
```
RUN mkdir /srv/httpserver
```
Copy Python script into your container (remember to add the script into your host directory)
```
COPY httpserver.py /srv/httpserver/httpserver.py
```
Finally, run your python script
```
CMD ["python","/srv/httpserver/httpserver.py"]
```
You may forget to copy your python script `httpserver.py` to the directory 
if you see `"httpserver.py": not found` 
Check your build directory
```
#ls
Dockerfile httpserver.py
```
To build your container run
```
sudo docker build -t httpserver:latest .
```

Check your image
```
# docker images
REPOSITORY   TAG       IMAGE ID      CREATED         SIZE
httpserver   latest    57ed00a10357  5 minutes ago   218MB
```
Run your container 
```
sudo docker run --publish 7272:7272 -it httpserver:latest
```
If you get this message
```
failed to bind host port for 0.0.0.0:7272:172.17.0.2:7272/tcp: address already in use
```
It means that the port has been used, you can either use another port or make room for it
Example of listening on port 8080
```
sudo docker run --publish 8080:7272 -it httpserver:latest
```

You can see you container running here (mine 24f9cdbaf61c)
```
sudo docker ps
CONTAINER ID   IMAGE               COMMAND                  CREATED         STATUS         PORTS                                                   NAMES
24f9cdbaf61c   httpserver:latest   "python /srv/httpser…"   3 seconds ago   Up 2 seconds   7272/tcp, 0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp   stupefied_curie
```
To get the IP address of your container (usually 172.17.0.2)
```
sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 24f9cdbaf61c
172.17.0.2
```
You can see your server on `localhost:8080` or `172.17.0.2:7272`
```
curl localhost:8080
curl 172.17.0.2:7272
```

# Option for your server
## Non-privileged user
It is a good pratice to run your container with a non-root user whenever possible
Start by creating a non-root user and a group by adding this to your Dockerfile
```
RUN groupadd -r httpuser && useradd --no-log-init -r -g httpuser httpuser
```
Change ownership before you lose root privilege
```
RUN chown -R httpuser:httpuser /srv/httpserver
```
Then you can specify using this user in your container
```
USER httpuser:httpuser
```
Your Dockerfile should look something like this
```
FROM registry.fedoraproject.org/fedora:latest

#Create your environment variable PORT 
ENV PORT=7272

EXPOSE $PORT

#Install Python
RUN dnf -y update && dnf -y install python3 && dnf clean all
#Create /srv/httpserver
RUN mkdir /srv/httpserver

#Create non-root user
RUN groupadd -r httpuser && useradd --no-log-init -r -g httpuser httpuser
#Changing ownership before move to non-root user
RUN chown -R httpuser:httpuser /srv/httpserver
USER httpuser:httpuser

COPY httpserver.py /srv/httpserver/


CMD ["python","/srv/httpserver/httpserver.py"]
```
##Shared volume
Create a "web" page
```
mkdir www
echo "Hello World" > www/test.html
sudo chmod -R a+rw www
```
Run your container, now with option `-v`

```
docker run --env PORT=7272 --publish 8080:7272 -v "$(pwd)"/www/:/srv/httpserver/www/:Z -it httpserver:latest
```
Check your web page
```
[vagrant@fedora ~]$ curl 172.17.0.2:7272/srv/httpserver/www/test.html
Hello World
```

# SELinux (bonus)
SELinux (Securtity Enhanced Linux) is a Linux Security Module that support access control security policies, including MAC (Mandatory Access Control)
In this session i am going to create a module for a daemon service that control its access to filesystemt and tcpsocket.
Read more in SELinux/README.md
