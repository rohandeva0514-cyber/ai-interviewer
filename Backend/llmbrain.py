import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List , Dict , Optional
import os


load_dotenv()
genai.configure(api_key=os.getenv("KEY"))
model=genai.GenerativeModel("gemini-2.5-flash-lite")


def call_model(prompt:str) -> str:
    resp=model.generate_content(prompt)
    return resp.text






def extract_json(raw:str) -> dict:
    try:
        return json.loads(raw)
    except:
        start = raw.find("{")
        end   = raw.rfind("}")+ 1
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end])
            except:
                return {"error": "JSON parse failed", "raw": raw}
        return {"error": "No JSON in response", "raw": raw}
    


def detect_language(code: str) -> str:
    """
    Detects the programming language of the given code.
    Returns detected language (string).
    """
    prompt = f"""
You are a programming language detector.
Analyze the following code and return ONLY the language name in JSON.

Code:{code}
Output JSON
{{ "language": "Python/Java/C++/JavaScript/Go/HTML/CSS/JAVASCRIPT/Other" }}
"""
    raw = call_model(prompt)
    result = extract_json(raw)
    return result.get("language", "unknown")



def greet_user(name: str) -> str:
    prompt = (
        f"Interview is starting, greet the user {name}. "
        f"Greet warmly like HR, 12-20 words, do not mention HR name."
    )

    return call_model(prompt)











def evaluate_ans(role:str, question:str, answer:str)->dict:
    prompt = f"""
You are evaluating a candidate for the role: {role}.
Question: {question}
Answer: {answer}

Give feedback with:
- Score from 1–5
- One-line feedback

Output JSON:
{{ "score": int, "feedback": "..." }}
"""

    raw = call_model(prompt)
    return extract_json(raw)






def analyze_code(role: str, question: str, code: str) -> dict:

   
    language = detect_language(code)

    prompt = f"""
You are a technical interviewer evaluating a coding submission.

Role: {role}
Question: {question}
Language: {language}
Candidate's Code:
{code}

Please provide:
1. Bugs & mistakes
2. Optimizations & better logic
3. Best practices for readability
4. An improved version of the code
5. A score out of 10

Present this feedback in supportive HR-interviewer style:
- Professional, encouraging tone
- Explain simply
- Do not mention being an AI

Output JSON:
{{
  "language": "{language}",
  "bugs": "...",
  "optimizations": "...",
  "best_practices": "...",
  "improved_code": "...",
  "score": int,
  "feedback": "..."
}}
"""

    raw = call_model(prompt)
    return extract_json(raw)







def next_question(name:str,role:str,history:List[Dict],q_count:int,lasteval:Optional[Dict]= None,is_fresher: bool = False ,difficulty:str="easy",) ->Dict :

    if q_count>=15:
        return{
    "question":f"THANK YOU {name},THE INTERVIEW IS COMPLETE",
    "question_type":"end",
    "reason":"ALL 15 QUESTIONS ASKED"
        }

    if q_count<3:
        category="fresher" if is_fresher else "behavioral"
    elif q_count<12: 
        category="role"
    else:
        category="technical"

    if category=="technical" and lasteval:
        score = lasteval.get("score",3)
        if score>=4 and difficulty!="hard":
            difficulty = "medium" if difficulty == "easy" else "hard"
        elif score<=2 and difficulty!="easy":
            difficulty = "medium" if difficulty == "hard" else "easy"
       
    history_text="\n".join(
    [f"Q: {h['question']} &A:{h.get('answer',"ANSWER NOT RECORDED") or "ANSWER NOT RECORDED"}" for h in history]
    )
    if category == "behavioral":
        prompt = f"""
You are conducting a behavioral interview.
Candidate: {name}, Role: {role}
History:
{history_text or "No previous answers yet."}

Generate ONE behavioral question that tests teamwork, leadership, or problem solving.
Output JSON:
{{ "question" : "...", "question_type" : "behavioral", "reason" : "..." }}
"""
        
    elif category == "fresher":
        prompt = f"""
You are conducting a fresher interview.
Candidate: {name}, Role: {role}
History:
{history_text or "No previous answers yet."}

Generate ONE fresher-specific question.
Examples:
- Tell me about your final year project.
- What did you learn from your internship/college assignments?
- How do you keep your skills updated?
OUTPUT JSON:
{{"question":"...",question_type":"fresher","reason":"..."}}
        """
    elif category=="role":
        prompt = f"""
You are interviewing for {role}
Candidate Name:{name}
History:{history_text or "No previous answers yet."}

Generate ONE question about the candidate's role/domain based knowledge.

OUTPUT JSON:
{{"question":"...","question_type":"role","reason":"..."}}
"""
    else:
        prompt=f"""
You are conducting the technical coding round.
Candidate name: {name}, role: {role}, difficulty: {difficulty}
History:
{history_text or "No previous answers yet"}

Generate ONE coding or system design question appropriate for {difficulty} difficulty.
- easy: basic concepts and simple implementations
- medium: intermediate problem solving
- hard: complex algorithms and system design

You MUST return this exact JSON structure with question_type as the string "technical":
{{"question":"...","question_type":"technical","reason":"..."}}
"""
    try:
     raw=call_model(prompt)
     result=extract_json(raw)
    except:
        return "AI IS BUSY NOW, PLEASE TRY AGAIN LATER"

    if category=="technical":
        result['difficulty']=difficulty
    
    return result
