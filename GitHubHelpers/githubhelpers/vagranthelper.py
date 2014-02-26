#/usr/bin/env python

# https://fedoraproject.org/wiki/Getting_started_with_virtualization?rd=Virtualization_Quick_Start#Installing_the_virtualization_packages

# yum install @virtualization
# reboot
# yum localinstall vagrant*.rpm
# vagrant plugin install vagrant-mutate
# vagrant plugin install vagrant-libvirt
# vagrant box add centos-6 https://download.gluster.org/pub/gluster/purpleidea/vagrant/centos-6.box --provider=libvirt
# export VAGRANT_DEFAULT_PROVIDER=libvirt
# vagrant init test
# vagrant up
