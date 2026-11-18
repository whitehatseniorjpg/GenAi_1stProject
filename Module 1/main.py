import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, Depends, HTTPException
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv
from Schema import TextRequest
from pptx import Presentation
from io import BytesIO
import jwt

load_dotenv()  # Load environment variables from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

model = os.getenv("CHAT_MODEL")
if not model:
    raise ValueError("CHAT_MODEL is not set in the environment variables.")  

app = FastAPI(
   title = "Module 1 - API Interaction of AI Tutor Project",
   description= "This API allows interaction with the AI Tutor Project, enabling users to request text generation based on specific topics, courses, and student levels.",
   version= "1.0.0",
)

ai_client = genai.Client(api_key=gemini_api_key)

def get_current_user(token: str = Header(...)):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["username"]
    except Exception:
        raise HTTPException(status_code=401, detail={"message": "Token Invalid or Expired"})

#Text input to generate text based on the topic, course, and student level
@app.post("/generate_text")
async def generate_explanation(request: TextRequest, username: str = Depends(get_current_user)):
    prompt = f"""
    You are an AI tutor creating study material for a student.
    Topic: "{request.topic}"
    Subject: "{request.course or "Not specified"}"
    Student level: "{request.student_level}"

    Explain the topic clearly and accurately using language suited to the student.
    Output a valid JSON response containing:
    1. "topic": string
    2. "lesson_content": string (clear explanation for study)
    3. "key_terms": list of objects with "term" and "definition" strings
    4. "example": string (a relevant example)
    5. "practice_questions": list of 3 questions
    """

    try:
        response =  ai_client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
            
        )
        response_json = json.loads(response.text)
        return JSONResponse(status_code=200, content=response_json)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Academic Image Analysis and Explanation
@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...), question: str = Form(...), username: str = Depends(get_current_user)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Only JPEG and PNG are allowed."})


    try:
        image_bytes = await file.read()
        image_input = types.Part.from_bytes(data=image_bytes, mime_type=file.content_type)

        prompt = f"""
        You are an AI tutor analyzing an academic image.
        Question: "{question}"

        Provide a clear and accurate explanation of the image in relation to the question.
        Output a valid JSON response containing:
        1. "image_analysis": string (detailed analysis of the image)
        2. "key_points": list of strings (important points from the analysis)
        3. "related_concepts": list of strings (concepts related to the image and question)
        """

        response =  ai_client.models.generate_content(
            model=model,
            contents=[prompt, image_input],
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )

        response_json = json.loads(response.text)
        return JSONResponse(status_code=200, content=response_json)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Text Question and Audio Answer Generation
@app.post("/evaluate_audio_answer")
async def evaluate_audio_answer(file: UploadFile = File(...), question: str = Form(...), username: str = Depends(get_current_user)):
    if file.content_type not in ["audio/mpeg", "audio/wav"]:
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Only MP3 and WAV are allowed."})

    try:
        audio_bytes = await file.read()
        audio_input = types.Part.from_bytes(data=audio_bytes, mime_type=file.content_type)

        prompt = f"""
        You are an AI tutor analyzing an academic image.
        Question: "{question}"

        Provide a clear and accurate explanation of the image in relation to the question.
        Output a valid JSON response containing:
        1. "image_analysis": string (detailed analysis of the image)
        2. "key_points": list of strings (important points from the analysis)
        3. "related_concepts": list of strings (concepts related to the image and question)
        """

        response =  ai_client.models.generate_content(
            model=model,
            contents=[prompt, audio_input],
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )

        response_json = json.loads(response.text)
        return JSONResponse(status_code=200, content=response_json)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# Video Analysis and Generate 3 MCQ Questions with options and answers
@app.post("/analyze_video")
async def analyze_video(file: UploadFile = File(...), question: str = Form(...), username: str = Depends(get_current_user)):
    if file.content_type not in ["video/mp4", "video/avi"]:
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Only MP4 and AVI are allowed."})

    try:
        video_bytes = await file.read()
        video_input = types.Part.from_bytes(data=video_bytes, mime_type=file.content_type)

        prompt = f"""
        You are an AI tutor analyzing an academic video.
        Question: "{question}"

        Provide a clear and accurate analysis of the video in relation to the question.
        Generate 3 multiple-choice questions (MCQs) based on the video content, each with 4 options and the correct answer.
        Output a valid JSON response containing:
        1. "video_analysis": string (detailed analysis of the video)
        2. "mcq_questions": list of objects with "question", "options" (list of strings), and "correct_answer" (string)
        """

        response =  ai_client.models.generate_content(
            model=model,
            contents=[prompt, video_input],
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )

        response_json = json.loads(response.text)
        return JSONResponse(status_code=200, content=response_json)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# PPT Analysis and Study Material Generation
@app.post("/analyze_ppt")
async def analyze_ppt(
    file: UploadFile = File(...),
    mode: str = Form("detailed"),
    question: str = Form("Explain the presentation."),
    username: str = Depends(get_current_user)
):

    if not file.filename.endswith(".pptx"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PPTX files are allowed."}
        )

    try:
        # Extract text from PPT
        ppt_bytes = await file.read()
        presentation = Presentation(BytesIO(ppt_bytes))

        ppt_content = ""

        for i, slide in enumerate(presentation.slides, start=1):
            ppt_content += f"\nSlide {i}:\n"

            for shape in slide.shapes:
                if shape.has_text_frame:
                    ppt_content += shape.text + "\n"

        # Prepare prompt
        prompt = f"""
        You are an AI tutor analyzing an academic PowerPoint.

        Student Question: "{question}"

        Presentation Content:
        {ppt_content}

        Analysis Mode: {mode}

        Explain the presentation according to the selected mode:

        1. detailed: Explain every slide in detail with examples.
        2. points: Explain concepts using headings and bullet points.
        3. flowchart: Explain concepts using logical flowcharts and arrows.
        4. exam_notes: Generate exam-oriented notes and important questions.

        Output a valid JSON response containing:

        1. "presentation_summary": string
        2. "slide_wise_analysis": list of objects containing
           "slide_number", "explanation" and "key_points"
        3. "flowchart": string
        4. "important_topics": list of strings
        5. "practice_questions": list of strings
        """

        response = ai_client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )

        response_json = json.loads(response.text)

        return JSONResponse(
            status_code=200,
            content=response_json
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
