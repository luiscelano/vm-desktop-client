#!/usr/bin/env python3
"""
Cliente de Virtualización - Proyecto Final SO2
Universidad Mariano Gálvez de Guatemala

Gestor de Máquinas Virtuales usando libvirt y tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import libvirt
import xml.etree.ElementTree as ET
import os
import threading
import time
from datetime import datetime
import subprocess

class VirtualizationClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente de Virtualización - SO2 UMG")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')

        # Conexión a libvirt
        self.conn = None
        self.connect_to_libvirt()

        # Variables
        self.vms = {}
        self.selected_vm = None

        # Configurar interfaz
        self.setup_ui()
        self.refresh_vm_list()

        # Auto-refresh cada 5 segundos
        self.auto_refresh()

    def connect_to_libvirt(self):
        """Conectar a libvirt"""
        try:
            self.conn = libvirt.open("qemu+tcp://192.168.64.2/system")
            if self.conn is None:
                messagebox.showerror("Error", "No se pudo conectar a libvirt")
        except libvirt.libvirtError as e:
            messagebox.showerror("Error de conexión", f"Error al conectar con libvirt: {str(e)}")

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Título principal
        title_frame = tk.Frame(self.root, bg='#34495e', height=80)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="Cliente de Virtualización",
                               font=('Arial', 24, 'bold'), fg='white', bg='#34495e')
        title_label.pack(expand=True)

        subtitle_label = tk.Label(title_frame, text="Sistemas Operativos 2 - UMG",
                                   font=('Arial', 12), fg='#bdc3c7', bg='#34495e')
        subtitle_label.pack()

        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Panel izquierdo - Lista de VMs
        left_frame = tk.Frame(main_frame, bg='#34495e', width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)

        # Título de la lista
        list_title = tk.Label(left_frame, text="Máquinas Virtuales",
                              font=('Arial', 16, 'bold'), fg='white', bg='#34495e')
        list_title.pack(pady=10)

        # Treeview para mostrar VMs
        tree_frame = tk.Frame(left_frame, bg='#34495e')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.vm_tree = ttk.Treeview(tree_frame, columns=('Estado', 'CPU', 'RAM'), show='tree headings')
        self.vm_tree.heading('#0', text='Nombre')
        self.vm_tree.heading('Estado', text='Estado')
        self.vm_tree.heading('CPU', text='CPU')
        self.vm_tree.heading('RAM', text='RAM (MB)')

        self.vm_tree.column('#0', width=120)
        self.vm_tree.column('Estado', width=80)
        self.vm_tree.column('CPU', width=50)
        self.vm_tree.column('RAM', width=80)

        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.vm_tree.yview)
        self.vm_tree.configure(yscrollcommand=scrollbar.set)

        self.vm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind para selección
        self.vm_tree.bind('<<TreeviewSelect>>', self.on_vm_select)

        # Botones de control
        buttons_frame = tk.Frame(left_frame, bg='#34495e')
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        btn_style = {'font': ('Arial', 10, 'bold'), 'width': 15, 'height': 2}

        self.btn_refresh = tk.Button(buttons_frame, text="Actualizar", bg='#3498db', fg='white',
                                     command=self.refresh_vm_list, **btn_style)
        self.btn_refresh.pack(pady=2, fill=tk.X)

        self.btn_create = tk.Button(buttons_frame, text="Crear VM", bg='#27ae60', fg='white',
                                    command=self.create_vm_dialog, **btn_style)
        self.btn_create.pack(pady=2, fill=tk.X)

        self.btn_start = tk.Button(buttons_frame, text="Iniciar", bg='#e67e22', fg='white',
                                   command=self.start_vm, **btn_style)
        self.btn_start.pack(pady=2, fill=tk.X)

        self.btn_stop = tk.Button(buttons_frame, text="Detener", bg='#e74c3c', fg='white',
                                  command=self.stop_vm, **btn_style)
        self.btn_stop.pack(pady=2, fill=tk.X)

        self.btn_connect_vnc = tk.Button(buttons_frame, text="Entrar a VM", bg='#6c5ce7', fg='white',
                                         command=self.connect_to_vm_display, **btn_style)
        self.btn_connect_vnc.pack(pady=2, fill=tk.X)

        self.btn_delete = tk.Button(buttons_frame, text="Eliminar", bg='#8e44ad', fg='white',
                                     command=self.delete_vm, **btn_style)
        self.btn_delete.pack(pady=2, fill=tk.X)

        # Panel derecho - Detalles
        right_frame = tk.Frame(main_frame, bg='#34495e')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Título de detalles
        details_title = tk.Label(right_frame, text="Detalles de la Máquina Virtual",
                                 font=('Arial', 16, 'bold'), fg='white', bg='#34495e')
        details_title.pack(pady=10)

        # Frame para información
        self.info_frame = tk.Frame(right_frame, bg='#2c3e50', relief=tk.RAISED, bd=2)
        self.info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Área de texto para mostrar información
        self.info_text = tk.Text(self.info_frame, bg='#34495e', fg='white',
                                 font=('Consolas', 11), wrap=tk.WORD, padx=15, pady=15)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Estado de conexión
        status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="Conectado a libvirt",
                                     fg='#27ae60', bg='#34495e', font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.time_label = tk.Label(status_frame, text="",
                                   fg='#bdc3c7', bg='#34495e', font=('Arial', 10))
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def connect_to_libvirt(self):
        """Conectar a libvirt"""
        try:
            self.conn = libvirt.open("qemu:///system")
            if self.conn is None:
                messagebox.showerror("Error", "No se pudo conectar a libvirt")
        except libvirt.libvirtError as e:
            messagebox.showerror("Error de conexión", f"Error al conectar con libvirt: {str(e)}")

    def refresh_vm_list(self):
        """Actualizar la lista de máquinas virtuales"""
        if not self.conn:
            return

        try:
            # Limpiar el tree
            for item in self.vm_tree.get_children():
                self.vm_tree.delete(item)

            # Obtener todas las VMs (activas e inactivas)
            active_vms = self.conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
            inactive_vms = self.conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_INACTIVE)

            all_vms = active_vms + inactive_vms

            for vm in all_vms:
                name = vm.name()

                # Obtener estado
                state, reason = vm.state()
                state_text = self.get_state_text(state)

                # Obtener información de la VM
                info = vm.info()
                max_mem = info[1] // 1024  # Convertir a MB
                vcpus = info[3]

                # Insertar en el tree
                item_id = self.vm_tree.insert('', 'end', text=name,
                                                values=(state_text, vcpus, max_mem))

                # Cambiar color según el estado
                if state == libvirt.VIR_DOMAIN_RUNNING:
                    self.vm_tree.set(item_id, 'Estado', '🟢 Ejecutando')
                elif state == libvirt.VIR_DOMAIN_SHUTOFF:
                    self.vm_tree.set(item_id, 'Estado', '🔴 Apagada')
                elif state == libvirt.VIR_DOMAIN_PAUSED:
                    self.vm_tree.set(item_id, 'Estado', '🟡 Pausada')
                else:
                    self.vm_tree.set(item_id, 'Estado', f'⚪ {state_text}')

            self.status_label.config(text=f"Conectado - {len(all_vms)} VMs encontradas", fg='#27ae60')

        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"Error al listar VMs: {str(e)}")
            self.status_label.config(text="Error de conexión", fg='#e74c3c')

    def get_state_text(self, state):
        """Convertir estado numérico a texto"""
        states = {
            libvirt.VIR_DOMAIN_NOSTATE: 'Sin estado',
            libvirt.VIR_DOMAIN_RUNNING: 'Ejecutando',
            libvirt.VIR_DOMAIN_BLOCKED: 'Bloqueada',
            libvirt.VIR_DOMAIN_PAUSED: 'Pausada',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'Apagándose',
            libvirt.VIR_DOMAIN_SHUTOFF: 'Apagada',
            libvirt.VIR_DOMAIN_CRASHED: 'Crasheada',
            libvirt.VIR_DOMAIN_PMSUSPENDED: 'Suspendida'
        }
        return states.get(state, 'Desconocido')

    def on_vm_select(self, event):
        """Manejar selección de VM"""
        selection = self.vm_tree.selection()
        if not selection:
            return

        item = selection[0]
        vm_name = self.vm_tree.item(item, 'text')
        self.selected_vm = vm_name
        self.show_vm_details(vm_name)

    def show_vm_details(self, vm_name):
        """Mostrar detalles de la VM seleccionada"""
        if not self.conn:
            return

        try:
            vm = self.conn.lookupByName(vm_name)

            # Información básica
            info = vm.info()
            state_text = self.get_state_text(info[0])

            # XML de configuración
            xml_desc = vm.XMLDesc(0)
            root = ET.fromstring(xml_desc)

            # Extraer información del XML
            os_type_elem = root.find('.//os/type')
            os_type = os_type_elem.text if os_type_elem is not None else 'Desconocido'
            machine_type = os_type_elem.get('machine') if os_type_elem is not None else 'Desconocido'


            memory_elem = root.find('memory')
            memory = int(memory_elem.text) // 1024 if memory_elem is not None else 0

            vcpu_elem = root.find('vcpu')
            vcpus = vcpu_elem.text if vcpu_elem is not None else '0'

            # Información de red
            interfaces = root.findall('.//interface')
            network_info = []
            for iface in interfaces:
                iface_type = iface.get('type', 'Desconocido')
                source = iface.find('source')
                if source is not None:
                    network = source.get('network', source.get('bridge', 'Desconocido'))
                    network_info.append(f"  - Tipo: {iface_type}, Red: {network}")

            # Información de discos
            disks = root.findall('.//disk[@device="disk"]')
            disk_info = []
            for disk in disks:
                disk_type = disk.get('type', 'Desconocido')
                source = disk.find('source')
                if source is not None:
                    file_path = source.get('file', source.get('dev', 'Desconocido'))
                    disk_info.append(f"  - Tipo: {disk_type}, Archivo: {os.path.basename(file_path)}")
            
            # Información de CDROM
            cdroms = root.findall('.//disk[@device="cdrom"]')
            cdrom_info = []
            for cdrom in cdroms:
                source = cdrom.find('source')
                if source is not None:
                    file_path = source.get('file', 'No ISO')
                    cdrom_info.append(f"  - Archivo ISO: {os.path.basename(file_path) if file_path != 'No ISO' else file_path}")


            # Construir texto de información
            details = f"""INFORMACIÓN DE LA MÁQUINA VIRTUAL
═══════════════════════════════════════════════

Nombre: {vm_name}
Estado: {state_text}
ID: {vm.ID() if info[0] == libvirt.VIR_DOMAIN_RUNNING else 'N/A'}
UUID: {vm.UUIDString()}

RECURSOS:
─────────────────────────────────────────────────
CPU Virtual: {vcpus} vCPUs
Memoria RAM: {memory} MB
Memoria Máxima: {info[1] // 1024} MB
Tiempo de CPU: {info[4] // 1000000000} segundos

SISTEMA OPERATIVO:
─────────────────────────────────────────────────
Tipo: {os_type} (Máquina: {machine_type})

REDES:
─────────────────────────────────────────────────
{chr(10).join(network_info) if network_info else '  - No hay interfaces de red configuradas'}

ALMACENAMIENTO:
─────────────────────────────────────────────────
{chr(10).join(disk_info) if disk_info else '  - No hay discos configurados'}

CDROM:
─────────────────────────────────────────────────
{chr(10).join(cdrom_info) if cdrom_info else '  - No hay CDROM configurado o ISO montado'}


ÚLTIMA ACTUALIZACIÓN:
─────────────────────────────────────────────────
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, details)

        except libvirt.libvirtError as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, f"Error al obtener detalles: {str(e)}")

    def start_vm(self):
        """Iniciar máquina virtual"""
        if not self.selected_vm:
            messagebox.showwarning("Advertencia", "Seleccione una máquina virtual")
            return

        try:
            vm = self.conn.lookupByName(self.selected_vm)
            if vm.isActive():
                messagebox.showinfo("Información", "La máquina virtual ya está ejecutándose")
                return

            vm.create()
            messagebox.showinfo("Éxito", f"Máquina virtual '{self.selected_vm}' iniciada correctamente")
            self.refresh_vm_list()

        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"Error al iniciar VM: {str(e)}")

    def stop_vm(self):
        """Detener máquina virtual"""
        if not self.selected_vm:
            messagebox.showwarning("Advertencia", "Seleccione una máquina virtual")
            return

        result = messagebox.askyesno("Confirmación",
                                     f"¿Está seguro de detener '{self.selected_vm}'?")
        if not result:
            return

        try:
            vm = self.conn.lookupByName(self.selected_vm)
            if not vm.isActive():
                messagebox.showinfo("Información", "La máquina virtual ya está detenida")
                return

            vm.shutdown() # Envía una señal ACPI de apagado
            messagebox.showinfo("Éxito", f"Señal de apagado enviada a '{self.selected_vm}'")
            self.refresh_vm_list()

            # Esperar un poco y luego intentar destruir si no se apaga
            # Esto es un comportamiento más robusto
            self.root.after(5000, lambda: self._check_and_destroy_vm(vm))

        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"Error al detener VM: {str(e)}")

    def _check_and_destroy_vm(self, vm):
        """Verifica si la VM se apagó y la destruye si no."""
        try:
            state, reason = vm.state()
            if state != libvirt.VIR_DOMAIN_SHUTOFF:
                response = messagebox.askyesno(
                    "Forzar apagado",
                    f"La VM '{vm.name()}' no se apagó. ¿Desea forzar su apagado (destruir)? "
                    "Esto puede causar pérdida de datos."
                )
                if response:
                    vm.destroy()
                    messagebox.showinfo("Éxito", f"VM '{vm.name()}' forzada a apagarse.")
                    self.refresh_vm_list()
            else:
                self.refresh_vm_list() # Ya se apagó, solo refrescar
        except libvirt.libvirtError as e:
            print(f"Error en _check_and_destroy_vm: {e}")
            self.refresh_vm_list() # Refrescar de todos modos


    def delete_vm(self):
        """Eliminar máquina virtual"""
        if not self.selected_vm:
            messagebox.showwarning("Advertencia", "Seleccione una máquina virtual")
            return

        result = messagebox.askyesno("Confirmación",
                                     f"¿Está seguro de eliminar '{self.selected_vm}'?\n"
                                     "Esta acción no se puede deshacer y eliminará también el archivo de disco.")
        if not result:
            return

        try:
            vm = self.conn.lookupByName(self.selected_vm)

            # Obtener la ruta del disco antes de indefinir la VM
            disk_path = None
            try:
                xml_desc = vm.XMLDesc(0)
                root = ET.fromstring(xml_desc)
                disk_source = root.find('.//disk[@device="disk"]/source')
                if disk_source is not None:
                    disk_path = disk_source.get('file')
            except Exception as xml_error:
                print(f"Advertencia: No se pudo obtener la ruta del disco del XML: {xml_error}")

            # Detener si está ejecutándose
            if vm.isActive():
                vm.destroy() # Forzar apagado para poder eliminar

            # Eliminar definición
            vm.undefine()
            messagebox.showinfo("Éxito", f"Máquina virtual '{self.selected_vm}' eliminada.")
            
            # Eliminar el archivo de disco asociado (automático con la confirmación)
            if disk_path and os.path.exists(disk_path):
                try:
                    os.remove(disk_path)
                    messagebox.showinfo("Disco Eliminado", f"Archivo de disco '{disk_path}' eliminado.")
                except OSError as e:
                    messagebox.showerror("Error", f"No se pudo eliminar el archivo de disco '{disk_path}':\n{e}")

            self.selected_vm = None
            self.info_text.delete(1.0, tk.END)
            self.refresh_vm_list()

        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"Error al eliminar VM: {str(e)}")

    def connect_to_vm_display(self):
        """
        Intenta conectar a la pantalla VNC de la VM seleccionada
        lanzando un cliente VNC externo.
        """
        if not self.selected_vm:
            messagebox.showwarning("Advertencia", "Seleccione una máquina virtual para conectar.")
            return

        try:
            vm = self.conn.lookupByName(self.selected_vm)
            if not vm.isActive():
                messagebox.showwarning("Advertencia", f"La VM '{self.selected_vm}' no está en ejecución. Iníciela primero.")
                return

            # --- NUEVA FORMA DE OBTENER LA DIRECCIÓN VNC DESDE EL XML Y virsh ---
            xml_desc = vm.XMLDesc(0)
            root = ET.fromstring(xml_desc)
            
            graphics_elem = root.find(".//graphics[@type='vnc']")
            if graphics_elem is None:
                messagebox.showerror("Error de VNC", "No se encontró configuración VNC en el XML de la VM.")
                return
            
            vnc_port_xml = graphics_elem.get('port') # Esto puede ser '-1'
            vnc_listen_address = graphics_elem.get('listen', '127.0.0.1') # Por defecto a 127.0.0.1 si no está en el XML

            vnc_port = None
            if vnc_port_xml == "-1": # Puerto asignado dinámicamente (autoport='yes')
                try:
                    # Usar virsh vncdisplay para obtener el puerto asignado dinámicamente
                    # Asegúrate de que virsh esté en el PATH o usa la ruta completa si es necesario
                    virsh_cmd = ["virsh", "vncdisplay", self.selected_vm]
                    virsh_result = subprocess.run(virsh_cmd, capture_output=True, text=True, check=True)
                    virsh_output = virsh_result.stdout.strip()
                    
                    if not virsh_output:
                        messagebox.showerror("Error VNC", "Virsh no devolvió información del display VNC.")
                        return

                    # Parsear la salida de virsh vncdisplay (ej. ':1' o '127.0.0.1:5901')
                    if ":" in virsh_output:
                        parts = virsh_output.split(':')
                        if len(parts) == 2:
                            if parts[0] == "": # Caso ':N' (ej. :1 -> 5901)
                                try:
                                    vnc_port = 5900 + int(parts[1])
                                except ValueError:
                                    messagebox.showerror("Error VNC", f"Formato de display VNC inválido desde virsh (puerto): {virsh_output}")
                                    return
                            else: # Caso 'IP:N' (ej. 127.0.0.1:5901)
                                vnc_listen_address = parts[0] # Actualizar por si acaso
                                try:
                                    vnc_port = int(parts[1])
                                except ValueError:
                                    messagebox.showerror("Error VNC", f"Formato de display VNC inválido desde virsh (host:puerto): {virsh_output}")
                                    return
                        else:
                            messagebox.showerror("Error VNC", f"Formato de display VNC desconocido desde virsh: {virsh_output}")
                            return
                    else:
                         messagebox.showerror("Error VNC", f"Formato de display VNC inesperado desde virsh: {virsh_output}")
                         return

                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error VNC", f"No se pudo obtener el display VNC de la VM (virsh vncdisplay falló):\n{e.stderr}")
                    return
                except Exception as e:
                    messagebox.showerror("Error VNC", f"Error al parsear la salida de virsh vncdisplay: {e}")
                    return
            else: # Puerto fijo en el XML
                try:
                    vnc_port = int(vnc_port_xml)
                except ValueError:
                    messagebox.showerror("Error VNC", f"Puerto VNC inválido en el XML: {vnc_port_xml}")
                    return

            if vnc_port is None:
                messagebox.showerror("Error VNC", "No se pudo determinar el puerto VNC.")
                return

            vnc_address = f"{vnc_listen_address}:{vnc_port}"
            # --- FIN NUEVA FORMA ---

            # Intentar lanzar Vinagre (Visor de Escritorios Remotos)
            try:
                subprocess.Popen(["vinagre", vnc_address])
                messagebox.showinfo("Conectando...", f"Lanzando Vinagre para conectar a {vnc_address}")
            except FileNotFoundError:
                # Si Vinagre no se encuentra, intentar Remmina
                try:
                    subprocess.Popen(["remmina", f"vnc://{vnc_address}"])
                    messagebox.showinfo("Conectando...", f"Lanzando Remmina para conectar a {vnc_address}")
                except FileNotFoundError:
                    messagebox.showerror("Error",
                                         "No se encontraron clientes VNC (Vinagre o Remmina).\n"
                                         "Por favor, instale uno: 'sudo apt install vinagre' o 'sudo apt install remmina remmina-plugin-vnc'")
            except Exception as e:
                messagebox.showerror("Error", f"Error al lanzar el cliente VNC: {str(e)}")

        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"Error al obtener información de la VM para VNC: {str(e)}")


    def create_vm_dialog(self):
        """Diálogo para crear nueva VM"""
        dialog = VMCreationDialog(self.root, self.conn, self.refresh_vm_list)

    def auto_refresh(self):
        """Auto-actualizar la lista cada 5 segundos"""
        self.time_label.config(text=datetime.now().strftime('%H:%M:%S'))
        if self.selected_vm:
            # Refresh details of the selected VM to show live status
            # Solo si la VM seleccionada está activa para evitar errores si se elimina
            try:
                vm = self.conn.lookupByName(self.selected_vm)
                if vm.isActive():
                    self.show_vm_details(self.selected_vm)
            except libvirt.libvirtError:
                # VM ya no existe o no se puede encontrar
                self.selected_vm = None
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(1.0, "VM seleccionada ya no existe o no está disponible.")

        self.refresh_vm_list() # Refresh the VM list in the treeview
        self.root.after(5000, self.auto_refresh)

    def __del__(self):
        """Cerrar conexión al destruir"""
        if self.conn and self.conn.isAlive(): # Añadir isAlive para evitar error "invalid connection pointer"
            try:
                self.conn.close()
            except libvirt.libvirtError as e:
                print(f"Error al cerrar la conexión libvirt en __del__: {e}")


class VMCreationDialog:
    def __init__(self, parent, conn, refresh_callback):
        self.conn = conn
        self.refresh_callback = refresh_callback

        # Crear ventana
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Crear Nueva Máquina Virtual")
        self.dialog.geometry("600x550") # Aumentado un poco para mejor layout
        self.dialog.configure(bg='#2c3e50')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Variables
        self.vm_name = tk.StringVar()
        self.os_type = tk.StringVar(value="linux")
        self.memory = tk.StringVar(value="1024")
        self.vcpus = tk.StringVar(value="1")
        self.disk_size = tk.StringVar(value="10") # Tamaño en GB
        self.iso_path = tk.StringVar()

        self.setup_dialog()

    def setup_dialog(self):
        """Configurar el diálogo"""
        # Título
        title = tk.Label(self.dialog, text="Crear Nueva Máquina Virtual",
                         font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title.pack(pady=20)

        # Frame principal
        main_frame = tk.Frame(self.dialog, bg='#34495e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Configuraciones
        configs = [
            ("Nombre de la VM:", self.vm_name),
            ("Memoria RAM (MB):", self.memory),
            ("CPUs Virtuales:", self.vcpus),
            ("Tamaño del disco (GB):", self.disk_size),
        ]

        for i, (label_text, var) in enumerate(configs):
            frame = tk.Frame(main_frame, bg='#34495e')
            frame.pack(fill=tk.X, pady=10)

            label = tk.Label(frame, text=label_text, fg='white', bg='#34495e',
                             font=('Arial', 12))
            label.pack(anchor=tk.W)

            entry = tk.Entry(frame, textvariable=var, font=('Arial', 11), width=40)
            entry.pack(fill=tk.X, pady=5)

        # Tipo de OS
        os_frame = tk.Frame(main_frame, bg='#34495e')
        os_frame.pack(fill=tk.X, pady=10)

        os_label = tk.Label(os_frame, text="Tipo de Sistema Operativo:",
                            fg='white', bg='#34495e', font=('Arial', 12))
        os_label.pack(anchor=tk.W)

        os_combo = ttk.Combobox(os_frame, textvariable=self.os_type,
                                values=['linux', 'windows', 'other'], state='readonly')
        os_combo.pack(fill=tk.X, pady=5)

        # ISO Path
        iso_frame = tk.Frame(main_frame, bg='#34495e')
        iso_frame.pack(fill=tk.X, pady=10)

        iso_label = tk.Label(iso_frame, text="Archivo ISO (opcional):",
                             fg='white', bg='#34495e', font=('Arial', 12))
        iso_label.pack(anchor=tk.W)

        iso_path_frame = tk.Frame(iso_frame, bg='#34495e')
        iso_path_frame.pack(fill=tk.X, pady=5)

        iso_entry = tk.Entry(iso_path_frame, textvariable=self.iso_path,
                             font=('Arial', 11))
        iso_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = tk.Button(iso_path_frame, text="Examinar",
                               command=self.browse_iso, bg='#3498db', fg='white')
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Botones
        button_frame = tk.Frame(main_frame, bg='#34495e')
        button_frame.pack(fill=tk.X, pady=20)

        create_btn = tk.Button(button_frame, text="Crear VM", command=self.create_vm,
                               bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                               width=15)
        create_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = tk.Button(button_frame, text="Cancelar", command=self.dialog.destroy,
                               bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                               width=15)
        cancel_btn.pack(side=tk.RIGHT)

    def browse_iso(self):
        """Examinar archivo ISO"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo ISO",
            filetypes=[("Archivos ISO", "*.iso"), ("Todos los archivos", "*.*")],
            initialdir="/var/lib/libvirt/images/" # Sugerir el directorio de imágenes
        )
        if filename:
            self.iso_path.set(filename)

    def create_qcow2_disk(self, disk_path, disk_size_gb):
        """Crea el archivo de disco QCOW2."""
        try:
            disk_dir = os.path.dirname(disk_path)
            if not os.path.exists(disk_dir):
                os.makedirs(disk_dir, exist_ok=True)

            command = ["qemu-img", "create", "-f", "qcow2", disk_path, f"{disk_size_gb}G"]
            
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Comando ejecutado para crear disco: {' '.join(command)}")
            print(f"Salida de qemu-img: {result.stdout}")
            messagebox.showinfo("Disco Creado", f"Archivo de disco QCOW2 creado: {disk_path}")
            return True
        except FileNotFoundError:
            messagebox.showerror("Error", "El comando 'qemu-img' no fue encontrado.\n"
                                          "Asegúrese de que QEMU esté instalado (sudo apt install qemu-utils).")
            return False
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error al crear disco", f"Fallo al crear el disco QCOW2:\n{e.stderr}")
            return False
        except Exception as e:
            messagebox.showerror("Error al crear disco", f"Ocurrió un error inesperado al crear el disco:\n{e}")
            return False

    def create_vm(self):
        """Crear la máquina virtual"""
        if not self.vm_name.get().strip():
            messagebox.showerror("Error", "El nombre de la VM es requerido.")
            return

        try:
            memory_mb = int(self.memory.get())
            vcpu_count = int(self.vcpus.get())
            disk_gb = int(self.disk_size.get())
        except ValueError:
            messagebox.showerror("Error", "Los valores numéricos de memoria, CPU y disco deben ser enteros válidos.")
            return

        vm_name_cleaned = self.vm_name.get().strip()
        disk_path = f"/var/lib/libvirt/images/{vm_name_cleaned}.qcow2"

        # *** Paso crucial: Crear el archivo de disco ANTES de definir la VM ***
        if not self.create_qcow2_disk(disk_path, disk_gb):
            return # Si la creación del disco falla, abortar la creación de la VM

        # Crear XML de configuración
        vm_xml = self.generate_vm_xml()

        try:
            # Definir la VM
            self.conn.defineXML(vm_xml)
            messagebox.showinfo("Éxito", f"Máquina virtual '{vm_name_cleaned}' creada correctamente.")
            self.refresh_callback()
            self.dialog.destroy()

        except libvirt.libvirtError as e:
            messagebox.showerror("Error al definir VM", f"Error al crear VM: {str(e)}\n"
                                                         f"Verifique la consola para más detalles del error XML.")
            # Si la definición falla, ofrecer limpiar el disco creado
            if os.path.exists(disk_path):
                clean_disk = messagebox.askyesno(
                    "Limpiar Disco",
                    f"La definición de la VM falló. ¿Desea eliminar el archivo de disco '{disk_path}' que se creó?"
                )
                if clean_disk:
                    try:
                        os.remove(disk_path)
                        messagebox.showinfo("Limpieza", "Archivo de disco eliminado.")
                    except OSError as ose:
                        messagebox.showerror("Error de limpieza", f"No se pudo eliminar el disco: {ose}")

    def generate_vm_xml(self):
        """Generar XML de configuración de la VM"""
        name = self.vm_name.get().strip()
        memory_kb = int(self.memory.get()) * 1024
        vcpus = self.vcpus.get()
        os_type = self.os_type.get()
        disk_path = f"/var/lib/libvirt/images/{name}.qcow2"
        iso_path_val = self.iso_path.get().strip()

        # XML básico
        xml = f"""<domain type='qemu'>
  <name>{name}</name>
  <memory unit='KiB'>{memory_kb}</memory>
  <currentMemory unit='KiB'>{memory_kb}</currentMemory>
  <vcpu placement='static'>{vcpus}</vcpu>
  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <boot dev='hd'/>
    <boot dev='cdrom'/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode='host-model' check='partial'/>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x04' slot='0x00' function='0x0'/>
    </disk>"""

        # Agregar CDROM si hay ISO
        if iso_path_val:
            xml += f"""
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='{iso_path_val}'/>
      <target dev='sdb' bus='sata'/>
      <readonly/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>"""

        # Continuar con el resto de la configuración
        xml += f"""
    <controller type='usb' index='0' model='qemu-xhci' ports='15'>
      <address type='pci' domain='0x0000' bus='0x02' slot='0x00' function='0x0'/>
    </controller>
    <controller type='sata' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x1f' function='0x2'/>
    </controller>
    <controller type='pci' index='0' model='pcie-root'/>
    <controller type='pci' index='1' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='1' port='0x10'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0' multifunction='on'/>
    </controller>
    <controller type='pci' index='2' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='2' port='0x11'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x1'/>
    </controller>
    <controller type='pci' index='3' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='3' port='0x12'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x2'/>
    </controller>
    <controller type='pci' index='4' model='pcie-root-port'>
      <model name='pcie-root-port'/>
      <target chassis='4' port='0x13'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x3'/>
    </controller>
    <controller type='virtio-serial' index='0'>
      <address type='pci' domain='0x0000' bus='0x03' slot='0x00' function='0x0'/>
    </controller>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
    </interface>
    <serial type='pty'>
      <target type='isa-serial' port='0'>
        <model name='isa-serial'/>
      </target>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
      <address type='virtio-serial' controller='0' bus='0' port='1'/>
    </channel>
    <input type='tablet' bus='usb'>
      <address type='usb' bus='0' port='1'/>
    </input>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'>
      <listen type='address' address='127.0.0.1'/>
    </graphics>
    <sound model='ich9'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x1b' function='0x0'/>
    </sound>
    <video>
      <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1' primary='yes'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x0'/>
    </video>
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x05' slot='0x00' function='0x0'/>
    </memballoon>
    <rng model='virtio'>
      <backend model='random'>/dev/urandom</backend>
      <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
    </rng>
  </devices>
</domain>"""

        return xml

def main():
    # Verificar si libvirt está disponible
    try:
        import libvirt
    except ImportError:
        messagebox.showerror("Error", "libvirt-python no está instalado.\n"
                                      "Instale con: sudo apt install python3-libvirt")
        return

    # Crear aplicación
    root = tk.Tk()
    app = VirtualizationClient(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario")
    finally:
        if hasattr(app, 'conn') and app.conn:
            app.conn.close()

if __name__ == "__main__":
    main()