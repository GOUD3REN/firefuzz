# firefuzz
FIREFUZZ: Advanced Subdomain Reconnaissance Tool


# basic mode
python3 firefuzz.py -d target.com -w wordlist.txt

# complete scan w httpx
python3 firefuzz.py -d target.com -w wordlist.txt --run-httpx -t 50

# silent mode 
TERM=dumb python3 firefuzz.py -d target.com -w wordlist.txt



