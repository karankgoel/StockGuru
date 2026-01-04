import os
import sys
from agent.orchestrator import AdvisorAgent

def main():
    print("Welcome to the Multi-Agent Stock Advisor!")
    print("Type 'exit' to quit.")
    
    # Check for API key
    if "GOOGLE_API_KEY" not in os.environ:
        print("Please set the GOOGLE_API_KEY environment variable.")
    
    agent = AdvisorAgent()
    
    while True:

        try:
            user_input = input("\nEnter a stock symbol or query: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            response = agent.run(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
