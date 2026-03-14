# AI Interviewer

AI Interviewer is a platform that simulates a technical interview experience using artificial intelligence. It allows users to practice interview questions, submit answers, attempt coding problems, and receive automated feedback.

The goal of this project is to help students and developers practice technical interviews in a realistic environment without needing a human interviewer.

---

## Features

### AI Interview Questions
The system dynamically generates interview questions based on the user's role and experience level.

### Answer Evaluation
User responses are evaluated using AI to provide feedback and improvement suggestions.

### Coding Round
The interview includes technical coding questions that can be analyzed by the system.

### Interview Report Generation
At the end of the interview, the system generates a downloadable PDF report summarizing the candidate's performance.

### Session-Based Interview Flow
Each interview runs inside a unique session, allowing the system to track questions, answers, and evaluations.

---

## System Architecture

```
Frontend (Vercel)
        │
        ▼
FastAPI Backend (Render)
        │
        ▼
LLM Logic (Question Generation & Answer Evaluation)
```

The frontend sends requests to the FastAPI backend.  
The backend manages interview sessions, generates questions using LLM logic, evaluates responses, and produces the final interview report.

---

## Tech Stack

### Backend
- Python
- FastAPI
- Large Language Model APIs

### Frontend
- HTML
- CSS
- JavaScript

### Deployment
- Vercel (Frontend)
- Render (Backend)

---

## Backend Components

The backend is responsible for managing the entire interview workflow.

Core responsibilities include:

- Creating and managing interview sessions
- Generating interview questions
- Evaluating candidate responses
- Analyzing coding answers
- Tracking interview history
- Generating the final interview report

The AI logic for generating questions and evaluating answers is implemented in the `llmbrain` module.

---

## API Endpoints

| Endpoint | Method | Description |
|--------|--------|-------------|
| `/` | GET | Health check endpoint to verify the server is running |
| `/config` | GET | Returns configuration values such as STT keys |
| `/startinterview` | POST | Starts a new interview session and returns a session ID |
| `/question/{session_id}` | GET | Retrieves the next interview question for the session |
| `/answer/{session_id}` | POST | Submits the user's answer and returns evaluation plus the next question |
| `/report/{session_id}` | GET | Generates and downloads the final interview report as a PDF |

---

## Interview Flow

1. The user starts an interview session using `/startinterview`.
2. The system generates the first question using `/question/{session_id}`.
3. The user submits an answer through `/answer/{session_id}`.
4. The backend evaluates the answer and determines the next question.
5. This process continues until the interview is completed.
6. After completion, a detailed PDF report can be downloaded using `/report/{session_id}`.

---

## Project Structure

```
ai-interviewer
│
├── backend
│   ├── run.py
│   ├── llmbrain.py
│   ├── report_generator.py
│   └── requirements.txt
│
├── frontend
│   ├── index.html
│   ├── script.js
│   └── styles.css
│
└── README.md
```

---

## What I Learned

Building this project helped me gain experience with:

- Designing and implementing REST APIs
- Building CRUD-style API workflows
- Writing API endpoints using FastAPI
- Managing session-based application state
- Working with external AI APIs
- Connecting frontend and backend systems
- Deploying backend services using Render
- Structuring backend logic using Python

---

## Credits

This project was built as a collaborative effort.

- Backend, FastAPI APIs, and LLM logic were implemented by **Rohan**.
- Some UI components were created with help from **Jia Bajpai**.
- Some UI elements were generated using **Stitch**.
- Some JavaScript logic was implemented with assistance from AI tools.

---

## Live Demo

Frontend:  
https://ai-interviewer-tau-nine.vercel.app

---

## Future Improvements

Potential improvements for the project include:

- Voice-based interview interaction
- Resume-based question generation
- Interview scoring system
- Interview history dashboard
- Improved UI and user experience

---

## License

This project is open-source and available under the MIT License.