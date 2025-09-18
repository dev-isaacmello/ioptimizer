"""
Módulo para gerenciamento de processos do sistema
"""

import psutil
import time
import os
from datetime import datetime
from collections import defaultdict

class ProcessManager:
    def __init__(self):
        self.blocked_processes = [
            'System', 'Registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
            'winlogon.exe', 'services.exe', 'lsass.exe', 'svchost.exe',
            'dwm.exe', 'explorer.exe'
        ]
        self.process_history = defaultdict(list)
    
    def get_all_processes(self):
        
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'create_time', 'status', 'username']):
                try:
                    pinfo = proc.info
                    pinfo['memory_mb'] = pinfo['memory_info'].rss / 1024 / 1024
                    pinfo['create_time_str'] = datetime.fromtimestamp(pinfo['create_time']).strftime('%H:%M:%S')
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return processes
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_resource_heavy_processes(self, cpu_threshold=5.0, memory_threshold=100):
        
        try:
            heavy_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / 1024 / 1024
                    
                    if (pinfo['cpu_percent'] > cpu_threshold or memory_mb > memory_threshold):
                        pinfo['memory_mb'] = memory_mb
                        pinfo['cpu'] = pinfo['cpu_percent']
                        pinfo['memory'] = pinfo['memory_percent']
                        heavy_processes.append(pinfo)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            heavy_processes.sort(key=lambda x: x['cpu'], reverse=True)
            return heavy_processes
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_process_details(self, pid):
            
        try:
            proc = psutil.Process(pid)
            
            
            details = {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'create_time': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent(),
                'memory_info': proc.memory_info()._asdict(),
                'num_threads': proc.num_threads(),
            }
            
            try:
                details['username'] = proc.username()
                details['cwd'] = proc.cwd()
                details['exe'] = proc.exe()
                details['cmdline'] = ' '.join(proc.cmdline())
                details['connections'] = len(proc.connections())
                details['open_files'] = len(proc.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            return details
            
        except psutil.NoSuchProcess:
            return {'error': 'Processo não encontrado'}
        except Exception as e:
            return {'error': str(e)}
    
    def kill_process(self, pid, force=False):
       
        try:
            proc = psutil.Process(pid)
            
            if proc.name() in self.blocked_processes:
                return False
            
            if force:
                proc.kill()  # SIGKILL
            else:
                proc.terminate()  # SIGTERM
                
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                if not force:
                    proc.kill()
                    proc.wait(timeout=2)
            
            return True
            
        except psutil.NoSuchProcess:
            return True  
        except psutil.AccessDenied:
            return False  
        except Exception:
            return False
    
    def kill_processes_by_name(self, process_name):
       
        killed_count = 0
        failed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        if self.kill_process(proc.info['pid']):
                            killed_count += 1
                        else:
                            failed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    failed_count += 1
                    
            return {
                'killed': killed_count,
                'failed': failed_count,
                'total_found': killed_count + failed_count
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_startup_processes(self):
        try:
            import winreg
            startup_processes = []
            
            startup_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            ]
            
            for hkey, subkey in startup_keys:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                startup_processes.append({
                                    'name': name,
                                    'command': value,
                                    'location': f"{hkey}\\{subkey}",
                                    'enabled': True
                                })
                                i += 1
                            except OSError:
                                break
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
            
            return startup_processes
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def monitor_process_performance(self, duration=60, interval=2):
        try:
            monitoring_data = {
                'start_time': datetime.now().isoformat(),
                'duration': duration,
                'interval': interval,
                'samples': []
            }
            
            end_time = time.time() + duration
            
            while time.time() < end_time:
                sample = {
                    'timestamp': datetime.now().isoformat(),
                    'processes': []
                }
                
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        pinfo = proc.info
                        if pinfo['cpu_percent'] > 1.0:  
                            sample['processes'].append(pinfo)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                sample['processes'].sort(key=lambda x: x['cpu_percent'], reverse=True)
                sample['processes'] = sample['processes'][:10]
                
                monitoring_data['samples'].append(sample)
                time.sleep(interval)
            
            monitoring_data['end_time'] = datetime.now().isoformat()
            return monitoring_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_services(self):
        
        try:
            services = []
            
            for service in psutil.win_service_iter():
                try:
                    service_info = service.as_dict()
                    services.append({
                        'name': service_info['name'],
                        'display_name': service_info['display_name'],
                        'status': service_info['status'],
                        'start_type': service_info['start_type'],
                        'pid': service_info.get('pid'),
                        'description': service_info.get('description', 'N/A')
                    })
                except Exception:
                    continue
            
            return services
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def optimize_processes(self):
        
        try:
            results = {
                'processes_killed': 0,
                'memory_freed': 0,
                'actions': []
            }
            
            resource_wasters = [
                'chrome.exe', 'firefox.exe', 'msedge.exe',  
                'spotify.exe', 'discord.exe', 'steam.exe',  
                'skype.exe', 'teams.exe'
            ]
            
            process_count = defaultdict(int)
            process_memory = defaultdict(float)
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = proc.info['name'].lower()
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    
                    process_count[name] += 1
                    process_memory[name] += memory_mb
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            for process_name in resource_wasters:
                if process_count[process_name] > 3: 
                    procs = [p for p in psutil.process_iter(['pid', 'name', 'create_time']) 
                            if p.info['name'].lower() == process_name]
                    
                    procs.sort(key=lambda x: x.info['create_time'])
                    
                    for proc in procs[:-2]:
                        if self.kill_process(proc.info['pid']):
                            results['processes_killed'] += 1
                            results['memory_freed'] += process_memory[process_name] / process_count[process_name]
                            results['actions'].append(f"Encerrou instância antiga de {process_name}")
            
            return results
            
        except Exception as e:
            return {'error': str(e)}