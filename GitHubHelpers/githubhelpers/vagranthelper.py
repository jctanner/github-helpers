#/usr/bin/env python

import os
import shlex
import tempfile
from processhelper import run_command

# http://ttboj.wordpress.com/2013/12/09/vagrant-on-fedora-with-libvirt/

# https://fedoraproject.org/wiki/Getting_started_with_virtualization?rd=Virtualization_Quick_Start#Installing_the_virtualization_packages

# yum install @virtualization
# yum isntall libvirt-devel libxslt-devel libxml2-devel
# reboot
# yum localinstall vagrant*.rpm
# vagrant plugin install vagrant-mutate
# vagrant plugin install vagrant-libvirt
# vagrant box add centos-6 https://download.gluster.org/pub/gluster/purpleidea/vagrant/centos-6.box --provider=libvirt
# export VAGRANT_DEFAULT_PROVIDER=libvirt
# vagrant init test
# vagrant up

"""
VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "centos-6"
  config.vm.synced_folder ".", "/vagrant", :disabled => true
  libvirt.storage_pool_name = "default" #FIXME
end
"""

"""
[root@corsair test1]# vagrant ssh-config
Host default
  HostName 192.168.121.131
  User vagrant
  Port 22
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /root/.vagrant.d/insecure_private_key
  IdentitiesOnly yes
  LogLevel FATAL
"""

BASEFILE='''VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "%s"
  config.vm.synced_folder ".", "/vagrant", :disabled => true
  libvirt.storage_pool_name = "default" #FIXME
end
'''

class VagrantHelper(object):
    def __init__(self):
        self.provider = None
        self.tmpdir = "/tmp/"
        self.workdir = None

        self.workdir = tempfile.mkdtemp(prefix=self.tmpdir)

    def createvagrantfile(self, config_opts=[]):
        header = 'VAGRANTFILE_API_VERSION = "2"'
        config_start = "Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|"
        config_opts = config_opts
        footer = "end"

        this_file = os.path.join(self.workdir, "Vagrantfile") 
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

        f = open(this_file, "wb")
        f.write(header + "\n")
        f.write(config_start + "\n")
        for opt in config_opts:
            f.write("\t" + opt + "\n")
        f.write(footer + "\n")

    def start(self):
        cmd = "vagrant up"
        rc, so, se = run_command(cmd, cwd=self.workdir)
        print rc,so,se
        self.get_ssh_config()

    def get_ssh_config(self):        
        cmd = "vagrant ssh-config"
        rc, so, se = run_command(cmd, cwd=self.workdir)
        print rc,so,se
        self.ssh_config = so

        ssh_dict = {}
        lines = so.split('\n')
        for line in lines:
            if line != '':
                try:
                    w = shlex.split(line, 1)
                    k = w[0].strip().lower()
                    v = w[1].strip()
                    ssh_dict[k] = v
                except:
                    #import epdb; epdb.st()
                    pass

        self.ssh_dict = ssh_dict
        #print ssh_dict

    def destroy(self):
        cmd = "vagrant destroy"
        rc, so, se = run_command(cmd, cwd=self.workdir)
        print rc,so,se
    
    def do(self, cmd, args):
        """ run an arbitrary vagrant command """
        pass

def main():
    this_opts = [ 'config.vm.box = "centos-6"',
                  'config.vm.synced_folder ".", "/vagrant", :disabled => true',
                  'config.vm.provider :libvirt do |libvirt|',
                  '\tlibvirt.storage_pool_name = "2TB"' ]
    x = VagrantHelper()
    #x.workdir = "/tmp/testbox"
    x.createvagrantfile(config_opts=this_opts)
    x.start()
    #x.get_ssh_config()
    print x.workdir
    print x.ssh_dict
    x.destroy()

if __name__ == "__main__":
    main() 
