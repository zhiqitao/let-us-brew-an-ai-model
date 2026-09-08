#!/usr/bin/env python3
"""Fleet proofread of the new book draft (public content -> safe for free cloud).
Sends the assembled manuscript to several distinct free models with a focused
copy-edit prompt, collecting independent opinions.
"""
import os, json, urllib.request, concurrent.futures

ROOT="/home/ubuntu/hermes-work/let-us-brew-an-ai-model"
MANU=os.path.join(ROOT,"book","_for_review.md")
OUT=os.path.join(ROOT,"docs","reviews")
os.makedirs(OUT,exist_ok=True)

or_key=""
for p in ["/home/ubuntu/.hermes/profiles/muta/.env","/home/ubuntu/.hermes/.env"]:
    if os.path.exists(p):
        for line in open(p):
            line=line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                or_key=line.split("=",1)[1].strip().strip('"').strip("'")
    if or_key: break
OR_URL="https://openrouter.ai/api/v1/chat/completions"

PROMPT_TMPL="""You are a sharp COPY-EDITOR and BOOK REVIEWER. You are reviewing the draft of
"Let us brew an AI Model" — a hands-on book about what a small language model can
actually learn when given one job: reading a natural-language programming request and
writing the Python program. The book's thesis is that building a small model is easy
but knowing whether it truly learned (vs memorized / exploited a shortcut) is hard.

The author wants the book to be INTUITIVE and reader-friendly, not a dry lab report.

Here is the full current manuscript:

---
{manuscript}
---

Give a CONCRETE, line-level copy-edit, in priority order:
1. CLARITY & INTUITION: flag sentences that are confusing, jargon-heavy, or read like
   an academic/lab report. Suggest a specific plain-language rewrite. The author
   wants it to click for a curious reader, not a researcher.
2. TONE / VOICE: any sentence that sounds robotic or off-register (too formal, too
   casual, inconsistent). Suggest the fix.
3. REPETITION: ideas/phrases stated too many times across chapters. Name where.
4. STRUCTURE: any chapter/section that reads as a spec or a laundry list rather than
   a flowing narrative. Suggest how to make it accessible.
5. ACCURACY CONCERNS: any claim that seems overstated, or where an analogy is
   stretched past the point of clarity.
6. THE ANNOYING PART: is there any metaphor or framing that's overused or that
   distracts? Flag it.
7. Anything else that would stop an editor accepting this for publication.

Be SPECIFIC and actionable. For each issue: quote the offending text, say what's
wrong, give the fix. Prioritize the 15-20 most important. Do NOT just praise it.
End with a short "TOP 5 MOST IMPORTANT FIXES" list. Output plain markdown."""

def call(model, prompt, retries=4):
    body={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":4000}
    headers={"Content-Type":"application/json","Authorization":"Bearer "+or_key}
    for i in range(retries):
        try:
            req=urllib.request.Request(OR_URL,data=json.dumps(body).encode(),headers=headers)
            with urllib.request.urlopen(req,timeout=600) as r: return json.loads(r.read().decode())
        except Exception as e:
            print(f"  [ERR {model}] retry{i+1} {type(e).__name__}: {e}"); import time; time.sleep(8*(i+1))
    return None

manuscript=open(MANU,encoding='utf-8').read()
prompt=PROMPT_TMPL.format(manuscript=manuscript)
print(f"manuscript {len(manuscript)} chars -> sending to fleet")

TASKS=[
    ("or-nemotron-ultra","nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("or-nemotron35","nvidia/nemotron-3.5-lightning:free"),
]
def work(name, model):
    print(f"  -> {name} ({model})")
    d=call(model,prompt)
    if d:
        c=d["choices"][0]["message"].get("content") or ""
        open(os.path.join(OUT,name+".md"),"w",encoding="utf-8").write(f"# {name} | {d.get('model','')}\n\n"+c)
        print(f"     {name}: done ({len(c)} chars)")
    else:
        open(os.path.join(OUT,name+".md"),"w",encoding="utf-8").write(f"# {name} | FAILED\n")
        print(f"     {name}: FAILED")

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    futs=[ex.submit(work,n,m) for n,m in TASKS]
    for f in concurrent.futures.as_completed(futs): pass
print("done ->", OUT)
