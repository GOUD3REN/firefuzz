import requests
import argparse
import socket
import random
import concurrent.futures
import subprocess
import os
import json
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

# Configurações globais
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1"
]

COMMON_PORTS = [80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 9000]
PROTOCOLS = ['http', 'https']

# Cores para terminal (ANSI escape codes)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_firefuzz_logo():
    """Exibe o logo FIREFUZZ em estilo hacker"""
    logo = f"""
{Colors.RED}{Colors.BOLD}
███████╗██╗██████╗ ███████╗███████╗██╗   ██╗███████╗███████╗
██╔════╝██║██╔══██╗██╔════╝╚══███╔╝██║   ██║╚══███╔╝╚══███╔╝
█████╗  ██║██████╔╝█████╗    ███╔╝ ██║   ██║  ███╔╝   ███╔╝ 
██╔══╝  ██║██╔══██╗██╔══╝   ███╔╝  ██║   ██║ ███╔╝   ███╔╝  
██║     ██║██║  ██║███████╗███████╗╚██████╔╝███████╗███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝
{Colors.END}
{Colors.YELLOW}>> Bug Bounty Recon Tool v3.0 <<{Colors.END}
{Colors.CYAN}>> Subdomain Scanner + HTTPX Integration <<{Colors.END}
{Colors.MAGENTA}>> github.com/firefuzz <<{Colors.END}
"""
    print(logo)

def get_random_agent():
    return random.choice(USER_AGENTS)

def detect_wildcard(domain):
    """Detecta e retorna IPs de wildcard DNS"""
    wildcard_ips = set()
    print(f"{Colors.YELLOW}[*] Verificando wildcard DNS...{Colors.END}")
    for _ in range(3):
        random_sub = f"{random.randint(100000000,999999999)}.{domain}"
        try:
            ip = socket.gethostbyname(random_sub)
            wildcard_ips.add(ip)
            print(f"{Colors.RED}[!] Wildcard DNS detectado: *.{domain} -> {ip}{Colors.END}")
        except:
            pass
    return list(wildcard_ips)

def check_port(host, port):
    """Verifica se uma porta está aberta rapidamente"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex((host, port)) == 0
    except:
        return False

def scan_target(subdomain, domain, ports, wildcard_ips):
    """Escaneia um subdomínio em múltiplas portas e protocolos"""
    full_domain = f"{subdomain}.{domain}"
    
    try:
        # Resolução DNS para filtrar wildcards
        ip = socket.gethostbyname(full_domain)
        if wildcard_ips and ip in wildcard_ips:
            return []
    except:
        return []

    results = []
    
    for port in ports:
        if not check_port(full_domain, port):
            continue
            
        for protocol in PROTOCOLS:
            # Pular combinações redundantes
            if (protocol == 'http' and port == 443) or (protocol == 'https' and port == 80):
                continue
                
            url = f"{protocol}://{full_domain}:{port}"
            headers = {'User-Agent': get_random_agent()}
            
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=3,
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code < 500:
                    result = {
                        'url': url,
                        'status': response.status_code,
                        'ip': ip,
                        'port': port,
                        'content_length': len(response.content),
                        'headers': dict(response.headers)
                    }
                    results.append(result)
            except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
                pass
            except Exception as e:
                pass

    return results

def run_httpx(urls_file, output_file):
    """Executa httpx para verificar URLs ativas com mais precisão"""
    if not os.path.exists(urls_file):
        print(f"{Colors.RED}[-] Arquivo de URLs não encontrado: {urls_file}{Colors.END}")
        return []

    try:
        print(f"{Colors.CYAN}[*] Executando httpx para verificação avançada...{Colors.END}")
        cmd = [
            'httpx',
            '-l', urls_file,
            '-title', '-tech-detect', '-status-code', '-content-length',
            '-json', '-o', output_file,
            '-timeout', '3', '-retries', '1', '-rate-limit', '100'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode != 0:
            print(f"{Colors.RED}[-] httpx error: {result.stderr}{Colors.END}")
            return []
        
        # Ler e retornar resultados do httpx
        if os.path.exists(output_file):
            with open(output_file) as f:
                httpx_results = [json.loads(line) for line in f.readlines()]
                print(f"{Colors.GREEN}[+] httpx encontrou {len(httpx_results)} URLs ativas{Colors.END}")
                return httpx_results
        return []
            
    except FileNotFoundError:
        print(f"{Colors.RED}[-] httpx não encontrado. Instale com:{Colors.END}")
        print("go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest")
    except Exception as e:
        print(f"{Colors.RED}[-] Erro ao executar httpx: {str(e)}{Colors.END}")
    
    return []

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Exibe uma barra de progresso visual"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()

def main():
    print_firefuzz_logo()
    
    parser = argparse.ArgumentParser(description='Advanced Subdomain Scanner com httpx',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--domain', required=True, help='Domínio alvo')
    parser.add_argument('-w', '--wordlist', required=True, help='Arquivo de wordlist')
    parser.add_argument('-o', '--output', default='firefuzz_scan', help='Prefixo de saída')
    parser.add_argument('-t', '--threads', type=int, default=30, help='Número de threads')
    parser.add_argument('-p', '--ports', nargs='+', type=int, default=COMMON_PORTS,
                        help=f'Portas para escanear (padrão: {COMMON_PORTS})')
    parser.add_argument('--run-httpx', action='store_true', help='Executar httpx nas URLs encontradas')
    parser.add_argument('--skip-http-check', action='store_true', help='Pular verificação HTTP inicial')
    
    args = parser.parse_args()

    # Configuração de arquivos
    output_json = f"{args.output}.json"
    output_txt = f"{args.output}.txt"
    urls_file = f"{args.output}_urls.txt"
    httpx_output = f"{args.output}_httpx.json"

    # Configuração inicial
    start_time = datetime.now()
    print(f"{Colors.BLUE}[*] Target: {Colors.BOLD}{args.domain}{Colors.END}")
    print(f"{Colors.BLUE}[*] Threads: {args.threads} | Portas: {args.ports}{Colors.END}")
    print(f"{Colors.BLUE}[*] Saída: {output_json} e {output_txt}{Colors.END}")
    
    # Detecção de wildcard
    wildcard_ips = detect_wildcard(args.domain)

    # Carregar wordlist
    try:
        with open(args.wordlist) as f:
            subdomains = [line.strip() for line in f if line.strip()]
            print(f"{Colors.GREEN}[+] Wordlist carregada: {len(subdomains)} subdomínios{Colors.END}")
    except FileNotFoundError:
        print(f"{Colors.RED}[-] Erro: Arquivo não encontrado - {args.wordlist}{Colors.END}")
        return

    # Iniciar arquivos de saída
    open(output_json, 'w').close()
    open(urls_file, 'w').close()

    # Execução paralela
    results = []
    active_urls = []
    print(f"{Colors.CYAN}[*] Iniciando escaneamento...{Colors.END}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(
            scan_target if not args.skip_http_check else lambda *args: [],
            sub,
            args.domain,
            args.ports,
            wildcard_ips
        ): sub for sub in subdomains}
        
        # Barra de progresso
        completed = 0
        total = len(subdomains)
        
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            sub = futures[future]
            
            try:
                sub_results = future.result()
                if sub_results:
                    results.extend(sub_results)
                    # Salvar URLs para httpx
                    with open(urls_file, 'a') as uf:
                        for res in sub_results:
                            uf.write(f"{res['url']}\n")
                            active_urls.append(res['url'])
            except Exception as e:
                pass
            
            print_progress_bar(completed, total, prefix='Progresso:', suffix=f'{completed}/{total} subdomínios')
    
    # Salvar resultados iniciais
    if results:
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=2)
        
        with open(output_txt, 'w') as f:
            for res in results:
                status_color = Colors.GREEN if res['status'] < 300 else Colors.YELLOW
                f.write(f"{res['url']} | Status: {res['status']} | IP: {res['ip']} | Porta: {res['port']}\n")
                print(f"{status_color}[+] {res['url']} {Colors.WHITE}| Status: {res['status']} | IP: {res['ip']} | Porta: {res['port']}{Colors.END}")

    # Executar httpx se solicitado
    httpx_results = []
    if args.run_httpx:
        httpx_results = run_httpx(urls_file, httpx_output)
        
        if httpx_results:
            # Adicionar resultados do httpx ao arquivo principal
            with open(output_txt, 'a') as f:
                f.write("\n=== RESULTADOS HTTPX ===\n")
                for res in httpx_results:
                    url = res.get('url', '')
                    status = res.get('status_code', '')
                    title = res.get('title', '')[:50]
                    tech = ','.join(res.get('technology', []))[:30]
                    f.write(f"{url} | Status: {status} | Título: {title} | Tech: {tech}\n")
                    
                    status_color = Colors.GREEN if status < 300 else Colors.YELLOW
                    print(f"{status_color}[HTTPX] {url} {Colors.WHITE}| Status: {status} | Título: {title} | Tech: {tech}{Colors.END}")

    # Relatório final
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n{Colors.GREEN}{Colors.BOLD}╔════════════════════════════════════════════╗")
    print(f"║           ESCANEAMENTO COMPLETO!          ║")
    print(f"╠════════════════════════════════════════════╣")
    print(f"║ Tempo decorrido: {duration}{' '*(26-len(str(duration)))}║")
    print(f"║ Subdomínios ativos: {len(results)}{' '*(25-len(str(len(results))))}║")
    print(f"║ URLs verificadas: {len(active_urls)}{' '*(26-len(str(len(active_urls))))}║")
    if args.run_httpx:
        print(f"║ Resultados do httpx: {len(httpx_results)}{' '*(23-len(str(len(httpx_results))))}║")
    print(f"║ Arquivos salvos:                          ║")
    print(f"║   • {output_txt}{' '*(36-len(output_txt))}║")
    print(f"║   • {output_json}{' '*(36-len(output_json))}║")
    if args.run_httpx:
        print(f"║   • {httpx_output}{' '*(36-len(httpx_output))}║")
    print(f"╚════════════════════════════════════════════╝{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}{Colors.BOLD}[!] Scan interrompido pelo usuário!{Colors.END}")
        sys.exit(1)
