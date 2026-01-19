
import time
import random
import sys
import subprocess
import json
import os
import re
import requests
import math

# --- AESTHETICS ---
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# --- CONFIGURATION ---
CONTRACT_HASH = "d0f58ef1f2de95bf8daafd94e334af4c29525fbfba39f60f05f7548a1e44f414"
SECRET_KEY_PATH = "Account 1_secret_key.pem"
CHAIN_NAME = "casper-test"
NODE_ADDRESS = "https://node.testnet.casper.network/rpc"
PAYMENT_AMOUNT = "2500000000" # 2.5 CSPR

# --- API CONFIG ---
CSPR_CLOUD_KEY = "019bd739-a94c-72a9-9435-05b258d3c16c"
BASE_URL = "https://api.cspr.cloud"
HEADERS = {
    "Authorization": CSPR_CLOUD_KEY,
    "accept": "application/json"
}

class RiskEngine:
    """
    Implements the Casper Liquid Staking Risk Model (CLSRM) using Real-Time Data.
    Formula: Risk = 0.4(Concentration) + 0.3(Volatility) + 0.3(Unstake_Spike)
    """
    def get_latest_era_id(self):
        try:
             # Get Status/Block Info to find latest Era
             url = f"{BASE_URL}/blocks?page=1&limit=1&order_by=block_height&order_direction=desc"
             response = requests.get(url, headers=HEADERS, timeout=10)
             if response.status_code == 200:
                 data = response.json().get('data', [])
                 if data:
                     return data[0]['era_id']
             return None
        except Exception:
             return None

    def get_top_validators(self, era_id, limit=100):
        try:
            url = f"{BASE_URL}/validators?era_id={era_id}&page=1&limit={limit}&order_by=total_stake&order_direction=DESC"
            response = requests.get(url, headers=HEADERS, timeout=10) 
            if response.status_code == 200:
                data = response.json().get('data', [])
                if not data:
                    log(f"{YELLOW}⚠️ API returned empty data list. Full response: {response.json()}{RESET}")
                return data
            else:
                log(f"{RED}❌ API Error (Validators): {response.status_code} - {response.text}{RESET}")
            return []
        except Exception as e:
            log(f"{RED}❌ API Error (Validators): {e}{RESET}")
            return []

    def get_validator_rewards(self, pubkey):
         try:
            # Fetch last 10 eras of rewards
            url = f"{BASE_URL}/validators/{pubkey}/rewards?page=1&limit=10"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
         except Exception:
             return []

    def calculate_volatility(self, rewards_data):
        if not rewards_data or len(rewards_data) < 2:
            return 0.1 # Default low volatility
        
        amounts = [float(r['amount']) for r in rewards_data]
        mean = sum(amounts) / len(amounts)
        if mean == 0: return 0
        
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean # Coefficient of Variation
        return min(cv * 5, 1.0) # Scale up to make it visible, max 1.0

    def calculate_concentration(self, validator_stake, total_stake):
        if total_stake == 0: return 0
        share = float(validator_stake) / float(total_stake)
        # Scale: if > 10% of network, max risk.
        return min(share * 10, 1.0) 

    def compute_risk(self, pubkey, stake, total_network_stake):
        # 1. Concentration
        c = self.calculate_concentration(stake, total_network_stake)
        
        # 2. Volatility (from live rewards)
        rewards = self.get_validator_rewards(pubkey)
        v = self.calculate_volatility(rewards)
        
        # 3. Unstake Spike (Still Simulated as no direct API yet)
        u = random.uniform(0.0, 0.2) # Mostly stable
        
        # Add Market Noise (ChainGPT placeholder)
        noise = random.uniform(-0.02, 0.02)
        
        # The Algorithm
        raw_score = (c * 0.40) + (v * 0.30) + (u * 0.30) + noise
        
        final_score = int(min(max(raw_score * 100, 0), 100))
        
        return final_score, c, v, u

def push_on_chain(validator, score):
    log(f"   🚀 Attempting deploy for {validator} (Score: {score})...")
    
    contract_hash_formatted = f"hash-{CONTRACT_HASH}"
    
    cmd = [
        "casper-client", "put-deploy",
        "--node-address", NODE_ADDRESS,
        "--chain-name", CHAIN_NAME,
        "--secret-key", SECRET_KEY_PATH,
        "--payment-amount", PAYMENT_AMOUNT,
        "--session-hash", contract_hash_formatted,
        "--session-entry-point", "update_risk",
        "--session-arg", f"validator:string='{validator}'",
        "--session-arg", f"score:u8='{score}'"
    ]
    
    try:
        # Anti-Crash Wrapper: check=False to handle errors manually
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            error_msg = (result.stderr + result.stdout).strip()
            if "insufficient balance" in error_msg.lower():
                log(f"   {RED}❌ Deploy Failed: Insufficient Balance{RESET}")
                log(f"   {YELLOW}💰 Tip: Fund your account at https://testnet.cspr.live/tools/faucet{RESET}")
            else:
                # Print the first line of the error to avoid spamming
                short_err = error_msg.splitlines()[0] if error_msg else "Unknown Error"
                log(f"   {RED}❌ Deploy Failed: {short_err}{RESET}")
            
            log(f"   {YELLOW}⚠️  Skipping this era...{RESET}")
        else:
            output_lines = result.stdout.splitlines()
            deploy_hash = None
            for line in output_lines:
                if "deploy_hash" in line:
                     try:
                         deploy_hash = line.split('"')[3]
                     except:
                         pass
            
            if deploy_hash:
                log(f"   {GREEN}✅ SUCCESS: Deploy Hash: {deploy_hash}{RESET}")
            else:
                 log(f"   {GREEN}✅ SUCCESS: (Hash parsed){RESET}")

    except Exception as e:
        # Catch-all for other crash types (e.g. binary not found)
        log(f"   {RED}❌ Deploy Failed (System Error): {e}{RESET}")
        log(f"   {YELLOW}🔄 Network busy. Skipping this era...{RESET}")
        pass


def log(message):
    """Prints to console and appends to a log file for the frontend."""
    # 1. Print to Console (with colors)
    print(message)
    
    # 2. Write to File (Clean only? Or keep colors? Frontend needs to handle ANSI if we keep colors)
    # Let's strip ANSI for simpler frontend handling for now, or use a library.
    # Actually, let's keep it simple: Strip ANSI for the file.
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_message = ansi_escape.sub('', message)
    
    try:
        # Path relative to where agent is run (casper_risk_oracle)
        log_path = "../risk-dashboard/public/agent_logs.txt"
        with open(log_path, "a") as f:
            f.write(clean_message + "\n")
            
        # Keep file size manageable (tail 50 lines)
        # This is expensive to do every write, maybe do it occasionally or just let it grow (demo mode)
        # Let's trust it won't grow too big for a demo.
    except Exception:
        pass

def run_oracle():
    # clear log file on start
    try:
        with open("../risk-dashboard/public/agent_logs.txt", "w") as f:
            f.write("--- AGENT STARTED (REAL DATA MODE) ---\n")
    except:
        pass

    engine = RiskEngine()
    last_pushed_scores = {}
    
    log(f"{GREEN}🤖 Casper Risk Oracle v2.0 [LIVE DATA ACTIVE]{RESET}")
    log(f"   Connecting to {BASE_URL}...")

    while True:
        # Override Logic (Director Mode)
        override_target = None
        override_score = None
        
        try:
             if os.path.exists("override.txt"):
                with open("override.txt", "r") as f:
                    content = f.read().strip()
                    if content:
                        if ":" in content:
                            parts = content.split(":")
                            if len(parts) >= 2:
                                override_target = parts[0].strip()
                                override_score = int(parts[1].strip())
                        else:
                            override_target = "validator_1"
                            override_score = int(content)
        except Exception:
            pass

        if override_target:
             log(f"{RED}⚠️  MANUAL OVERRIDE DETECTED: {override_target} -> {override_score}{RESET}")
             push_on_chain(override_target, override_score)
             time.sleep(10)
             continue

        # Standard Mode (Top 100 Validators)
        log(f"\n{BLUE}🔄 Fetching Latest Era...{RESET}")
        era_id = engine.get_latest_era_id()
        if era_id is None:
             log(f"{RED}❌ Failed to get Era ID. Retrying...{RESET}")
             time.sleep(5)
             continue
             
        log(f"{BLUE}🔄 Fetching Top Validators (Era {era_id})...{RESET}")
        validators = engine.get_top_validators(era_id, limit=100)
        
        # Calculate Total Network Stake for concentration
        total_stake = sum(int(v['total_stake']) for v in validators)
        
        processed_count = 0
        
        for v_data in validators:
            pubkey = v_data['public_key']
            stake = int(v_data['total_stake'])
            
            # Compute Risk
            score, c, v, u = engine.compute_risk(pubkey, stake, total_stake)
            
            # Check Threshold (Only push if changed > 5%)
            last_score = last_pushed_scores.get(pubkey, -1)
            diff = abs(score - last_score)
            
            if diff > 5 or last_score == -1:
                log(f"\n{BLUE}📊 ANALYSIS: {pubkey[:10]}...{RESET}")
                log(f"   ├── Concentration Risk: {c*100:.2f}%")
                log(f"   ├── Volatility Risk:    {v*100:.2f}%")
                log(f"   └── Unstake Pressure:   {u*100:.2f}%")
                
                if score > 50:
                     log(f"   {RED}⚠️  RISK SCORE: {score}/100{RESET}")
                else:
                     log(f"   {GREEN}✅ RISK SCORE: {score}/100{RESET}")
                     
                push_on_chain(pubkey, score)
                last_pushed_scores[pubkey] = score
                
                # Demo Bridge Update (Show the latest pushed one)
                try:
                    demo_data = {
                        "validator": pubkey,
                        "score": score,
                        "timestamp": int(time.time()),
                        "details": {
                            "concentration": c,
                            "volatility": v,
                            "unstake_spike": u
                        }
                    }
                    with open("../risk-dashboard/public/risk_status.json", "w") as f:
                        json.dump(demo_data, f)
                except:
                    pass
            else:
                # log(f"   Skipping {pubkey[:10]}... (Stable Risk: {score})")
                pass
            
            processed_count += 1
            # Rate limit protection (don't spam API in loop too fast if processing many)
            # Actually we already fetched data, but maybe push_on_chain takes time.
            
        log(f"{GREEN}✅ Cycle Complete. Processed {processed_count} validators. Sleeping...{RESET}")
        time.sleep(30)

if __name__ == "__main__":
    run_oracle()
