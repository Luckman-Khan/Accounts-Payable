from agent import app
from IPython.display import Image, display


try:
   
    graph_image = app.get_graph().draw_mermaid_png()
    
    with open("agent_architecture.png", "wb") as f:
        f.write(graph_image)
        
    print("✅ Graph saved as 'agent_architecture.png'")
except Exception as e:
    print(f"Could not draw graph: {e}")
    print("You might need to install: pip install pygraphviz")