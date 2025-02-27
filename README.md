# Vsphere-operations-script

``python scipt that uses the vcsa/nas api to make different changes and checks to vms``

#### this script works on python 3.9+
### pip packages needed
``$ pip install requests``<br />
``$ pip install urllib3``<br />
``$ pip install git+https://github.com/vmware/vsphere-automation-sdk-python.git``

## Usage
Run the scipt with flags to perform various actions
### Command-line Arguments
- ``-source`` or ``-s``<br />
  <b>Description:</b> Sets the source VM for cloning.<br />
  <b>Example:</b> ``-s SourceVM``
  
- ``-target`` or ``-t``<br />
  <b>Description:</b> Sets the target VM where operations will be performed..<br />
  <b>Example:</b> ``-t TargetVM``

- ``-datastore`` or ``-ds``<br />
  <b>Description:</b> Specifies the datastore location for cloned VMs.<br />
  <b>Example:</b> ``-ds Datastore1``
  
- ``-cpu``<br />
  <b>Description:</b> Sets the number of CPU cores used for full clones and modifications. (Default: 4 cores)<br />
  <b>Example:</b> ``-cpu 6``
  
- ``-memory`` or ``-mem``<br />
  <b>Description:</b> Sets the amount of memory (in GB) for full clones and modifications. (Default: 8GB)<br />
  <b>Example:</b> ``-mem 16``
  
- ``-vsphere``<br />
  <b>Description:</b> Specifies the vSphere server to connect to. (Default: vcsa)<br />
  <b>Example:</b> ``-vsphere my-vsphere-server``
  
- ``-operation`` or ``-o``<br />
  <b>Description:</b> Defines the operation to be performed on the VM.<br />
  <b>Available Options:</b>
   - ``deployfullvm`` or ``dfv``: Performs a full VM clone with the specified parameters.
   - ``instantclone`` or ``ic``: Performs an instant clone.
   - ``poweroff``: Powers off the target VM.
   - ``poweron``: Powers on the target VM.
   - ``modify``: Modifies the target VM's memory and CPU according to given parameters.
   - ``delete``: Deletes the target VM.

## Requirements for Operations
- Instant Clone (``instantclone`` or ``ic``) requires ``-source``, ``-target``, and ``-datastore`` to be set.
- Full VM Clone (``deployfullvm`` or ``dfv``) requires ``-source``, ``-target``, and ``-datastore`` to be set. It can optionally include ``-cpu`` and ``-memory`` settings.

## Example Usage
Deploy a full VM clone:
```console
python script.py -s SourceVM -t TargetVM -ds Datastore1 -cpu 6 -mem 16 -o dfv
```
Perform an instant clone:
```console
python script.py -s SourceVM -t TargetVM -ds Datastore1 -o ic
```
Modify an existing VM:
```console
python script.py -t TargetVM -cpu 8 -mem 32 -o modify
```
Power off a VM:
```console
python script.py -t TargetVM -o poweroff
```
Delete a VM:
```console
python script.py -t TargetVM -o delete
```
