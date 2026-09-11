import asyncio
import json
import os
import time
from rich.console import Console
from rich.table import Table
from app.rag.retriever import Retriever
from app.conversation.session_manager import SessionManager
from app.llm.response_generator import ResponseGenerator
from app.utils.logger import logger
from app.config import settings

console = Console()

async def run_evaluation():
    console.print("[bold green]Starting Formal RAG Evaluation Framework...[/bold green]")
    
    # 1. Load Dataset
    dataset_path = os.path.join("database", "eval_dataset.json")
    if not os.path.exists(dataset_path):
        console.print(f"[bold red]Dataset not found at {dataset_path}[/bold red]")
        return
        
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    # 2. Initialize System
    retriever = Retriever()
    retriever.load()
    session_manager = SessionManager()
    generator = ResponseGenerator(retriever, session_manager)
    
    results = []
    
    # 3. Run queries
    for item in dataset:
        qid = item["id"]
        query = item["query"]
        console.print(f"\n[bold blue]Running {qid}:[/bold blue] {query}")
        
        session_id = f"eval_session_{qid}"
        session_manager.memory.create_session(session_id)
        
        # Inject state for Q4 pronoun test
        if qid == "Q4":
            state = session_manager.get_state(session_id)
            state.crop_name = "ರಾಗಿ"
            state.crop_confirmed = True
            session_manager.memory.update_state(session_id, state)
        
        start_time = time.time()
        
        # Generate Response
        response_dict = await generator.generate(session_id, query)
        
        latency = time.time() - start_time
        
        # Analyze Results
        source = response_dict.get("source", "unknown")
        confidence = response_dict.get("confidence", 0.0)
        
        # Determine Success Criteria based on Expected Intent
        expected_intent = item.get("expected_intent")
        
        success = False
        if expected_intent == "non_agricultural" and source == "rejection":
            success = True
        elif expected_intent == "general" and source in ["database", "ollama", "gemini"] and confidence < 0.6:
            success = True # Expected fallback / low confidence
        elif source in ["database", "rag"] and confidence >= 0.45:
            success = True
            
        results.append({
            "id": qid,
            "query": query,
            "source": source,
            "confidence": confidence,
            "latency": latency,
            "success": success
        })
        
        console.print(f"Source: {source} | Confidence: {confidence:.2f} | Latency: {latency:.2f}s | Success: {success}")
        
        # Add a sleep to prevent Gemini rate limit exhaustion (429)
        time.sleep(10)
        
    # 4. Generate Report
    console.print("\n[bold green]=== Evaluation Report ===[/bold green]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Query", min_width=30)
    table.add_column("Source", justify="center")
    table.add_column("Confidence", justify="right")
    table.add_column("Latency (s)", justify="right")
    table.add_column("Pass", justify="center")
    
    passed = 0
    for r in results:
        if r["success"]:
            passed += 1
            pass_str = "[green]✓[/green]"
        else:
            pass_str = "[red]✗[/red]"
            
        table.add_row(
            r["id"],
            r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"],
            r["source"],
            f"{r['confidence']:.2f}",
            f"{r['latency']:.2f}",
            pass_str
        )
        
    console.print(table)
    
    accuracy = (passed / len(results)) * 100
    console.print(f"[bold cyan]Overall Accuracy / Pass Rate: {accuracy:.1f}%[/bold cyan]")
    
    # Wait for background tasks to finish
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
