import os
import sys
import time
from colorama import init, Fore, Back, Style
import click

init(autoreset=True)

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from system_monitor import SystemMonitor
    from system_cleaner import SystemCleaner
    from process_manager import ProcessManager
    from startup_manager import StartupManager
    from system_tweaks import SystemTweaks
    from admin_check import is_admin, request_admin
except ImportError as e:
    print(f"{Fore.RED}Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os arquivos estão no diretório correto.")
    sys.exit(1)

class iOptimizer:
    def __init__(self):
        self.monitor = SystemMonitor()
        self.cleaner = SystemCleaner()
        self.process_mgr = ProcessManager()
        self.startup_mgr = StartupManager()
        self.tweaks = SystemTweaks()
        
    def show_banner(self):
        """Exibe o banner da aplicação"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                        {Fore.YELLOW}iOptimizer v3.0{Fore.CYAN}                        ║
║                  {Fore.GREEN}Otimizador de Sistema Windows{Fore.CYAN}                 ║
║                                                              ║
║  {Fore.WHITE}Desenvolvido para melhorar a performance do seu PC by @dev-isaacmello{Fore.CYAN}        ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    def show_system_info(self):
        """Exibe informações básicas do sistema"""
        print(f"\n{Fore.YELLOW}📊 Informações do Sistema:")
        print("=" * 50)
        
        info = self.monitor.get_system_info()
        for key, value in info.items():
            print(f"{Fore.CYAN}{key}: {Fore.WHITE}{value}")
    
    def show_menu(self):
        """Exibe o menu principal"""
        print(f"\n{Fore.GREEN}🔧 Menu Principal:")
        print("=" * 30)
        print(f"{Fore.CYAN}1. {Fore.WHITE}Monitorar Sistema")
        print(f"{Fore.CYAN}2. {Fore.WHITE}Limpeza de Sistema")
        print(f"{Fore.CYAN}3. {Fore.WHITE}Gerenciar Processos")
        print(f"{Fore.CYAN}4. {Fore.WHITE}Gerenciar Inicialização")
        print(f"{Fore.CYAN}5. {Fore.WHITE}Aplicar Tweaks de Performance")
        print(f"{Fore.CYAN}6. {Fore.WHITE}Otimização Completa")
        print(f"{Fore.CYAN}7. {Fore.WHITE}Sair")
        print("=" * 30)
    
    def monitor_system(self):
        """Monitora o sistema em tempo real"""
        print(f"\n{Fore.YELLOW}📈 Monitor do Sistema")
        print("Pressione Ctrl+C para voltar ao menu")
        print("-" * 40)
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                self.show_banner()
                
                stats = self.monitor.get_real_time_stats()
                
                print(f"{Fore.CYAN}CPU: {Fore.GREEN if stats['cpu'] < 70 else Fore.RED}{stats['cpu']:.1f}%")
                print(f"{Fore.CYAN}RAM: {Fore.GREEN if stats['memory'] < 80 else Fore.RED}{stats['memory']:.1f}%")
                print(f"{Fore.CYAN}Disco: {Fore.GREEN if stats['disk'] < 90 else Fore.RED}{stats['disk']:.1f}%")
                
                if 'temperature' in stats:
                    temp_color = Fore.GREEN if stats['temperature'] < 70 else Fore.YELLOW if stats['temperature'] < 85 else Fore.RED
                    print(f"{Fore.CYAN}Temperatura: {temp_color}{stats['temperature']:.1f}°C")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Voltando ao menu principal...")
            time.sleep(1)
    
    def clean_system(self):
        """Executa limpeza do sistema"""
        print(f"\n{Fore.YELLOW}🧹 Limpeza do Sistema")
        print("-" * 30)
        
        if not is_admin():
            print(f"{Fore.RED}⚠️  Privilégios de administrador necessários para algumas operações.")
            if input(f"{Fore.CYAN}Continuar mesmo assim? (s/n): ").lower() != 's':
                return
        
        print(f"{Fore.CYAN}Iniciando limpeza...")
        results = self.cleaner.full_cleanup()
        
        print(f"\n{Fore.GREEN}✅ Limpeza concluída!")
        for category, size in results.items():
            print(f"{Fore.CYAN}{category}: {Fore.WHITE}{size}")
    
    def manage_processes(self):
        """Gerencia processos do sistema"""
        print(f"\n{Fore.YELLOW}⚙️  Gerenciamento de Processos")
        print("-" * 35)
        
        processes = self.process_mgr.get_resource_heavy_processes()
        
        if not processes:
            print(f"{Fore.GREEN}Nenhum processo pesado detectado.")
            return
        
        print(f"{Fore.CYAN}Processos com alto uso de recursos:")
        for i, proc in enumerate(processes[:10], 1):
            print(f"{Fore.WHITE}{i}. {proc['name']} - CPU: {proc['cpu']:.1f}% RAM: {proc['memory']:.1f}%")
        
        choice = input(f"\n{Fore.CYAN}Digite o número do processo para encerrar (0 para voltar): ")
        if choice.isdigit() and 1 <= int(choice) <= len(processes):
            proc = processes[int(choice) - 1]
            if self.process_mgr.kill_process(proc['pid']):
                print(f"{Fore.GREEN}✅ Processo {proc['name']} encerrado com sucesso.")
            else:
                print(f"{Fore.RED}❌ Erro ao encerrar o processo.")
    
    def manage_startup(self):
        """Gerencia programas de inicialização"""
        print(f"\n{Fore.YELLOW}🚀 Gerenciamento de Inicialização")
        print("-" * 40)
        
        if not is_admin():
            print(f"{Fore.RED}⚠️  Privilégios de administrador necessários.")
            return
        
        startup_items = self.startup_mgr.get_startup_programs()
        
        if not startup_items:
            print(f"{Fore.GREEN}Nenhum programa de inicialização encontrado.")
            return
        
        print(f"{Fore.CYAN}Programas na inicialização:")
        for i, item in enumerate(startup_items, 1):
            status = "✅ Ativo" if item['enabled'] else "❌ Desabilitado"
            print(f"{Fore.WHITE}{i}. {item['name']} - {status}")
        
        # lógica para habilitar/desabilitar
        pass
        
    
    def apply_tweaks(self):
        """Aplica tweaks de performance"""
        print(f"\n{Fore.YELLOW}⚡ Tweaks de Performance")
        print("-" * 30)
        
        if not is_admin():
            print(f"{Fore.RED}⚠️  Privilégios de administrador necessários.")
            return
        
        print(f"{Fore.CYAN}Aplicando tweaks de performance...")
        results = self.tweaks.apply_performance_tweaks()
        
        for tweak, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {tweak}")
    
    def full_optimization(self):
        """Executa otimização completa"""
        print(f"\n{Fore.YELLOW}🔥 Otimização Completa")
        print("-" * 25)
        
        if not is_admin():
            print(f"{Fore.RED}⚠️  Privilégios de administrador recomendados.")
            if input(f"{Fore.CYAN}Continuar? (s/n): ").lower() != 's':
                return
        
        print(f"{Fore.CYAN}Iniciando otimização completa...")
        
        print(f"{Fore.YELLOW}1/3 Limpeza do sistema...")
        self.cleaner.full_cleanup()
        
        print(f"{Fore.YELLOW}2/3 Aplicando tweaks...")
        self.tweaks.apply_performance_tweaks()
        
        print(f"{Fore.YELLOW}3/3 Finalizando...")
        time.sleep(2)
        
        print(f"{Fore.GREEN}🎉 Otimização completa finalizada!")
    
    def run(self):
        """Executa a aplicação principal"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.show_banner()
        
        if os.name != 'nt':
            print(f"{Fore.RED}❌ Esta aplicação foi projetada para Windows.")
            sys.exit(1)
        
        self.show_system_info()
        
        while True:
            self.show_menu()
            
            try:
                choice = input(f"\n{Fore.CYAN}Escolha uma opção (1-7): {Fore.WHITE}")
                
                if choice == '1':
                    self.monitor_system()
                elif choice == '2':
                    self.clean_system()
                elif choice == '3':
                    self.manage_processes()
                elif choice == '4':
                    self.manage_startup()
                elif choice == '5':
                    self.apply_tweaks()
                elif choice == '6':
                    self.full_optimization()
                elif choice == '7':
                    print(f"{Fore.YELLOW}👋 Obrigado por usar o iOptimizer!")
                    break
                else:
                    print(f"{Fore.RED}❌ Opção inválida. Tente novamente.")
                
                if choice in ['2', '3', '4', '5', '6']:
                    input(f"\n{Fore.CYAN}Pressione Enter para continuar...")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 Saindo do iOptimizer...")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Erro: {e}")
                input(f"{Fore.CYAN}Pressione Enter para continuar...")

if __name__ == "__main__":
    app = iOptimizer()
    app.run()