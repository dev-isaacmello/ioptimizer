"""
Módulo para limpeza do sistema
"""

import os
import shutil
import tempfile
import glob
from pathlib import Path
import winreg
from datetime import datetime, timedelta

class SystemCleaner:
    def __init__(self):
        self.temp_dirs = [
            os.path.join(os.environ.get('TEMP', ''), ''),
            os.path.join(os.environ.get('TMP', ''), ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            r'C:\Windows\Temp',
            r'C:\Windows\Prefetch',
            r'C:\Windows\SoftwareDistribution\Download'
        ]
        
        self.browser_cache_dirs = {
            'Chrome': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Code Cache')
            ],
            'Edge': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Code Cache')
            ],
            'Firefox': [
                os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles', '*', 'cache2')
            ]
        }
        
        self.log_dirs = [
            r'C:\Windows\Logs',
            r'C:\Windows\System32\LogFiles',
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'WebCache')
        ]
    
    def get_directory_size(self, directory):
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    try:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except (OSError, FileNotFoundError):
            pass
        return total_size
    
    def clean_temp_files(self):
        
        total_freed = 0
        files_deleted = 0
        errors = []
        
        for temp_dir in self.temp_dirs:
            if not os.path.exists(temp_dir):
                continue
                
            try:
                size_before = self.get_directory_size(temp_dir)
                
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            
                            if os.path.getmtime(file_path) < (datetime.now() - timedelta(days=1)).timestamp():
                                os.remove(file_path)
                                files_deleted += 1
                        except (PermissionError, FileNotFoundError, OSError) as e:
                            errors.append(f"Erro ao deletar {file_path}: {str(e)}")
                    
                    
                    for dir_name in dirs:
                        try:
                            dir_path = os.path.join(root, dir_name)
                            if not os.listdir(dir_path):  
                                os.rmdir(dir_path)
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
                
                
                size_after = self.get_directory_size(temp_dir)
                total_freed += (size_before - size_after)
                
            except Exception as e:
                errors.append(f"Erro ao limpar {temp_dir}: {str(e)}")
        
        return {
            'space_freed': self._bytes_to_readable(total_freed),
            'files_deleted': files_deleted,
            'errors': errors
        }
    
    def clean_browser_cache(self):
        
        total_freed = 0
        results = {}
        
        for browser, cache_dirs in self.browser_cache_dirs.items():
            browser_freed = 0
            files_deleted = 0
            
            for cache_dir in cache_dirs:
                if '*' in cache_dir:
                    expanded_dirs = glob.glob(cache_dir)
                    for expanded_dir in expanded_dirs:
                        if os.path.exists(expanded_dir):
                            size_before = self.get_directory_size(expanded_dir)
                            try:
                                shutil.rmtree(expanded_dir, ignore_errors=True)
                                browser_freed += size_before
                                files_deleted += 1
                            except Exception:
                                continue
                else:
                    if os.path.exists(cache_dir):
                        size_before = self.get_directory_size(cache_dir)
                        try:
                            shutil.rmtree(cache_dir, ignore_errors=True)
                            browser_freed += size_before
                            files_deleted += 1
                        except Exception:
                            continue
            
            if browser_freed > 0:
                results[browser] = {
                    'space_freed': self._bytes_to_readable(browser_freed),
                    'files_deleted': files_deleted
                }
                total_freed += browser_freed
        
        results['total_freed'] = self._bytes_to_readable(total_freed)
        return results
    
    def clean_recycle_bin(self):
        
        try:
            import winshell
            
            recycle_bin_size = 0
            try:
                for item in winshell.recycle_bin():
                    try:
                        recycle_bin_size += os.path.getsize(item.original_filename())
                    except:
                        continue
            except:
                pass
            
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            
            return {
                'space_freed': self._bytes_to_readable(recycle_bin_size),
                'success': True
            }
            
        except ImportError:
            try:
                import subprocess
                result = subprocess.run(['powershell', '-Command', 
                                       'Clear-RecycleBin -Force -Confirm:$false'], 
                                      capture_output=True, text=True)
                return {
                    'space_freed': 'Desconhecido',
                    'success': result.returncode == 0
                }
            except:
                return {
                    'space_freed': '0 B',
                    'success': False,
                    'error': 'Não foi possível esvaziar a lixeira'
                }
    
    def clean_system_logs(self):
        
        total_freed = 0
        files_deleted = 0
        errors = []
        
        for log_dir in self.log_dirs:
            if not os.path.exists(log_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(('.log', '.txt', '.etl')):
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.getmtime(file_path) < (datetime.now() - timedelta(days=7)).timestamp():
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    total_freed += file_size
                                    files_deleted += 1
                            except (PermissionError, FileNotFoundError, OSError) as e:
                                errors.append(f"Erro ao deletar {file_path}: {str(e)}")
                                
            except Exception as e:
                errors.append(f"Erro ao acessar {log_dir}: {str(e)}")
        
        return {
            'space_freed': self._bytes_to_readable(total_freed),
            'files_deleted': files_deleted,
            'errors': errors
        }
    
    def clean_windows_update_cache(self):
        
        try:
            import subprocess
            
            services = ['wuauserv', 'cryptSvc', 'bits', 'msiserver']
            
            for service in services:
                try:
                    subprocess.run(['net', 'stop', service], 
                                 capture_output=True, check=False)
                except:
                    continue
            
            cache_dirs = [
                r'C:\Windows\SoftwareDistribution\Download',
                r'C:\Windows\System32\catroot2'
            ]
            
            total_freed = 0
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        size_before = self.get_directory_size(cache_dir)
                        shutil.rmtree(cache_dir, ignore_errors=True)
                        total_freed += size_before
                    except:
                        continue
            
            for service in services:
                try:
                    subprocess.run(['net', 'start', service], 
                                 capture_output=True, check=False)
                except:
                    continue
            
            return {
                'space_freed': self._bytes_to_readable(total_freed),
                'success': True
            }
            
        except Exception as e:
            return {
                'space_freed': '0 B',
                'success': False,
                'error': str(e)
            }
    
    def full_cleanup(self):
        
        results = {}
        
        print("🧹 Limpando arquivos temporários...")
        results['temp_files'] = self.clean_temp_files()
        
        print("🌐 Limpando cache dos navegadores...")
        results['browser_cache'] = self.clean_browser_cache()
        
        print("🗑️ Esvaziando lixeira...")
        results['recycle_bin'] = self.clean_recycle_bin()
        
        print("📝 Limpando logs do sistema...")
        results['system_logs'] = self.clean_system_logs()
        
        print("🔄 Limpando cache do Windows Update...")
        results['windows_update'] = self.clean_windows_update_cache()
        
        
        total_space = 0
        for category, data in results.items():
            if isinstance(data, dict) and 'space_freed' in data:
                
                space_str = data['space_freed']
                if 'MB' in space_str:
                    total_space += float(space_str.split()[0]) * 1024 * 1024
                elif 'GB' in space_str:
                    total_space += float(space_str.split()[0]) * 1024 * 1024 * 1024
                elif 'KB' in space_str:
                    total_space += float(space_str.split()[0]) * 1024
        
        results['total_space_freed'] = self._bytes_to_readable(total_space)
        results['cleanup_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return results
    
    def _bytes_to_readable(self, bytes_value):
        
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"