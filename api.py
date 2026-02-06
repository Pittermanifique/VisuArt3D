import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from pathlib import Path

app = FastAPI()
queue = None

app.mount("/static", StaticFiles(directory="web//static"), name="static")


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/content")
async def get_content():
    content_dirs = os.listdir("content")
    result = []
    for i in content_dirs:
        files = os.listdir(os.path.join("content", i))
        model_content = {
            "project": i,
            "model": True if any(f.endswith((".glb", ".glbf")) for f in files) else False,
            "texture": True if any(f.endswith(".png") for f in files) else False,
            "fr": True if "fr.wav" in files else False,
            "en": True if "en.wav" in files else False,
            "es": True if "es.wav" in files else False,
            "de": True if "de.wav" in files else False
        }
        result.append(model_content)
    return {"content": result}

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    data: str = Form(...)
):
    data = json.loads(data)

    project = data["project"]

    save_path = Path("content") / project
    save_path.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    filename = file.filename
    

    if ext in [".glb", ".glbf"]:
        for f in save_path.iterdir():
            if f.suffix.lower() in [".glb", ".glbf"]:
                f.unlink()

    elif ext == ".png":
        for f in save_path.iterdir():
            if f.suffix.lower() == ".png":
                f.unlink()

    elif ext == ".wav":
        filename = f"{data['language']}.wav"

    else:
        return {"error": "extension not supported"}

    file_location = save_path / filename

    with open(file_location, "wb") as file_object:
        file_object.write(await file.read())

    return {"status": f"{filename} uploaded successfully to {project}"}

@app.post("/delete")
async def delete_file(
    data: str = Form(...),
    ):

    data = json.loads(data)

    project = data["project"]
    save_path = Path("content") / project
    type = data["type"]
    
    if type == "model":
        for f in save_path.iterdir():
            if f.suffix.lower() in [".glb", ".glbf"]:
                f.unlink()

                return {"status": f"model {f.name} in {project} deleted"}
            
    elif type == "texture":
        for f in save_path.iterdir():
            if f.suffix.lower() == ".png":
                f.unlink()

                return {"status": f"texture {f.name} in {project} deleted"}
            
    elif type == "audio":
        language = data["language"]
        audio_file = save_path / f"{language}.wav"
        if audio_file.exists():
            audio_file.unlink()

        return {"status": f"audio {language} in {project} deleted"}
    
    elif type == "project":
        if save_path.exists():
            shutil.rmtree(save_path)
            return {"status": f"project {project} deleted"}
        return {"status": f"project {project} does not exist"}
    
    else:
        return {"error": "type not supported"}
        
    
@app.post("/set_project")
async def set_project(project: str, 
                      language: str):
    global queue
    if queue is None:
        return {"error": "queue not initialized"}

    project = {"project": project, "language": language}
    queue.put(("set_project", project))
    
    return {"status": "sent", "project": project["project"], "language": project["language"]}

@app.get("/userpage")
async def get_userpage():
    return FileResponse("web/pages/userpage.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)