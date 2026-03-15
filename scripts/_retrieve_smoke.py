import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / "backend"))
from backend.rag.retriever import retrieve
q = "lighting upgrade energy savings for small shop"
hits = retrieve(q, top_k=5)
print("Hits:", len(hits))
for i,h in enumerate(hits):
    print(i+1, h.get("id") or h.get("metadata",{}).get("id"), h.get("score"))
    print("FILE:", h.get("metadata",{}).get("filename"))
    print("SECTION:", h.get("metadata",{}).get("section"))
    print("TEXT:", (h.get("text") or "")[:300].replace("\n"," "))
    print("----")
