from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import os
import json
import tempfile
from dotenv import load_dotenv

load_dotenv()

from database import init_db, create_task, save_step, complete_task, fail_task, get_history, get_task_steps
from agent import run_agent
from rag import add_document, extract_text_from_file, get_uploaded_files, get_doc_count, delete_document

app = FastAPI(title="AgentFlow", version="1.0.0")

# TODO: restrict this later, allowing everything for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# request model
class TaskRequest(BaseModel):
    task: str


# setup db on startup
@app.on_event("startup")
def startup():
    print("starting agentflow...")
    init_db()


# health check
@app.get("/health")
def health():
    return {"status": "ok", "message": "AgentFlow is running!"}


# run a task - streams the steps back as SSE
@app.post("/run")
def run_task(req: TaskRequest):
    if not req.task or len(req.task.strip()) == 0:
        raise HTTPException(status_code=400, detail="Task is required")

    task_text = req.task.strip()

    # save task to database
    task_id = create_task(task_text)

    def stream_steps():
        # this sends steps as server-sent events to frontend
        step_count = 0

        def on_step(step_data):
            nonlocal step_count
            step_count += 1

            # save step to database
            save_step(
                task_id,
                step_data.get("step", step_count),
                step_data.get("thought", ""),
                step_data.get("tool"),
                step_data.get("tool_input"),
                step_data.get("tool_output")
            )

        try:
            # run the agent - collect steps via callback
            all_steps = []

            def on_step_and_collect(step_data):
                on_step(step_data)
                all_steps.append(step_data)

            # i couldnt figure out how to stream directly from the agent loop
            # so collecting all steps first then yielding them
            result = run_agent(task_text, on_step=on_step_and_collect)

            # stream each step as SSE
            for step_data in all_steps:
                yield f"data: {json.dumps(step_data)}\n\n"

            # update task in database
            complete_task(task_id, result.get("final_answer", ""), result.get("total_steps", 0))

            # send done event
            yield f"data: {json.dumps({'type': 'done', 'task_id': task_id})}\n\n"

        except Exception as e:
            print(f"task error: {e}")
            fail_task(task_id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        stream_steps(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# get task history
@app.get("/history")
def history():
    results = get_history()
    return {"history": results, "count": len(results)}


# get steps for a specific task
@app.get("/history/{task_id}")
def task_detail(task_id: int):
    steps = get_task_steps(task_id)
    return {"task_id": task_id, "steps": steps, "count": len(steps)}


# ---- document upload for RAG ----

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    allowed = ['txt', 'pdf', 'docx', 'md', 'csv', 'json', 'py', 'js', 'html']
    ext = file.filename.split('.')[-1].lower()

    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported. Use: {', '.join(allowed)}")

    # save to temp file, extract text, then add to vector store
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        content = await file.read()
        tmp.write(content)
        tmp.close()

        # extract text from the file
        text = extract_text_from_file(tmp.name, file.filename)
        os.unlink(tmp.name)  # delete temp file

        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract text from file or file is too short")

        # add to vector store
        result = add_document(text, file.filename)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            "message": f"Uploaded {file.filename}",
            "filename": file.filename,
            "chunks": result["chunks"],
            "total_chars": result["total_chars"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# get list of uploaded documents
@app.get("/documents")
def list_documents():
    files = get_uploaded_files()
    count = get_doc_count()
    return {"documents": files, "total_chunks": count}


# delete a document
@app.delete("/documents/{filename}")
def remove_document(filename: str):
    ok = delete_document(filename)
    if ok:
        return {"success": True, "message": f"Deleted {filename}"}
    raise HTTPException(status_code=404, detail="Document not found")


# run it
if __name__ == "__main__":
    import uvicorn
    print("starting agentflow on port 8001...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
