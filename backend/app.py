from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.sparql_client import SparqlError
from backend.routes import health,profils,ontology,search,ask,contraceptifs,patient,auth
from backend.services import auth_store
s=get_settings()
@asynccontextmanager
async def lifespan(_: FastAPI):
    auth_store.initialize()
    if s.bootstrap_admin_email and s.bootstrap_admin_password:
        auth_store.bootstrap_admin(s.bootstrap_admin_email, s.bootstrap_admin_password.get_secret_value(), s.bootstrap_admin_name)
    yield
app=FastAPI(title=s.app_name,version="2.0.0",description="Academic semantic backend; not a medical decision system.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in s.cors_origins.split(",")],allow_methods=["*"],allow_headers=["*"],allow_credentials=True)
@app.exception_handler(SparqlError)
async def sparql_error(_:Request,exc:SparqlError): return JSONResponse(status_code=503,content={"detail":str(exc)})
app.include_router(health.router,prefix="/api")
app.include_router(auth.router,prefix="/api")
app.include_router(auth.admin_router,prefix="/api")
app.include_router(profils.router,prefix="/api",dependencies=[Depends(auth.admin)])
for r in (ontology.router,search.router,ask.router,contraceptifs.router): app.include_router(r,prefix="/api",dependencies=[Depends(auth.current_user)])
app.include_router(patient.router,prefix="/api")
@app.get("/")
def root(): return {"name":s.app_name,"docs":"/docs","notice":"Academic use only; no diagnosis or prescription."}
