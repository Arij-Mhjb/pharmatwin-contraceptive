from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.sparql_client import SparqlError
from backend.routes import health,profils,ontology,search,ask,contraceptifs,patient
s=get_settings();app=FastAPI(title=s.app_name,version="1.0.0",description="Academic semantic backend; not a medical decision system.")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in s.cors_origins.split(",")],allow_methods=["*"],allow_headers=["*"],allow_credentials=True)
@app.exception_handler(SparqlError)
async def sparql_error(_:Request,exc:SparqlError): return JSONResponse(status_code=503,content={"detail":str(exc)})
for r in (health.router,profils.router,ontology.router,search.router,ask.router,contraceptifs.router,patient.router): app.include_router(r,prefix="/api")
@app.get("/")
def root(): return {"name":s.app_name,"docs":"/docs","notice":"Academic use only; no diagnosis or prescription."}
