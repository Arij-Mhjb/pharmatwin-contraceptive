from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from backend.config import get_settings
from backend.models.auth import SignUp, SignIn, Onboarding, PasswordChange, AvatarUpdate, UserAdminUpdate
from backend.services import auth_store

SESSION_COOKIE = "pharmatwin_session"
CSRF_COOKIE = "pharmatwin_csrf"
router = APIRouter(prefix="/auth", tags=["authentication"])
admin_router = APIRouter(prefix="/admin", tags=["administration"])

def set_session(response: Response, user):
    settings = get_settings(); token, csrf, expires = auth_store.create_session(user["id"], settings.session_days)
    options = dict(path="/", secure=settings.cookie_secure, samesite="lax", expires=expires)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **options)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **options)

def current_user(pharmatwin_session: str | None = Cookie(default=None)):
    result = auth_store.session_user(pharmatwin_session)
    if not result: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    return result[0]

def current_session(request: Request, x_csrf_token: str | None = Header(default=None), pharmatwin_session: str | None = Cookie(default=None), pharmatwin_csrf: str | None = Cookie(default=None)):
    result = auth_store.session_user(pharmatwin_session)
    if not result: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    if not auth_store.csrf_valid(result[1], x_csrf_token, pharmatwin_csrf): raise HTTPException(status.HTTP_403_FORBIDDEN, "Jeton CSRF invalide")
    return result[0]

def admin(user=Depends(current_user)):
    if user["role"] != "admin": raise HTTPException(status.HTTP_403_FORBIDDEN, "Rôle administrateur requis")
    return user

def admin_session(user=Depends(current_session)):
    if user["role"] != "admin": raise HTTPException(status.HTTP_403_FORBIDDEN, "Rôle administrateur requis")
    return user

@router.post("/signup", status_code=201)
def signup(payload: SignUp, response: Response):
    try: user = auth_store.create_user(payload.email, payload.password, payload.display_name)
    except ValueError as exc: raise HTTPException(409 if "existe" in str(exc) else 422, str(exc))
    set_session(response, user); return {"user": user}

@router.post("/signin")
def signin(payload: SignIn, response: Response):
    user = auth_store.authenticate(payload.email, payload.password)
    if not user: raise HTTPException(401, "Adresse e-mail ou mot de passe incorrect")
    set_session(response, user); return {"user": user}

@router.get("/session")
def session(user=Depends(current_user)): return {"user": user}

@router.post("/signout", status_code=204)
def signout(response: Response, token: str | None = Cookie(default=None, alias=SESSION_COOKIE), _=Depends(current_session)):
    auth_store.revoke_session(token); response.delete_cookie(SESSION_COOKIE, path="/"); response.delete_cookie(CSRF_COOKIE, path="/")

@router.put("/onboarding")
def onboarding(payload: Onboarding, user=Depends(current_session)):
    if not payload.academic_use_accepted: raise HTTPException(422, "L’usage académique doit être accepté")
    return {"user": auth_store.complete_onboarding(user["id"], payload.display_name)}

@router.put("/password", status_code=204)
def password(payload: PasswordChange, user=Depends(current_session)):
    try: auth_store.change_password(user["id"], payload.current_password, payload.new_password)
    except ValueError as exc: raise HTTPException(422, str(exc))

@router.put("/avatar")
def avatar(payload: AvatarUpdate, user=Depends(current_session)):
    return {"user": auth_store.update_avatar(user["id"], payload.data_url)}

@admin_router.get("/users")
def users(_=Depends(admin)): return auth_store.list_users()

@admin_router.get("/overview")
def overview(_=Depends(admin)): return auth_store.admin_overview()

@admin_router.patch("/users/{user_id}")
def edit_user(user_id: str, payload: UserAdminUpdate, actor=Depends(current_session)):
    if actor["role"] != "admin": raise HTTPException(403, "Rôle administrateur requis")
    try: return auth_store.update_user(actor["id"], user_id, payload.role, payload.status)
    except KeyError: raise HTTPException(404, "Compte introuvable")
    except ValueError as exc: raise HTTPException(422, str(exc))
