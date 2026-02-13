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
# def reflection_node(state: AgentState):
#     """
#     Worker 3 (Reflector): Increments the retry counter.
#     In a more advanced app, this would also modify the 'prompt' to give a hint.
#     """
#     current_count = state.get("retry_count", )
#     errors = state["validation_result"].errors if state["validation_result"] else ["Extraction Failed"]
    
#     print(f"🤔 Agent: Validation failed with {errors}. Retrying...")
#     return {"retry_count": current_count + 1}

def decision_node(state: AgentState):
    """Worker 3: Final Decision."""
    result = state.get("validation_result")
    
    # Case 1: Extraction Failed completely
    if result is None:
        print("❌ Agent: Fatal Extraction Error.")
        return {"final_decision": "REJECTED"} 
    
    # Case 2: Validation Passed
    if result.is_valid:
        print("✅ Agent: Invoice APPROVED.")
        return {"final_decision": "PAY"}
    
    # Case 3: Validation Failed (Fraud, Anomaly, etc.)
    else:
        print(f"❌ Agent: Invoice REJECTED. Reasons: {result.errors}")
        return {"final_decision": "REJECTED"}


# def should_retry(state: AgentState):
#     result = state.get("validation_result")
#     count = state.get("retry_count", 0)

    
#     if result and result.is_valid:
#         return "decide"  
   
#     if count < 2:
#         return "reflect"
    
#     return "decide"


workflow = StateGraph(AgentState)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
# workflow.add_node("reflect", reflection_node)
workflow.add_node("decide", decision_node)


workflow.set_entry_point("extract")
workflow.add_edge("extract", "validate")


# workflow.add_conditional_edges(
#     "validate",
#     should_retry,
#     {
#         "decide": "decide",
#         "reflect": "reflect" 
#     }
# )


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