#SELinux
We will create a daemon service that run the script python for a simple http server
You can use the script `simpleserver.py` and `simpleserver.service` or create your own script.

First, move your script `simpleserver.py` to the directory `/usr/local/bin` and the service `simpleservre.service` to `etc/systemd/system`
Make sure your script is executable
```
cp /usr/local/bin/simpleserver.py /usr/local/bin/simpleserver
chmod a+x /usr/local/bin/simpleserver.py
```


Restore the default SELinux context for the files 
```
sudo restorecon -Fv /usr/local/bin/simpleserver /etc/systemd/system/simpleserver.service
```

Setting up your SELinux module
```
mkdir ~/module
cd ~/module
sepolgen --init /usr/local/bin/simpleserver
```
You should see your files .te .fc .if here 
```
# ls
simpleserver.fc  simpleserver.if  simpleserver.pp  simpleserver_selinux.spec  simpleserver.sh  simpleserver.te  tmp
```
Modify your `simpleserver.te` or use my version
```
policy_module(simpleserver, 1.0.0)

require {
type init_t;
type bin_t;
type node_t;
type svn_port_t;
type httpd_sys_content_t;
}
########################################
#
# Declarations
#

type simpleserver_t;
type simpleserver_exec_t;
#permissive simpleserver_t;
init_daemon_domain(simpleserver_t,simpleserver_exec_t);


########################################
#
# simpleserver local policy
#

#files_read_etc_files(simpleserver_t);
auth_read_shadow(simpleserver_t);
fs_associate(simpleserver_t);
allow simpleserver_t self:fifo_file rw_fifo_file_perms;
allow simpleserver_t bin_t:file { execute execute_no_trans map };

allow simpleserver_t self:unix_stream_socket create_stream_socket_perms;
allow simpleserver_t self:tcp_socket { accept bind create getattr listen read setopt shutdown write };
allow simpleserver_t node_t:tcp_socket node_bind;
allow simpleserver_t svn_port_t:tcp_socket name_bind;

#allow simpleserver_t httpd_sys_content_t:dir read;
allow simpleserver_t httpd_sys_content_t:file {getattr open read write};

allow init_t simpleserver_exec_t:file { execute execute_no_trans getattr open read };
```

Whenever you change your module policies via file `.te` you should repeat from this step
Compile your module and implement it to the kernel
```
make -f /usr/share/selinux/devel/Makefile simpleserver.pp
sudo semodule -i simpleserver.pp
sudo restorecon -Fv /usr/local/bin/simpleserver /etc/systemd/system/simpleserver.service
```

Run you daemon service
```
sudo systemctl daemon-reload
sudo systemctl start simpleserver
```

#Test your server

Create test file at `/var/www/html/test/` 
```
mkdir /var/www/html/test
mkdir /var/www/html/test/tata
mkdir /var/www/html/test/toto
sudo touch /var/www/html/test/tata/titi
sudo touch /var/www/html/test/toto/foo
sudo echo "Tata Titi" > /var/www/html/test/tata/titi
sudo echo "Toto" > /var/www/html/test/toto/foo
sudo touch /etc/ssl/test
```
This should work
```
#curl localhost:3690/var/www/html/test/tata/titi
Tata Titi
#curl -d "Some POST data" localhost:3690/var/www/html/test/tata/titi
#curl localhost:3690/var/www/html/test/tata/titi
Some POST data
#curl localhost:3690/var/www/html/test/toto/foo
Toto
```
And this should not work
```
curl -d "Some POST data" localhost:3690/etc/ssl/test
curl localhost:3690/etc/ssl/test
curl localhost:3690/etc/shadow
```

#Debug 

Install `setroubleshoot` to help you understand more about SELinux errors
Deactivate `dontaudit` to get the log for error
```
sudo dnf install -y setroubleshoot-server
sudo semodule -DB
```
You then can see the errors at `/var/log/audit/audit.log`
```
sudo tail -fn 10 /var/log/audit/audit.log
sudo journalctl -e _TRANSPORT=audit
```
You can also use with `audit2allow` to generate policies needed for your `.te` file
```
sudo cat /var/log/audit/audit.log | audit2allow
```
