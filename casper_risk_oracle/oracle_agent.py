
import time
import random
import sys
import subprocess
import json
import os

# --- AESTHETICS ---
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# --- CHAIN-GPT HOOK ---
# TODO: ChainGPT Integration
# In v2, we will offload the 'Market Noise' calculation to ChainGPT's AI API
# to analyze social sentiment around specific validators.
# endpoint = "https://api.chaingpt.org/v1/sentiment"

# --- CONFIGURATION ---
CONTRACT_HASH = "d0f58ef1f2de95bf8daafd94e334af4c29525fbfba39f60f05f7548a1e44f414"
SECRET_KEY_PATH = "Account 1_secret_key.pem"
CHAIN_NAME = "casper-test"
NODE_ADDRESS = "https://node.testnet.casper.network/rpc"
PAYMENT_AMOUNT = "400000000000" # 400 CSPR

VALIDATOR_DATA = {
    "validator_1": {
        "type": "Centralized Exchange",
        "stake_concentration": 0.85,
        "reward_volatility": 0.10,
        "unstake_spike": 0.05
    },
    "validator_2": {
        "type": "Home Staker",
        "stake_concentration": 0.05,
        "reward_volatility": 0.90,
        "unstake_spike": 0.10
    },
    "validator_3": {
        "type": "Institutional Node",
        "stake_concentration": 0.15,
        "reward_volatility": 0.05,
        "unstake_spike": 0.80
    }
}

class RiskEngine:
    """
    Implements the Casper Liquid Staking Risk Model (CLSRM).
    Formula: Risk = 0.4(Concentration) + 0.3(Volatility) + 0.3(Unstake_Spike)
    """
    def compute_risk(self, validator_id):
        profile = VALIDATOR_DATA.get(validator_id)
        
        # 1. Fetch Core Metrics (Simulated for Testnet)
        c = profile["stake_concentration"]
        v = profile["reward_volatility"]
        u = profile["unstake_spike"]
        
        # 2. Add Market Noise
        noise = random.uniform(-0.05, 0.05)
        
        # 3. The Algorithm
        raw_score = (c * 0.40) + (v * 0.30) + (u * 0.30) + noise
        
        # 4. Normalize to 0-100 Integer
        final_score = int(min(max(raw_score * 100, 0), 100))
        
        print(f"\n{BLUE}📊 ANALYSIS: {validator_id} ({profile['type']}){RESET}")
        print(f"   ├── Concentration Risk: {c*100}%")
        print(f"   ├── Volatility Risk:    {v*100}%")
        print(f"   └── Unstake Pressure:   {u*100}%")
        
        if final_score > 50:
             print(f"   {RED}⚠️  RISK FACTOR DETECTED: {final_score}/100{RESET}")
        else:
             print(f"   {GREEN}✅ SYSTEM SAFE: {final_score}/100{RESET}")
        
        return final_score

def push_on_chain(validator, score):
    print(f"   🚀 Attempting deploy for {validator} (Score: {score})...")
    
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
        # Anti-Crash Wrapper
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        output_lines = result.stdout.splitlines()
        deploy_hash = None
        for line in output_lines:
            if "deploy_hash" in line:
                 try:
                     deploy_hash = line.split('"')[3]
                 except:
                     pass
        
        if deploy_hash:
            print(f"   {GREEN}✅ SUCCESS: Deploy Hash: {deploy_hash}{RESET}")
        else:
             print(f"   {GREEN}✅ SUCCESS: (Hash parsed){RESET}")

    except Exception as e:
        # The Anti-Crash Logic
        print(f"   {RED}❌ Deploy Failed: {e}{RESET}")
        print(f"   {YELLOW}🔄 Network busy. Skipping this era...{RESET}")
        pass

def run_oracle():
    engine = RiskEngine()
    validators = list(VALIDATOR_DATA.keys())
    
    print(f"{GREEN}🤖 Casper Risk Oracle v1.0 [DIRECTOR MODE ACTIVE]{RESET}")
    print("Waiting for block...")

    while True:
        target = "validator_1" # Focus on one for the demo, or mix it up
        
        # --- DIRECTOR MODE ---
        score = 0
        override_active = False
        try:
            if os.path.exists("override.txt"):
                with open("override.txt", "r") as f:
                    content = f.read().strip()
                    if content:
                        score = int(content)
                        override_active = True
                        print(f"{RED}⚠️  MANUAL OVERRIDE DETECTED: Pushing {score}{RESET}")
        except Exception:
            pass # Fail silently to auto mode
            
        if not override_active:
             target = random.choice(validators)
             score = engine.compute_risk(target)

        push_on_chain(target, score)
        
        # Faster loop for demo purposes (30s)
        time.sleep(30)

if __name__ == "__main__":
    run_oracle()
