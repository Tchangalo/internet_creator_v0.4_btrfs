#!/bin/bash

export ANSIBLE_HOST_KEY_CHECKING=False

node=$1
provider=$2
destroy=$3
router=$4
refresh=$5

C='\033[0;94m'
NC='\033[0m'

sleeping ()
{
	while sleep 5
	do
	    ansible -i ${HOME}/streams/ansible/inventories/inventory${provider}.yaml p$1r${router}v -m ping -u vyos | grep -q pong && break
	done
	echo -e "${C}Router ${router} is running${NC}"
}

#destroy and recreate vms
cd ${HOME}/streams/create-vms/create-vms-vyos/

#destroy
if [ $destroy == 1 ]
   then
       echo -e "${C}Destroying VM${NC}"
	   sudo qm stop ${node}0${provider}00${router}
	   sudo bash create-vm-vyos.sh -c destroy -n ${node} -p ${provider} -r ${router}
fi

#create
echo -e "${C}Creating VM${NC}"
sudo bash create-vm-vyos.sh -c create -n ${node} -p ${provider} -r ${router}

#start
echo -e "${C}Starting VM${NC}"
sudo qm start ${node}0${provider}00${router}

#ssh-keygen
echo -e "${C}ssh-keygen${NC}"
ssh-keygen -f "${HOME}/.ssh/known_hosts" -R "10.20.30.${provider}${router}"

#sleeping
echo -e "${C}Waiting for first boot${NC}"
sleeping $provider $router

#upgrade and reboot
if [ "${refresh}" == "1" ]
then
	cd ${HOME}/streams/ansible
	rm -rf vyos-files
	mkdir vyos-files
	cd vyos-files

	download_url=$(curl -s https://api.github.com/repos/vyos/vyos-nightly-build/releases/latest | jq -r ".assets[0].browser_download_url")

	echo -e "${C}Waiting for download of latest Vyos version into /home/user/streams/ansible/vyos-files to complete ...${NC}"
	if curl -LO "$download_url" 
	then
		echo -e "${C}Download completed successfully${NC}"
	else
		echo -e "${NC}Download failed. Exiting script${NC}"
		exit 1
	fi
fi

cd ${HOME}/streams/ansible
echo -e "${C}System upgrade and reboot${NC}"
ansible-playbook -i inventories/inventory${provider}.yaml vyos_upgrade_turbo.yml -e "vyos_version=$(ls -t ${HOME}/streams/ansible/vyos-files/ | head -n 1 | sed -e 's/^vyos-//' | sed -e 's/-amd.*$//')" -l "p${provider}r${router}v"

#sleeping
echo -e "${C}Waiting for second boot${NC}"
sleeping $provider $router

#configuring
echo -e "${C}Configuring network${NC}"
ansible-playbook -i inventories/inventory${provider}.yaml setup.yml "-l p${provider}r${router}v"

#delete cdrom
echo -e "${C}Deleting cdrom${NC}"
sudo qm set ${node}0${provider}00${router} --delete ide2

#reboot
echo -e "${C}Final reboot${NC}"
echo -e "${C}Shutting down VM${NC}"
sudo qm shutdown ${node}0${provider}00${router}
echo -e "${C}Final restart${NC}"
sudo qm start ${node}0${provider}00${router}

echo -e "${C}All done. Wait a minute until the router is running.${NC}"
