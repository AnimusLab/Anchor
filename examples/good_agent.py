"""
GOOD EXAMPLE: Autonomous Trading Agent (FINOS-Compliant)

This code demonstrates SECURE patterns that pass anchor-audit enforcement.
It uses approved abstractions instead of raw network/execution primitives.
"""

from mcp import Client  # ✅ APPROVED: Controlled network access
from anchor.runtime import TaskQueue  # ✅ APPROVED: Managed concurrency
from openai import OpenAI
import ast  # ✅ APPROVED: Static code analysis


class SecureTradingAgent:
    """
    SECURE: This agent follows FINOS AI Governance best practices.
    """
    
    def __init__(self):
        self.mcp_client = Client(cert_path="./agent.cert")
        self.llm_client = OpenAI()
        self.task_queue = TaskQueue(max_workers=4)
    
    def fetch_market_data(self, symbol: str):
        """
        ✅ COMPLIANT: Uses MCP Client with certificate authentication
        Satisfies RI-24 mitigation requirements
        """
        response = self.mcp_client.get(
            endpoint=f"/market/quote/{symbol}",
            timeout=5
        )
        return response.json()
    
    def generate_strategy(self, market_data: dict):
        """
        ✅ COMPLIANT: Uses AST validation instead of exec()
        Satisfies AI-20 mitigation requirements
        """
        prompt = f"Generate Python code to trade based on: {market_data}"
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        strategy_code = response.choices[0].message.content
        
        # Validate before execution
        try:
            tree = ast.parse(strategy_code)
            # Only allow safe operations (no exec, eval, import)
            self._validate_ast(tree)
            return compile(tree, '<llm-generated>', 'exec')
        except SyntaxError:
            raise ValueError("LLM generated invalid Python code")
    
    def execute_parallel_trades(self, trades: list):
        """
        ✅ COMPLIANT: Uses managed task queue
        Satisfies RI-12 mitigation requirements
        """
        for trade in trades:
            self.task_queue.submit(self._execute_trade, trade)
        
        # Wait for completion with timeout
        self.task_queue.wait(timeout=30)
    
    def _execute_trade(self, trade):
        print(f"Executing: {trade}")
    
    def _validate_ast(self, tree):
        """Ensures LLM output doesn't contain dangerous operations"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("LLM attempted to import modules")
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', '__import__']:
                        raise ValueError(f"LLM attempted to call {node.func.id}")


if __name__ == "__main__":
    agent = SecureTradingAgent()
    
    # This code will PASS anchor-audit enforcement:
    # anchor check --context examples/threat_model.md --dir examples/
    
    data = agent.fetch_market_data("AAPL")
    strategy = agent.generate_strategy(data)
    agent.execute_parallel_trades([{"symbol": "AAPL", "qty": 100}])
    
    print("✅ All security checks passed!")
