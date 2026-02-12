from typing import TypedDict, Literal, Annotated
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



def extract_node(state: AgentState):
    """Worker 1: Reads the invoice."""
    print(f"🤖 Agent: Reading invoice (Attempt {state.get('retry_count', 0) + 1})...")
    data = extract_invoice_from_text(state["invoice_text"])
    return {"extracted_data": data}

def validate_node(state: AgentState):
    """Worker 2: Checks the database."""
    print("🕵️ Agent: Checking database rules...")
    data = state["extracted_data"]
    
    if not data:
        return {"validation_result": None}

    result = validate_invoice(data)
    return {"validation_result": result}

def reflection_node(state: AgentState):
    """
    Worker 3 (Reflector): Increments the retry counter.
    In a more advanced app, this would also modify the 'prompt' to give a hint.
    """
    current_count = state.get("retry_count", 0)
    errors = state["validation_result"].errors if state["validation_result"] else ["Extraction Failed"]
    
    print(f"🤔 Agent: Validation failed with {errors}. Retrying...")
    return {"retry_count": current_count + 1}

def decision_node(state: AgentState):
    """Worker 4: Final Decision."""
    result = state.get("validation_result")
    
    if result is None:
        print("❌ Agent: Fatal Extraction Error.")
        return {"final_decision": "DENY"}
    
    if result.is_valid:
        print("✅ Agent: Invoice APPROVED.")
        return {"final_decision": "PAY"}
    else:
        print(f"❌ Agent: Invoice REJECTED. Reasons: {result.errors}")
        return {"final_decision": "DENY"}


def should_retry(state: AgentState):
    result = state.get("validation_result")
    count = state.get("retry_count", 0)

    
    if result and result.is_valid:
        return "decide"  
   
    if count < 2:
        return "reflect"
    
    return "decide"


workflow = StateGraph(AgentState)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
workflow.add_node("reflect", reflection_node)
workflow.add_node("decide", decision_node)


workflow.set_entry_point("extract")
workflow.add_edge("extract", "validate")


workflow.add_conditional_edges(
    "validate",
    should_retry,
    {
        "decide": "decide",
        "reflect": "reflect" 
    }
)


workflow.add_edge("reflect", "extract")
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