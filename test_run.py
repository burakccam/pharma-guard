import sys
from agents import run_pharma_guard_analysis

def main():
    print("Testing Pharma-Guard AI with Groq...")
    results = run_pharma_guard_analysis(manual_drug_name="Parol", user_context="Yaş: 30")
    
    if results.get("status") == "ERROR" or results.get("status") == "BLOCKED":
        print("TEST FAILED")
        print("Status:", results.get("status"))
        print("Reason:", results.get("block_reason"))
    else:
        print("TEST PASSED")
        print("Status:", results.get("status"))
        print("Report length:", len(results.get("final_markdown_report", "")))
        print("\nExcerpt from AI Knowledge:\n", results.get("ai_knowledge")[:200])
        print("\nFinal Report excerpt:\n", results.get("final_markdown_report")[:200])

if __name__ == "__main__":
    main()
