from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from agent_logic import query_claude_with_tasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import base64
from utils.secrets import JWT_SECRET
from starlette.middleware.sessions import SessionMiddleware
from mongo_utils import get_user_by_id, get_all_tasks, get_role_hierarchy

app = FastAPI()

# Define security scheme (Basic Auth)
security = HTTPBasic()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to enforce authentication for Swagger UI & OpenAPI
async def enforce_docs_auth(request: Request):
    if request.url.path in ["/docs", "/openapi.json"]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(
                headers={"WWW-Authenticate": "Basic"},
                status_code=401,
                content="Unauthorized: Missing authentication"
            )

        # Decode the Base64-encoded credentials
        encoded_credentials = auth_header.split("Basic ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)

        # Validate credentials
        correct_username = "Admin"
        correct_password = JWT_SECRET  # Ensure JWT_SECRET is set correctly

        if username != correct_username or password != correct_password:
            return Response(
                headers={"WWW-Authenticate": "Basic"},
                status_code=401,
                content="Unauthorized: Incorrect credentials"
            )

# Add authentication middleware for Swagger UI & OpenAPI
@app.middleware("http")
async def docs_auth_middleware(request: Request, call_next):
    response = await enforce_docs_auth(request)
    if response:
        return response  # Return 401 if unauthorized

    return await call_next(request)

# Secure the Swagger UI
@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

# Secure the OpenAPI schema (optional)
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(title="API", version="1.0.0", routes=app.routes)


class QueryRequest(BaseModel):
    user_id: str 
    prompt: str

class UserScoreRequest(BaseModel):
    user_id: str

# Main endpoint to ask the delegation ai agent
@app.post("/ask")
def ask_agent(request: QueryRequest):
    try:
        user = get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role = user.get("role", "delegatee").capitalize()
        all_tasks = get_all_tasks()

        if role.lower() == "delegatee":
            filtered_tasks = [
                t for t in all_tasks 
                if request.user_id in [str(uid) for uid in t.get("delegateeName", [])]
            ]
        elif role.lower() == "delegator":
            filtered_tasks = [
                t for t in all_tasks 
                if str(t.get("delegatorName")) == request.user_id
            ]
        else:  # Boss
            filtered_tasks = [
                t for t in all_tasks
                if request.user_id in [str(uid) for uid in t.get("delegateeName", [])]
                or str(t.get("delegatorName")) == request.user_id
            ]

        if not filtered_tasks:
            return {"answer": "No relevant data found for your role or prompt."}

        answer = query_claude_with_tasks(request.prompt, filtered_tasks, role)
        return {"answer": answer}

    except Exception as e:
        return {"answer": f"Something went wrong while processing your request. {str(e)}"}


# Endpoint to user details and total score
@app.post("/user-score")
def get_user_score(request: UserScoreRequest):
    user = get_user_by_id(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    name = user.get("name", "Unknown")
    role = user.get("role", "Unknown").capitalize()

    all_tasks = get_all_tasks()

    if role.lower() == "delegatee":
        user_tasks = [
            task for task in all_tasks
            if request.user_id in [str(uid) for uid in task.get("delegateeName", [])]
        ]
    elif role.lower() == "delegator":
        user_tasks = [
            task for task in all_tasks
            if str(task.get("delegatorName")) == request.user_id
        ]
    else:  # Boss
        user_tasks = [
            task for task in all_tasks
            if request.user_id in [str(uid) for uid in task.get("delegateeName", [])]
            or str(task.get("delegatorName")) == request.user_id
        ]

    total_score = sum(
        task.get("taskScore", 0)
        for task in user_tasks
        if isinstance(task.get("taskScore"), (int, float))
    )

    return {
        "user_id": request.user_id,
        "name": name,
        "role": role,
        "total_score": total_score
    }

# Public Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "Service is running normally"}

if __name__ == "__main__":
    import uvicorn
    # Run the application with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
