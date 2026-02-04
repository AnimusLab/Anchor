"""
BAD EXAMPLE: Autonomous Trading Agent (Violates FINOS Risks)

This code demonstrates INSECURE patterns that anchor-audit will block.
It violates RI-24, AI-20, and RI-12 from the FINOS AI Governance Framework.
"""

import requests  # ❌ VIOLATION: RI-24 (Raw Network Access)
import threading  # ❌ VIOLATION: RI-12 (Direct Threading)
from openai import OpenAI


class TradingAgent:
    """
    INSECURE: This agent has multiple security vulnerabilities.
    """
    
    def __init__(self):
        self.client = OpenAI()
    
    def fetch_market_data(self, symbol: str):
        """
        ❌ VIOLATION: RI-24
        Direct network access bypasses security controls.
        """
        url = f"https://api.marketdata.com/quote/{symbol}"
        response = requests.get(url)  # ← BLOCKED by anchor-audit
        return response.json()
    
    def generate_strategy(self, market_data: dict):
        """
        ❌ VIOLATION: AI-20
        Dynamic execution of LLM output is forbidden.
        """
        prompt = f"Generate Python code to trade based on: {market_data}"
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        strategy_code = response.choices[0].message.content
        exec(strategy_code)  # ← BLOCKED by anchor-audit (AI-20)
    
    def execute_parallel_trades(self, trades: list):
        """
        ❌ VIOLATION: RI-12
        Direct thread spawning bypasses isolation.
        """
        for trade in trades:
            worker = threading.Thread(target=self._execute_trade, args=(trade,))
            worker.start()  # ← BLOCKED by anchor-audit (RI-12)
    
    def _execute_trade(self, trade):
        print(f"Executing: {trade}")


if __name__ == "__main__":
    agent = TradingAgent()
    
    # This code will be BLOCKED by anchor-audit when run with:
    # anchor check --context examples/threat_model.md --dir examples/
    
    data = agent.fetch_market_data("AAPL")
    agent.generate_strategy(data)
    agent.execute_parallel_trades([{"symbol": "AAPL", "qty": 100}])
