# File: backend/app.py (Flask Backend)
from flask import Flask, jsonify, request
import libvirt
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Connect to the hypervisor
def get_conn():
    return libvirt.open("qemu+tcp://192.168.64.2/system")

# List all VMs
@app.route('/vms', methods=['GET'])
def list_vms():
    conn = get_conn()
    domains = conn.listAllDomains()
    vms = [{
        'name': d.name(),
        'id': d.ID(),
        'isActive': d.isActive()
    } for d in domains]
    conn.close()
    return jsonify(vms)

# Start a VM
@app.route('/vms/<name>/start', methods=['POST'])
def start_vm(name):
    conn = get_conn()
    domain = conn.lookupByName(name)
    domain.create()
    conn.close()
    return jsonify({'status': 'started'})

# Stop a VM
@app.route('/vms/<name>/stop', methods=['POST'])
def stop_vm(name):
    conn = get_conn()
    domain = conn.lookupByName(name)
    domain.shutdown()
    conn.close()
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
