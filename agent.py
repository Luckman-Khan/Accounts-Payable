from typing import TypedDict, Literal, Annotated ,List
import operator
from langgraph.graph import StateGraph, END
from extractor import extract_invoice_from_text, InvoiceData
from validator import validate_invoice, ValidationResult


class AgentState(TypedDict):
    invoice_text: str         
    extracted_data: InvoiceData | None 
    validation_result: ValidationResult | None
    final_decision: str       
    retry_count: int
    analysis_notes: List[str]  



def extract_node(state: AgentState):
    """Worker 1: Reads the invoice (Single Attempt)."""
    print(f"🤖 Agent: Reading invoice...")
    try:
        data = extract_invoice_from_text(state["invoice_text"])
        return {"extracted_data": data}
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return {"extracted_data": None}

def validate_node(state: AgentState):
    """Worker 2: Checks the database."""
    print("🕵️ Agent: Checking database rules...")
    data = state.get("extracted_data")
    
    if not data:
        return {
            "validation_result": None, 
            "analysis_notes": ["Extraction Failed"]
        }

    result = validate_invoice(data)
    return {
        "validation_result": result,
        "analysis_notes": result.errors if not result.is_valid else []
    }

def decision_node(state: AgentState):
    """Worker 3: Final Decision."""
    result = state.get("validation_result")
    
    if result is None:
        print("❌ Agent: Fatal Extraction Error.")
        return {"final_decision": "REJECTED"} 
    
    if result.is_valid:
        if any("High Value" in e for e in result.errors):
            print("⚖️ Agent: Invoice valid but exceeds auto-pay limit. FLAGGING.")
            return {"final_decision": "FLAG"}
        
        print("✅ Agent: Invoice APPROVED.")
        return {"final_decision": "PAY"}
    
    else:
        print(f"❌ Agent: Invoice REJECTED. Reasons: {result.errors}")
        return {"final_decision": "REJECTED"}


workflow = StateGraph(AgentState)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
workflow.add_node("decide", decision_node)


workflow.set_entry_point("extract")
workflow.add_edge("extract", "validate")
workflow.add_edge("validate", "decide")
workflow.add_edge("decide", END)

app = workflow.compile()

if __name__ == "__main__":
    test_invoice_text = """
    INVOICE #9921
    From: TechSupplies Ltd
    Total: $5000.00
    PO Ref: PO-001
    """

    print("🚀 Starting Robust AI Agent...")
    result = app.invoke({"invoice_text": test_invoice_text, "retry_count": 0})
    
    print(f"\nFinal Decision: {result['final_decision']}")