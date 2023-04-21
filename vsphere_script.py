# this script is used to make different operations to vms using the vsphere api

# this script works on python 3.9+
# packages needed to pip install
# pip install requests
# pip install urllib3
# pip install git+https://github.com/vmware/vsphere-automation-sdk-python.git

import requests
import urllib3
import sys
import time

from com.vmware.vcenter_client import VM

from com.vmware.cis_client import Session

from vmware.vapi.vsphere.client import create_vsphere_client
from vmware.vapi.lib.connect import get_requests_connector
from vmware.vapi.security.session import create_session_security_context
from vmware.vapi.security.user_password import \
    create_user_password_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
from com.vmware.vcenter_client import Datastore
from com.vmware.vcenter.vm.hardware_client import Cpu
from com.vmware.vcenter.vm.hardware_client import Memory
from com.vmware.vcenter.vm_client import Power
from com.vmware.vcenter.vm.guest_client import Identity
from com.vmware.vapi.std.errors_client import ServiceUnavailable


sourcevm = None
clonedvmname = None
datastorelocation = None
cpuamount = 4
memamount = 8
vsphere = 'vcsa'
operation = None
uname = ""
pword = ""


args = (sys.argv)
args.pop(0)

argslenght = len(args)
for index, arg in enumerate(args):
    arg = arg.lower()
    if arg == '-help' or arg == '-h':
        print(
            '-source or -s to set source of the cloning.\n'
            '-target or -t to set'
            ' the target of the operations.\n'
            '-datastore or -ds to set the location'
            ' for the clones-\n'
            '-cpu to set the amount of cores '
            'the fullclone and modify will use'
            ' (default: 4 cores)\n'
            '-memory or -mem to set the amount of memory in GB that fullclone'
            ' and modify will use (default: 8gb)\n'
            '-vsphere sets the server that will'
            ' be connected to (default: vcsa)\n'
            '-operation or -o is used to set the operation that will be'
            ' performed: \n'
            '    deplyofullvm or dfv will do a fullvmclone with'
            ' the set parameters,\n'
            '    instanclone or ic will do a instantclone\n'
            '    poweroff will'
            ' turn the target vms power off\n'
            '    power on will turn the target'
            ' vms power on\n'
            '    modify will set the target vms memory and cpu amount to the'
            ' given parameters\n'
            '    delete will delete target vm\n'
            'instantclone needs to have source, target and datastore'
            ' set to function\n'
            'deployfullvm needs to have source, target and datastore set'
            ' and optionally have cpu and memory set'
        )
    elif arg == '-source' or arg == '-s':
        if index < (argslenght - 1):
            next = args[index + 1]
            sourcevm = next
    elif arg == '-target' or arg == '-t':
        if index < (argslenght - 1):
            next = args[index + 1]
            clonedvmname = next
    elif arg == '-datastore' or arg == '-ds':
        if index < (argslenght - 1):
            next = args[index + 1]
            datastorelocation = next
    elif arg == '-cpu':
        if index < (argslenght - 1):
            next = args[index + 1]
            try:
                cpuamount = int(next)
            except ValueError:
                sys.exit('Cpu amount not a int')
    elif arg == '-mem' or arg == '-memory':
        if index < (argslenght - 1):
            next = args[index + 1]
            try:
                memamount = int(next)
            except ValueError:
                sys.exit('Memory amount not a int')
    elif arg == '-vsphere':
        if index < (argslenght - 1):
            next = args[index + 1]
            vsphere = next
    elif arg == '-operation' or arg == '-o':
        if index < (argslenght - 1):
            next = args[index + 1]
            operation = next


def get_jsonrpc_endpoint_url(host):
    # The URL for the stub requests are made against the /api HTTP endpoint
    # of the vCenter system.
    return "https://{}/api".format(host)


def connect(host, user, pwd, skip_verification=False,
            cert_path=None, suppress_warning=True):

    # Create an authenticated stub configuration
    # object that can be used to issue
    # requests against vCenter.
    # Returns a stub_config that stores the session
    # identifier that can be used
    # to issue authenticated requests against vCenter.

    host_url = get_jsonrpc_endpoint_url(host)

    session = requests.Session()
    if skip_verification:
        session = create_unverified_session(session, suppress_warning)
    elif cert_path:
        session.verify = cert_path
    connector = get_requests_connector(session=session, url=host_url)
    stub_config = StubConfigurationFactory.new_std_configuration(connector)

    return login(stub_config, user, pwd)


def login(stub_config, user, pwd):

    # Create an authenticated session with vCenter.
    # Returns a stub_config that stores the session identifier that can be used
    # to issue authenticated requests against vCenter.

    # Pass user credentials (user/password) in the security context to
    # authenticate.
    user_password_security_context = create_user_password_security_context(
        user, pwd)
    stub_config.connector.set_security_context(user_password_security_context)

    # Create the stub for the session service and login by creating a session.
    session_svc = Session(stub_config)
    session_id = session_svc.create()

    # Successful authentication.  Store the session identifier in the security
    # context of the stub and use that for all subsequent remote requests
    session_security_context = create_session_security_context(session_id)
    stub_config.connector.set_security_context(session_security_context)

    return stub_config


def logout(stub_config):
    # Delete session with vCenter.
    if stub_config:
        session_svc = Session(stub_config)
        session_svc.delete()


def create_unverified_session(session, suppress_warning=True):
    session.verify = False
    if suppress_warning:
        # Suppress unverified https request warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session


# function wants the name of the searched vm
def vmsearcher(target):
    vmfound = None
    vmslist = connection_list()
    for x in vmslist:
        vmlist = str(x)
        if target in vmlist:
            vmfoundname = vmlist
            # Data comes in the form below and is parsed to include only,
            # the name of the vm.
            # {vm : vmid, name : vmname, power_state : POWERED_ON,\
            #  cpu_count : 2, memory_size_mib : 8192}
            vmfoundname = vmfoundname.split(',')
            vmfoundname = vmfoundname[1].split(':')
            vmfoundname = vmfoundname[1].strip(' ')
            if target == vmfoundname:
                vmfound = vmlist
    # strip it into the needed vm id
    if vmfound is None:
        sys.exit('VM not found')
    vmfound = str(vmfound)
    # Data comes in the form below and is parsed to include only,
    # the id of the vm.
    # {vm : vmid, name : vmname, power_state : POWERED_ON,\
    #  cpu_count : 2, memory_size_mib : 8192}
    vmfound = vmfound.split(',')
    vmfound = vmfound[0].split(':')
    vmfound = vmfound[1].strip(' ')
    return vmfound


# Function needs the name of the datastore.
# Search for the datastore info of the wanted datastore,
# and get the correct datastore id.
def datastoresearch(datastoresname):
    datastorename = {datastoresname}
    datastores = Datastore(config=conf)
    datastorefilter = datastores.FilterSpec(names=datastorename)
    datastorelist = datastores.list(filter=datastorefilter)
    for x in datastorelist:
        datastore = str(x)
    try:
        datastore = datastore.split(',')
    except UnboundLocalError:
        sys.exit('Datastore not found')
    datastore = datastore[0].split(':')
    datastore = datastore[1].strip(' ')
    return datastore


# connect to the server without verification
conf = connect(vsphere, uname, pword, skip_verification=True)


def connection_list():
    session = requests.session()
    create_unverified_session(session, True)
    vsphere_client = create_vsphere_client(server=vsphere,
                                           username=uname,
                                           password=pword,
                                           session=session)
    vmslist = vsphere_client.vcenter.VM.list()
    return vmslist


if operation:
    session = requests.session()
    create_unverified_session(session, True)
    vsphere_client = create_vsphere_client(server=vsphere,
                                           username=uname,
                                           password=pword,
                                           session=session)
if datastorelocation:
    datastore = datastoresearch(datastorelocation)
if sourcevm:
    sourcevmfound = vmsearcher(sourcevm)


def poweroncheck():
    timeouttime = 0
    while True:
        try:
            iden = Identity(config=conf)
            getvm = iden.get(vm=targetvmfound)
            print('vm responded')
            break
        except ServiceUnavailable:
            time.sleep(5)
            timeouttime = timeouttime+5
        if timeouttime >= 120:
            sys.exit('poweron timed out')


if operation == 'instantclone' or operation == 'ic':
    print("instantcloning vm...")
    # specs for the insantclone process
    instantcloneplacementspec = VM.InstantClonePlacementSpec(
                                        datastore=datastore)
    instantclone = VM.InstantCloneSpec(source=sourcevmfound,
                                       name=clonedvmname,
                                       placement=instantcloneplacementspec)
    # instanclone the vm using the specs
    instantclonevm = VM(config=conf)
    instantclonevm.instant_clone(spec=instantclone)
    print('instantclone done')
if operation == 'deployfullvm' or operation == 'dfv':
    print('cloning vm...')
    # specs for the insantclone process
    cloneplacementspec = VM.ClonePlacementSpec(datastore=datastore)
    clone = VM.CloneSpec(source=sourcevmfound, name=clonedvmname,
                         placement=cloneplacementspec, power_on=False)
    # clone the vm using the specs
    clonevm = VM(config=conf)
    clonevm.clone(spec=clone)
    print("cloned with power off")
    targetvmfound = vmsearcher(clonedvmname)
    print("changing cpu and mem amount")
    update_spec_cpu = Cpu.UpdateSpec(cpuamount)
    vsphere_client.vcenter.vm.hardware.Cpu.update(targetvmfound,
                                                  update_spec_cpu)
    update_spec_mem = Memory.UpdateSpec(memamount * 1024)
    vsphere_client.vcenter.vm.hardware.Memory.update(targetvmfound,
                                                     update_spec_mem)
    print("powering back on")
    vsphere_client.vcenter.vm.Power.start(targetvmfound)
    power = vsphere_client.vcenter.vm.Power.get(targetvmfound)
    if power == Power.Info(state=Power.State.POWERED_ON):
        print("power is on")
        print("waiting for vm to respond")
        poweroncheck()
    print("cloning done")

if clonedvmname is not None:
    targetvmfound = vmsearcher(clonedvmname)

if operation == 'poweroff':
    print("target vm powering off")
    vsphere_client.vcenter.vm.Power.stop(targetvmfound)
    print('power turned off')

if operation == 'modify':
    power = vsphere_client.vcenter.vm.Power.get(targetvmfound)
    if power == Power.Info(state=Power.State.POWERED_ON):
        print("the target vms power is not off")
    else:
        print("modifying target vm cpu and memory specs")
        cpu_update_spec = Cpu.UpdateSpec(cpuamount)
        vsphere_client.vcenter.vm.hardware.Cpu.update(targetvmfound,
                                                      cpu_update_spec)
        mem_update_spec = Memory.UpdateSpec(memamount * 1024)
        vsphere_client.vcenter.vm.hardware.Memory.update(targetvmfound,
                                                         mem_update_spec)
        print("specs modified")

if operation == 'poweron':
    print("target vm powering on")
    vsphere_client.vcenter.vm.Power.start(targetvmfound)
    print('power turned on')
    print("waiting for vm to respond")
    power = vsphere_client.vcenter.vm.Power.get(targetvmfound)
    if power == Power.Info(state=Power.State.POWERED_ON):
        print("power is on")
        poweroncheck()

if operation == 'delete':
    power = vsphere_client.vcenter.vm.Power.get(targetvmfound)
    if power == Power.Info(state=Power.State.POWERED_ON):
        print("the target vms power is not off")
    else:
        print("deleting target vm")
        vsphere_client.vcenter.VM.delete(targetvmfound)
        print("deleted VM: "+targetvmfound)

if operation == 'freezecheck' or operation == 'fc':
    vmconfig = VM(config=conf)
    source_vm = vmconfig.get(vm=sourcevmfound)
    is_frozen = source_vm.instant_clone_frozen
    if is_frozen:
        print("The source VM: "+sourcevm+" is frozen")
    else:
        sys.exit(1)
