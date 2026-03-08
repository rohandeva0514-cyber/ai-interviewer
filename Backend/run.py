from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from llmbrain import greet_user, next_question, evaluate_ans, analyze_code
from report_generator import generate_report
import uuid
import os
from datetime import datetime


app=FastAPI()

@app.get("/")
def health():
    return {"status": "server running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-interviewer-tau-nine.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Information(BaseModel):
    name:str
    role:str
    is_fresher:bool

class Question(BaseModel):
    question:str

class Answer(BaseModel):
    answer:str


sessions={}

# ── /config: exposes STTKEY (Deepgram) to the frontend ──
@app.get("/config")
def config():
    return {"stt_key": os.getenv("STTKEY", "")}


# ── /report/{session_id}: generates and returns PDF via ReportLab ──
@app.get("/report/{session_id}")
def report(session_id: str):
    if session_id not in sessions:
        return JSONResponse({"error": "Invalid session"}, status_code=404)

    session = sessions[session_id]

    # Attach current timestamp as duration if not already stored
    started_at = session.get("started_at")
    if started_at:
        elapsed = datetime.now() - started_at
        total_sec = int(elapsed.total_seconds())
        mm = total_sec // 60
        ss = total_sec % 60
        session["duration"] = f"{mm:02d}:{ss:02d}"
    else:
        session["duration"] = "—"

    pdf_bytes = generate_report(session)

    safe_name = session.get("name", "candidate").replace(" ", "_")
    filename  = f"interview_report_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )


@app.post("/startinterview")
def startinterview(info:Information):
    
    session_id=str(uuid.uuid4()) 

    sessions[session_id]={
        "name":info.name,
        "role":info.role,
        "is_fresher":info.is_fresher,
        "started_at": datetime.now(),
        "current_question":None,
        "current_question_type":None,
        "q_count":0,
        "last_eval":None,
        "difficulty":"easy",  
        "history":[],
        "completed":False
    }   
    return{"session_id":session_id,
           "greeting":greet_user(info.name)}


@app.get("/question/{session_id}")
def question(session_id:str):
    if session_id not in sessions:
        return {"Invalid Session"}
    
    session=sessions[session_id]
    
    if session["current_question"] is None:
        question_data=next_question(
            name=session["name"],
            role=session["role"],
            is_fresher=session["is_fresher"],
            q_count=session["q_count"],
            difficulty=session["difficulty"],
            history=session["history"],
            lasteval=session["last_eval"]
        )
        session["current_question"]=question_data["question"]
        session["current_question_type"]=question_data["question_type"]

        return {
        "question": session["current_question"],
        "question_type": session["current_question_type"]
    }

@app.post("/answer/{session_id}")
def answer(data: Answer, session_id: str):
    if session_id not in sessions:
        return {"error": "Invalid Session"}

    session = sessions[session_id]

    if session["completed"]:
        return {"error": "Interview already completed"}

   
    if session["current_question_type"] == "technical":
        evaluation = analyze_code(
            session["role"],
            session["current_question"],
            data.answer
        )
    else:
        evaluation = evaluate_ans(
            session["role"],
            session["current_question"],
            data.answer
        )


    session["history"].append({
        "question": session["current_question"],
        "question_type": session["current_question_type"],
        "answer": data.answer,
        "evaluation": evaluation
    })

  
    session["q_count"] += 1
    session["last_eval"] = evaluation

  
    session["current_question"] = None
    session["current_question_type"] = None

  
    question_data = next_question(
        name=session["name"],
        role=session["role"],
        q_count=session["q_count"],          
        lasteval=session["last_eval"],       
        difficulty=session["difficulty"],
        history=session["history"],
        is_fresher=session["is_fresher"]
    )

     
    if question_data["question_type"] == "end":
        session["completed"] = True
        return {
            "interview_completed": True,
            "message": question_data["question"]
        }

 
    session["current_question"] = question_data["question"]
    session["current_question_type"] = question_data["question_type"]

    return {
        "interview_completed": False,
        "question": session["current_question"],
        "question_type": session["current_question_type"],
        "evaluation": evaluation,
        "qcount": session["q_count"]
    }