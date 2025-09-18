import psutil
import platform
import time
import json
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
    
    def get_system_info(self):
        """
        Obtém informações básicas do sistema
        
        Returns:
            dict: Informações do sistema
        """
        try:
            uname = platform.uname()
            
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            memory = psutil.virtual_memory()
            
            disk = psutil.disk_usage('/')
            
            return {
                'Sistema': f"{uname.system} {uname.release}",
                'Versão': uname.version,
                'Máquina': uname.machine,
                'Processador': uname.processor,
                'CPU Física': f"{cpu_count} cores",
                'CPU Lógica': f"{cpu_count_logical} threads",
                'Frequência CPU': f"{cpu_freq.max:.0f} MHz" if cpu_freq else "N/A",
                'RAM Total': f"{self._bytes_to_gb(memory.total):.1f} GB",
                'Disco Total': f"{self._bytes_to_gb(disk.total):.1f} GB",
                'Uptime Sistema': self._get_uptime()
            }
        except Exception as e:
            return {'Erro': str(e)}
    
    def get_real_time_stats(self):
        """
        Obtém estatísticas em tempo real do sistema
        
        Returns:
            dict: Estatísticas atuais
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            net_io = psutil.net_io_counters()
            
            process_count = len(psutil.pids())
            
            stats = {
                'cpu': cpu_percent,
                'cpu_cores': cpu_per_core,
                'memory': memory.percent,
                'memory_used': self._bytes_to_gb(memory.used),
                'memory_available': self._bytes_to_gb(memory.available),
                'swap': swap.percent,
                'disk': disk.percent,
                'disk_used': self._bytes_to_gb(disk.used),
                'disk_free': self._bytes_to_gb(disk.free),
                'processes': process_count,
                'network_sent': self._bytes_to_mb(net_io.bytes_sent),
                'network_recv': self._bytes_to_mb(net_io.bytes_recv),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            stats['temperature'] = entries[0].current
                            break
            except:
                pass
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_top_processes(self, limit=10, sort_by='cpu'):
        """
        Obtém os processos que mais consomem recursos
        
        Args:
            limit (int): Número de processos a retornar
            sort_by (str): Critério de ordenação ('cpu', 'memory')
            
        Returns:
            list: Lista de processos
        """
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    pinfo['memory_mb'] = pinfo['memory_info'].rss / 1024 / 1024
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if sort_by == 'cpu':
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == 'memory':
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_disk_usage_by_drive(self):
        """
        Obtém uso de disco por drive
        
        Returns:
            dict: Uso de disco por drive
        """
        try:
            drives = {}
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drives[partition.device] = {
                        'total': self._bytes_to_gb(usage.total),
                        'used': self._bytes_to_gb(usage.used),
                        'free': self._bytes_to_gb(usage.free),
                        'percent': (usage.used / usage.total) * 100,
                        'filesystem': partition.fstype
                    }
                except PermissionError:
                    continue
                    
            return drives
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_info(self):
        """
        Obtém informações de rede
        
        Returns:
            dict: Informações de rede
        """
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            network_info = {}
            
            for interface, addresses in interfaces.items():
                interface_info = {
                    'addresses': [],
                    'is_up': stats[interface].isup if interface in stats else False,
                    'speed': stats[interface].speed if interface in stats else 0,
                }
                
                for addr in addresses:
                    if addr.family.name == 'AF_INET':
                        interface_info['addresses'].append({
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
                    
                if interface in io_counters:
                    io = io_counters[interface]
                    interface_info.update({
                        'bytes_sent': self._bytes_to_mb(io.bytes_sent),
                        'bytes_recv': self._bytes_to_mb(io.bytes_recv),
                        'packets_sent': io.packets_sent,
                        'packets_recv': io.packets_recv
                    })
                
                network_info[interface] = interface_info
            
            return network_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _bytes_to_gb(self, bytes_value):
        """Converte bytes para GB"""
        return bytes_value / (1024 ** 3)
    
    def _bytes_to_mb(self, bytes_value):
        """Converte bytes para MB"""
        return bytes_value / (1024 ** 2)
    
    def _get_uptime(self):
        """Obtém o tempo de atividade do sistema"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days}d {hours}h {minutes}m"
        except:
            return "N/A"
    
    def export_report(self, filename=None):
        """
        Exporta um relatório completo do sistema
        
        Args:
            filename (str): Nome do arquivo (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"system_report_{timestamp}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_info': self.get_system_info(),
                'real_time_stats': self.get_real_time_stats(),
                'top_processes_cpu': self.get_top_processes(sort_by='cpu'),
                'top_processes_memory': self.get_top_processes(sort_by='memory'),
                'disk_usage': self.get_disk_usage_by_drive(),
                'network_info': self.get_network_info()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return filename
            
        except Exception as e:
            return f"Erro ao gerar relatório: {e}"