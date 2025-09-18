import ctypes
import sys
import os
from subprocess import run, PIPE
from colorama import Fore

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    if not is_admin():
        print(f"{Fore.RED}⚠️  Privilégios de administrador necessários.")
        if input(f"{Fore.CYAN}Continuar mesmo assim? (s/n): ").lower() != 's':
            sys.exit(1)
        run(['runas', '/user:Administrator', sys.executable] + sys.argv)
        sys.exit(0)

def get_user_info():
    try:
        import getpass
        import platform

        return {
            'username': getpass.getuser(),
            'is_admin': is_admin(),
            'os': platform.system(),
            'architecture': platform.machine(),
            'version': platform.version(),
            'release': platform.release(),
            'processor': platform.processor(),
            'memory': platform.system_memory(),
            'disk': platform.disk_usage('/'),
            'network': platform.node(),
            'python_version': sys.version,
            'system_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'machine': platform.machine(),
            'processor': platform.processor(),
        }
    except Exception as e:
        print(f"{Fore.RED}Erro ao obter informações do usuário: {e}")
        return None
    
def run_as_admin(cmd):
    if not is_admin():
        return False, "", "Privilégios de administrador necessários."
    try:
        result = run(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        return True, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    except Exception as e:
        return False, "", f"Erro ao executar comando: {e}"