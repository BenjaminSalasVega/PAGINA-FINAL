from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import random
API_PREFIX = "/api/vinaurbana"

app = FastAPI(
    title="API Viña Urbana",
    description="Plataforma boutique de vinos - Proyecto Viña Urbana",
    version="1.0.0"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/sesion/inicio")

# ============================================================
# CONFIGURACIÓN GENERAL - VIÑA URBANA
# ============================================================
SECRET_KEY = ""
ALGORITHM = ""
ACCESS_TOKEN_EXPIRE_MINUTES = 30




app = FastAPI(
    title="API Viña Urbana",
    description="Plataforma boutique de vinos - Proyecto Viña Urbana",
    version="1.0.0"
)

API_PREFIX = "/api/vinaurbana"

# CORS para que puedas pegarle desde cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pon tu dominio si quieres restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELOS BASE
# ============================================================
class Response(BaseModel):
    statusCode: int = 200
    message: str = "OK"
    data: Optional[dict | list] = None

# --- Autenticación ---
class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: str
    name: str
    hashed_password: str
    createdAt: datetime = Field(default_factory=datetime.now)

class UserRegistrationInput(BaseModel):
    email: str
    name: str
    password: str
    preferencias: Optional[List[str]] = []

class LoginInput(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ============================================================
# FUNCIONES DE SEGURIDAD
# ============================================================

def hashear_contraseña(password: str) -> str:
    # Hash simple para evitar errores con passlib/bcrypt
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verificar_contraseña(plain: str, hashed: str) -> bool:
    return hashear_contraseña(plain) == hashed


def crear_token(data: dict) -> str:
    """
    NO usamos JWT porque jose da error en tu PC.
    Devolvemos un token simple: 'token-<email>'
    """
    sub = data.get("sub")
    if not sub:
        raise ValueError("El payload del token debe incluir 'sub' con el email del usuario")
    return f"token-{sub}"


# ============================================================
# "BASES DE DATOS" EN MEMORIA
# ============================================================
db_users: List[User] = []
db_catalogo: List[dict] = []
db_membresias: List[dict] = []
db_notificaciones: List[dict] = []
db_stock: List[dict] = []

# ============================================================
# HELPERS
# ============================================================
def get_user_by_email(email: str) -> Optional[User]:
    return next((u for u in db_users if u.email == email), None)

def autenticar_usuario(email: str, password: str) -> Optional[User]:
    user = get_user_by_email(email)
    if not user or not verificar_contraseña(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Token esperado: 'token-<email>'
    Ejemplo: 'token-benja@example.com'
    """
    cred_exception = HTTPException(status_code=401, detail="Token inválido")

    # Validamos formato del token
    if not token.startswith("token-"):
        raise cred_exception

    # Sacamos el email desde el token
    email = token[len("token-"):]  # todo lo que viene después de 'token-'

    # Buscamos el usuario en la "BD"
    user = get_user_by_email(email) if "get_user_by_email" in globals() else None
    if user is None:
        # Si no tienes get_user_by_email, puedes hacer un for:
        for u in db_users:
            if u.email == email:
                user = u
                break

    if user is None:
        raise cred_exception

    return user

# ============================================================
# ENDPOINTS GENERALES
# ============================================================
@app.get("/")
def root():
    return {"mensaje": "API Viña Urbana operativa. Visita /docs para explorar los endpoints."}

# ============================================================
# H-01: Registro con preferencias enológicas
# ============================================================
@app.post(f"{API_PREFIX}/usuarios/registro", response_model=User, tags=["Usuarios"])
def registrar_usuario(input: UserRegistrationInput):
    if get_user_by_email(input.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    hashed = hashear_contraseña(input.password)

    nuevo = User(
        email=input.email,
        name=input.name,
        hashed_password=hashed,
    )
    db_users.append(nuevo)

    print(f"Usuario registrado: {nuevo.email} con preferencias {input.preferencias}")
    return nuevo

# ============================================================
# LOGIN / TOKENS
# ============================================================
@app.post(f"{API_PREFIX}/sesion/inicio", response_model=TokenResponse, tags=["Autenticación"])
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm usa "username"
    user = autenticar_usuario(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    access_token = crear_token({"sub": user.email})
    return TokenResponse(access_token=access_token)

@app.post(f"{API_PREFIX}/sesion/login-json", response_model=TokenResponse, tags=["Autenticación"])
def login_json(input: LoginInput):
    user = autenticar_usuario(input.email, input.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    access_token = crear_token({"sub": user.email})
    return TokenResponse(access_token=access_token)

# ============================================================
# H-02: Filtros avanzados de catálogo
# ============================================================
class CatalogFilter(BaseModel):
    cepa: Optional[str] = None
    origen: Optional[str] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None

@app.get(f"{API_PREFIX}/catalogo/filtrar", response_model=Response, tags=["Catálogo"])
def filtrar_catalogo(filtros: CatalogFilter = Depends()):
    print(f"Aplicando filtros: {filtros}")
    vinos = [
        {"nombre": "Syrah Reserva", "cepa": "Syrah", "origen": "Colchagua", "precio": 12000},
        {"nombre": "Pinot Noir", "cepa": "Pinot Noir", "origen": "Casablanca", "precio": 9800}
    ]
    filtrados = [
        v for v in vinos
        if (not filtros.cepa or filtros.cepa.lower() in v["cepa"].lower())
        and (not filtros.origen or filtros.origen.lower() in v["origen"].lower())
        and (not filtros.precio_min or v["precio"] >= filtros.precio_min)
        and (not filtros.precio_max or v["precio"] <= filtros.precio_max)
    ]
    return Response(data=filtrados, message="Resultados del filtro")

# ============================================================
# H-03: Membresía con beneficios
# ============================================================
class MembresiaInput(BaseModel):
    tipo: str  # Silver o Gold
    activa: bool = True

@app.post(f"{API_PREFIX}/membresias/activar", response_model=Response, tags=["Membresías"])
def activar_membresia(input: MembresiaInput, user: User = Depends(get_current_user)):
    registro = {"usuario": user.email, "tipo": input.tipo, "activa": input.activa, "fecha": datetime.now()}
    db_membresias.append(registro)
    print(f"Membresía {input.tipo} activada para {user.email}")
    return Response(message=f"Membresía {input.tipo} activada correctamente", data=registro)

# ============================================================
# H-04: Notificaciones personalizadas
# ============================================================
class NotificacionInput(BaseModel):
    canal: str  # email o whatsapp
    mensaje: str
    horario_inicio: Optional[str] = None
    horario_fin: Optional[str] = None

@app.post(f"{API_PREFIX}/notificaciones/enviar", response_model=Response, tags=["Notificaciones"])
def enviar_notificacion(input: NotificacionInput, user: User = Depends(get_current_user)):
    registro = {"usuario": user.email, "canal": input.canal, "mensaje": input.mensaje, "fecha": datetime.now()}
    db_notificaciones.append(registro)
    print(f"Notificación enviada a {user.email} por {input.canal}")
    return Response(message="Notificación procesada", data=registro)

# ============================================================
# H-05: Stock en tiempo real y bloqueo de sobreventa
# ============================================================
class ProductoStock(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nombre: str
    stock: int

db_stock.append({"nombre": "Cabernet Sauvignon Reserva", "stock": 3})

@app.post(f"{API_PREFIX}/stock/reservar", response_model=Response, tags=["Inventario"])
def reservar_stock(nombre: str, cantidad: int):
    for p in db_stock:
        if p["nombre"].lower() == nombre.lower():
            if p["stock"] < cantidad:
                raise HTTPException(status_code=400, detail="Stock insuficiente")
            p["stock"] -= cantidad
            print(f"Reservadas {cantidad} unidades de {nombre}")
            return Response(message=f"{cantidad} unidades reservadas de {nombre}")
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# ============================================================
# H-06: Seguimiento de pedido y despacho
# ============================================================
class Pedido(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    usuario: str
    estado: str = "Preparando"
    tracking: Optional[str] = None

db_pedidos: List[Pedido] = []

@app.post(f"{API_PREFIX}/pedidos/crear", response_model=Pedido, tags=["Pedidos"])
def crear_pedido(user: User = Depends(get_current_user)):
    pedido = Pedido(usuario=user.email, estado="Preparando", tracking=f"TRK-{random.randint(1000,9999)}")
    db_pedidos.append(pedido)
    print(f"Pedido {pedido.id} creado para {user.email}")
    return pedido

@app.get(f"{API_PREFIX}/pedidos/seguimiento", response_model=Response, tags=["Pedidos"])
def seguimiento_pedido(pedido_id: UUID):
    pedido = next((p for p in db_pedidos if p.id == pedido_id), None)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    avance = random.choice(["Preparando", "Despachado", "En ruta", "Entregado"])
    pedido.estado = avance
    return Response(data={"id": pedido.id, "estado": pedido.estado, "tracking": pedido.tracking})

# ============================================================
# H-07: Chatbot de maridaje
# ============================================================
class ChatbotInput(BaseModel):
    plato: str

@app.post(f"{API_PREFIX}/maridaje/chatbot", response_model=Response, tags=["Maridaje"])
def chatbot_maridaje(input: ChatbotInput):
    sugerencias = {
        "carne": "Cabernet Sauvignon",
        "pescado": "Sauvignon Blanc",
        "pasta": "Merlot",
        "queso": "Carmenere"
    }
    plato = input.plato.lower()
    vino = sugerencias.get(plato, "Pinot Noir")
    print(f"Sugerencia chatbot para {plato}: {vino}")
    return Response(message=f"Recomendado para {plato}: {vino}")

# ============================================================
# H-08: Atención multicanal y SLA
# ============================================================
class TicketInput(BaseModel):
    canal: str  # email, whatsapp, telefono
    prioridad: str  # alta, media, baja
    mensaje: str

db_tickets: List[dict] = []

@app.post(f"{API_PREFIX}/soporte/ticket", response_model=Response, tags=["Atención Cliente"])
def crear_ticket(input: TicketInput, user: User = Depends(get_current_user)):
    tiempo = {"email": "24h", "whatsapp": "5min", "telefono": "10min"}
    registro = {
        "usuario": user.email,
        "canal": input.canal,
        "prioridad": input.prioridad,
        "mensaje": input.mensaje,
        "SLA": tiempo.get(input.canal, "24h"),
        "fecha": datetime.now()
    }
    db_tickets.append(registro)
    print(f"Ticket creado para {user.email} via {input.canal}")
    return Response(message="Ticket registrado", data=registro)

# ============================================================
# H-09: Integración con marketplace gourmet
# ============================================================
class MarketplaceSyncInput(BaseModel):
    producto: str
    stock: int
    precio: float
    activo: bool = True

db_marketplace: List[dict] = []

@app.post(f"{API_PREFIX}/marketplace/sincronizar", response_model=Response, tags=["Integraciones"])
def sincronizar_marketplace(input: MarketplaceSyncInput):
    registro = {
        "producto": input.producto,
        "stock": input.stock,
        "precio": input.precio,
        "activo": input.activo,
        "fecha": datetime.now()
    }
    db_marketplace.append(registro)
    print(f"Marketplace sincronizado: {input.producto}")
    return Response(message="Sincronización completada", data=registro)

# ============================================================
# H-10: Alianzas con restaurantes
# ============================================================
class AlianzaInput(BaseModel):
    restaurante: str
    beneficio: str
    qr_valido: bool = True

db_alianzas: List[dict] = []

@app.post(f"{API_PREFIX}/alianzas/registrar", response_model=Response, tags=["Alianzas"])
def registrar_alianza(input: AlianzaInput):
    registro = {
        "restaurante": input.restaurante,
        "beneficio": input.beneficio,
        "qr_valido": input.qr_valido,
        "fecha": datetime.now()
    }
    db_alianzas.append(registro)
    print(f"Alianza creada con {input.restaurante}")
    return Response(message="Alianza registrada", data=registro)

# ============================================================
# H-11: Dashboard de métricas
# ============================================================
@app.get(f"{API_PREFIX}/metricas/dashboard", response_model=Response, tags=["Analítica"])
def dashboard_metricas():
    ventas = random.randint(20, 50)
    ticket_promedio = round(random.uniform(8000, 15000), 2)
    clientes_nuevos = random.randint(3, 10)
    data = {
        "ventas": ventas,
        "ticket_promedio": ticket_promedio,
        "clientes_nuevos": clientes_nuevos,
        "fecha": datetime.now().strftime("%Y-%m-%d")
    }
    print("Dashboard actualizado con métricas simuladas.")
    return Response(message="Métricas generadas", data=data)

# ============================================================
# H-12: Predicción de demanda
# ============================================================
class PrediccionInput(BaseModel):
    cepa: str
    mes: str

@app.post(f"{API_PREFIX}/demanda/predecir", response_model=Response, tags=["Analítica"])
def predecir_demanda(input: PrediccionInput):
    base = {"Syrah": 120, "Pinot Noir": 90, "Carmenere": 75, "Cabernet": 130}
    estimacion = base.get(input.cepa, random.randint(50, 100))
    ajuste = random.uniform(0.9, 1.2)
    demanda = round(estimacion * ajuste)
    print(f"Predicción: {input.cepa} en {input.mes} → {demanda} botellas estimadas")
    return Response(message="Predicción de demanda generada",
                    data={"cepa": input.cepa, "mes": input.mes, "estimado": demanda})

# ============================================================
# H-13: Etiqueta digital con huella de carbono
# ============================================================
class EtiquetaDigital(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    vino: str
    huella_carbono: float
    certificaciones: List[str]
    vigente: bool = True

db_etiquetas: List[EtiquetaDigital] = []

@app.post(f"{API_PREFIX}/etiquetas/registrar", response_model=Response, tags=["Sostenibilidad"])
def registrar_etiqueta(input: EtiquetaDigital):
    db_etiquetas.append(input)
    print(f"Etiqueta digital registrada para {input.vino}")
    return Response(message="Etiqueta registrada", data=input.dict())

@app.get(f"{API_PREFIX}/etiquetas/ver", response_model=Response, tags=["Sostenibilidad"])
def ver_etiqueta(vino: str):
    etiqueta = next((e for e in db_etiquetas if e.vino.lower() == vino.lower()), None)
    if not etiqueta:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    if not etiqueta.vigente:
        return Response(message="Etiqueta expirada", data=etiqueta.dict())
    return Response(message="Etiqueta encontrada", data=etiqueta.dict())

# ============================================================
# H-14: Campañas de donación responsable
# ============================================================
class DonacionInput(BaseModel):
    ong: str
    porcentaje: float  # 0.02 = 2%
    monto_compra: float

db_donaciones: List[dict] = []

@app.post(f"{API_PREFIX}/donaciones/aportar", response_model=Response, tags=["Responsabilidad Social"])
def registrar_donacion(input: DonacionInput, user: User = Depends(get_current_user)):
    aporte = round(input.monto_compra * input.porcentaje, 2)
    registro = {
        "usuario": user.email,
        "ong": input.ong,
        "aporte": aporte,
        "fecha": datetime.now()
    }
    db_donaciones.append(registro)
    print(f"{user.email} aportó ${aporte} a {input.ong}")
    return Response(message="Donación registrada", data=registro)

# ============================================================
# H-15: Visitas virtuales a viñedos (AR/VR)
# ============================================================
class VisitaVirtual(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    bodega: str
    url_experiencia: str
    duracion_min: int
    compatible_webar: bool = True

db_visitas: List[VisitaVirtual] = []

@app.post(f"{API_PREFIX}/visitas/registrar", response_model=Response, tags=["Experiencias"])
def registrar_visita(input: VisitaVirtual):
    db_visitas.append(input)
    print(f"Visita virtual registrada: {input.bodega}")
    return Response(message="Visita registrada", data=input.dict())

@app.get(f"{API_PREFIX}/visitas/listar", response_model=Response, tags=["Experiencias"])
def listar_visitas():
    return Response(message="Listado de experiencias virtuales", data=[v.dict() for v in db_visitas])

# ============================================================
# H-16: Maridajes interactivos en etiqueta
# ============================================================
class MaridajeInteractivo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    vino: str
    sugerencias: List[str]
    disponible_offline: bool = False

db_maridajes: List[MaridajeInteractivo] = []

@app.post(f"{API_PREFIX}/maridajes/registrar", response_model=Response, tags=["Maridajes"])
def registrar_maridaje(input: MaridajeInteractivo):
    db_maridajes.append(input)
    print(f"Maridaje interactivo registrado para {input.vino}")
    return Response(message="Maridaje registrado", data=input.dict())

@app.get(f"{API_PREFIX}/maridajes/ver", response_model=Response, tags=["Maridajes"])
def ver_maridaje(vino: str):
    maridaje = next((m for m in db_maridajes if m.vino.lower() == vino.lower()), None)
    if not maridaje:
        raise HTTPException(status_code=404, detail="Maridaje no encontrado")
    return Response(message="Maridaje encontrado", data=maridaje.dict())

# ============================================================
# FIN DEL ARCHIVO
# ============================================================
print("API Viña Urbana lista. Ejecuta: uvicorn main_vinaurbana:app --reload")
