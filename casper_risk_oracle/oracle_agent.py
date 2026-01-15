
import time
import random
import sys
import subprocess
import json
import os
import re

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
        
        log(f"\n{BLUE}📊 ANALYSIS: {validator_id} ({profile['type']}){RESET}")
        log(f"   ├── Concentration Risk: {c*100}%")
        log(f"   ├── Volatility Risk:    {v*100}%")
        log(f"   └── Unstake Pressure:   {u*100}%")
        
        if final_score > 50:
             log(f"   {RED}⚠️  RISK FACTOR DETECTED: {final_score}/100{RESET}")
        else:
             log(f"   {GREEN}✅ SYSTEM SAFE: {final_score}/100{RESET}")
        
        return final_score

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
            f.write("--- AGENT STARTED ---\n")
    except:
        pass

    engine = RiskEngine()
    validators = list(VALIDATOR_DATA.keys())
    
    log(f"{GREEN}🤖 Casper Risk Oracle v1.0 [DIRECTOR MODE ACTIVE]{RESET}")
    log("Waiting for block...")

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
                        log(f"{RED}⚠️  MANUAL OVERRIDE DETECTED: Pushing {score}{RESET}")
        except Exception:
            pass # Fail silently to auto mode
            
        if not override_active:
             target = random.choice(validators)
             score = engine.compute_risk(target)

        push_on_chain(target, score)
        
        # --- DEMO BRIDGE ---
        # Write to frontend public folder for instant updates
        try:
            demo_data = {
                "validator": target,
                "score": score,
                "timestamp": int(time.time())
            }
            # Adjust path as needed based on where you run the agent
            # Assuming agent is in casper_risk_oracle and dashboard is sibling
            json_path = "../risk-dashboard/public/risk_status.json"
            with open(json_path, "w") as f:
                json.dump(demo_data, f)
            log(f"   {BLUE}📺 DEMO BRIDGE: Updated frontend data -> {score}{RESET}")
        except Exception as e:
            log(f"   {RED}❌ DEMO BRIDGE FAILED: {e}{RESET}")
        
        # Faster loop for demo purposes (30s)
        time.sleep(30)

if __name__ == "__main__":
    run_oracle()
