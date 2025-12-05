from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
import hashlib
import random

# ============================================================
# CONFIGURACIÓN GENERAL - VIÑA URBANA
# ============================================================

API_PREFIX = "/api/vinaurbana"

app = FastAPI(
    title="API Viña Urbana",
    description="Plataforma boutique de vinos - Proyecto Viña Urbana",
    version="1.1.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/sesion/inicio")

# CORS para que puedas pegarle desde cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: pon tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELOS BASE / RESPUESTA
# ============================================================

class Response(BaseModel):
    statusCode: int = 200
    message: str = "OK"
    data: Optional[dict | list] = None


# --- Autenticación / Usuarios ---

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


# --- Catálogo / Productos usados por los HTML ---

class Producto(BaseModel):
    id: str
    nombre: str
    tipo: str        # tinto, blanco, rosado, espumante
    cepa: str
    origen: str
    precio: int
    imagen: Optional[str] = None


class Oferta(BaseModel):
    id: str
    producto_id: str
    nombre: str
    tipo: str
    precio: int
    original: int
    descuento: int
    club_only: bool = False
    imagen: Optional[str] = None


class Tienda(BaseModel):
    id: str
    comuna: str
    nombre: str
    direccion: str
    horario: str
    telefono: str
    servicios: List[str]
    imagen: Optional[str] = None
    maps_url: Optional[str] = None


# ============================================================
# FUNCIONES DE SEGURIDAD (SIN JWT, TOKEN SIMPLE)
# ============================================================

def hashear_contraseña(password: str) -> str:
    """Hash simple para evitar problemas con bcrypt/passlib en tu entorno."""
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
db_membresias: List[dict] = []
db_notificaciones: List[dict] = []
db_stock: List[dict] = []
db_pedidos: List["Pedido"] = []
db_tickets: List[dict] = []
db_marketplace: List[dict] = []
db_alianzas: List[dict] = []
db_etiquetas: List["EtiquetaDigital"] = []
db_donaciones: List[dict] = []
db_visitas: List["VisitaVirtual"] = []
db_maridajes: List["MaridajeInteractivo"] = []

# Catálogo principal alineado con los HTML (p01–p12 + rosados + espumantes)
CATALOGO: List[Producto] = [
    # Reserva Especial tintos / blancos (p01–p12)
    Producto(
        id="p01",
        nombre="Reserva Especial 2016",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle del Maipo",
        precio=9690,
        imagen="https://images.pexels.com/photos/2149147/pexels-photo-2149147.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p02",
        nombre="Reserva Especial 2017",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Casablanca",
        precio=10390,
        imagen="https://images.pexels.com/photos/2149164/pexels-photo-2149164.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p03",
        nombre="Reserva Especial 2018",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle de Colchagua",
        precio=11090,
        imagen="https://images.pexels.com/photos/2149151/pexels-photo-2149151.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p04",
        nombre="Reserva Especial 2019",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Casablanca",
        precio=11790,
        imagen="https://images.pexels.com/photos/1407850/pexels-photo-1407850.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p05",
        nombre="Reserva Especial 2020",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle del Maipo",
        precio=12490,
        imagen="https://images.pexels.com/photos/2149161/pexels-photo-2149161.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p06",
        nombre="Reserva Especial 2021",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Leyda",
        precio=13190,
        imagen="https://images.pexels.com/photos/5531554/pexels-photo-5531554.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p07",
        nombre="Reserva Especial 2022",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle del Maipo",
        precio=13890,
        imagen="https://images.pexels.com/photos/2149148/pexels-photo-2149148.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p08",
        nombre="Reserva Especial 2023",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Casablanca",
        precio=14590,
        imagen="https://images.pexels.com/photos/1407855/pexels-photo-1407855.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p09",
        nombre="Reserva Especial 2024",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle del Maipo",
        precio=15290,
        imagen="https://images.pexels.com/photos/1407857/pexels-photo-1407857.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p10",
        nombre="Reserva Especial 2025",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Casablanca",
        precio=15990,
        imagen="https://images.pexels.com/photos/2149144/pexels-photo-2149144.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p11",
        nombre="Reserva Especial 2026",
        tipo="tinto",
        cepa="Cabernet Sauvignon",
        origen="Valle del Maipo",
        precio=16690,
        imagen="https://images.pexels.com/photos/2149146/pexels-photo-2149146.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="p12",
        nombre="Reserva Especial 2027",
        tipo="blanco",
        cepa="Sauvignon Blanc",
        origen="Valle de Casablanca",
        precio=17390,
        imagen="https://images.pexels.com/photos/5946922/pexels-photo-5946922.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    # Rosados usados en rosados.html
    Producto(
        id="ros-01",
        nombre="Rosé Costa Fresca",
        tipo="rosado",
        cepa="Blend rosé",
        origen="Valle de Casablanca",
        precio=8990,
        imagen="https://images.pexels.com/photos/5947020/pexels-photo-5947020.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="ros-02",
        nombre="Rosé de Syrah",
        tipo="rosado",
        cepa="Syrah",
        origen="Valle de Colchagua",
        precio=9490,
        imagen="https://images.pexels.com/photos/5947024/pexels-photo-5947024.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="ros-03",
        nombre="Rosé Tarde de Verano",
        tipo="rosado",
        cepa="Grenache",
        origen="Valle del Maule",
        precio=7990,
        imagen="https://images.pexels.com/photos/5947026/pexels-photo-5947026.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    # Espumantes de espumantes.html (aprox)
    Producto(
        id="esp-01",
        nombre="Espumante Brut Tradición",
        tipo="espumante",
        cepa="Blend",
        origen="Valle de Limarí",
        precio=10990,
        imagen="https://images.pexels.com/photos/5947023/pexels-photo-5947023.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="esp-02",
        nombre="Espumante Rosé",
        tipo="espumante",
        cepa="Pinot Noir",
        origen="Valle de Casablanca",
        precio=11990,
        imagen="https://images.pexels.com/photos/5947021/pexels-photo-5947021.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Producto(
        id="esp-03",
        nombre="Espumante Brut Nature",
        tipo="espumante",
        cepa="Chardonnay",
        origen="Valle de Casablanca",
        precio=12990,
        imagen="https://images.pexels.com/photos/5947023/pexels-photo-5947023.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
]

# Ofertas alineadas con ofertas.html
OFERTAS: List[Oferta] = [
    Oferta(
        id="of-01",
        producto_id="p01",
        nombre="Pack 3x Cabernet Reserva",
        tipo="tinto",
        precio=19990,
        original=26970,
        descuento=26,
        club_only=False,
        imagen="https://images.pexels.com/photos/2149149/pexels-photo-2149149.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Oferta(
        id="of-02",
        producto_id="p02",
        nombre="Caja 6x Sauvignon Blanc Costa",
        tipo="blanco",
        precio=27990,
        original=35940,
        descuento=22,
        club_only=True,
        imagen="https://images.pexels.com/photos/2903166/pexels-photo-2903166.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Oferta(
        id="of-03",
        producto_id="ros-01",
        nombre="Dúo Rosé + Espumante",
        tipo="rosado",
        precio=14990,
        original=18980,
        descuento=21,
        club_only=False,
        imagen="https://images.pexels.com/photos/5947021/pexels-photo-5947021.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
    Oferta(
        id="of-04",
        producto_id="esp-01",
        nombre="Pack 4x Espumante Brut",
        tipo="espumante",
        precio=25990,
        original=33960,
        descuento=24,
        club_only=True,
        imagen="https://images.pexels.com/photos/5947023/pexels-photo-5947023.jpeg?auto=compress&cs=tinysrgb&w=1200",
    ),
]

# Tiendas alineadas con tiendas.html
TIENDAS: List[Tienda] = [
    Tienda(
        id="st-providencia",
        comuna="Providencia",
        nombre="Viña Urbana Providencia",
        direccion="Av. Providencia 1234, Providencia, Santiago",
        horario="Lunes a sábado 11:00–21:00",
        telefono="+56 2 2222 1111",
        servicios=[
            "Sala de degustación",
            "Retiro de compras online",
            "Asesoría de sommelier",
        ],
        imagen="https://images.pexels.com/photos/941864/pexels-photo-941864.jpeg?auto=compress&cs=tinysrgb&w=1200",
        maps_url="https://maps.google.com/?q=Providencia+1234+Santiago",
    ),
    Tienda(
        id="st-lascondes",
        comuna="Las Condes",
        nombre="Viña Urbana Las Condes",
        direccion="Av. Apoquindo 3456, Las Condes, Santiago",
        horario="Lunes a domingo 11:00–22:00",
        telefono="+56 2 2333 2222",
        servicios=[
            "Eventos privados y catas",
            "Estacionamiento clientes",
            "Club pick-up (membresía)",
        ],
        imagen="https://images.pexels.com/photos/1407858/pexels-photo-1407858.jpeg?auto=compress&cs=tinysrgb&w=1200",
        maps_url="https://maps.google.com/?q=Apoquindo+3456+Santiago",
    ),
    Tienda(
        id="st-nunoa",
        comuna="Ñuñoa",
        nombre="Viña Urbana Ñuñoa",
        direccion="Av. Irarrázaval 789, Ñuñoa, Santiago",
        horario="Martes a domingo 12:00–21:00",
        telefono="+56 2 2444 3333",
        servicios=[
            "Bar de vinos por copa",
            "Retiro de pedidos web",
            "Talleres y charlas (demo)",
        ],
        imagen="https://images.pexels.com/photos/2147855/pexels-photo-2147855.jpeg?auto=compress&cs=tinysrgb&w=1200",
        maps_url="https://maps.google.com/?q=Irarrázaval+789+Santiago",
    ),
]

# Stock mínimo de ejemplo para H-05
db_stock.append({"nombre": "Cabernet Sauvignon Reserva", "stock": 3})


# ============================================================
# HELPERS
# ============================================================

def get_user_by_email(email: str) -> Optional[User]:
    return next((u for u in db_users if u.email.lower() == email.lower()), None)


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

    if not token.startswith("token-"):
        raise cred_exception

    email = token[len("token-"):]
    user = get_user_by_email(email)

    if user is None:
        raise cred_exception

    return user


# ============================================================
# ENDPOINTS GENERALES
# ============================================================

@app.get("/")
def root():
    return {
        "mensaje": "API Viña Urbana operativa. Visita /docs para explorar los endpoints.",
        "version": "1.1.0",
    }


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
    # OAuth2PasswordRequestForm usa "username" para el correo
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
# + endpoints de catálogo reales para los HTML
# ============================================================

class CatalogFilter(BaseModel):
    tipo: Optional[str] = None       # tinto, blanco, rosado, espumante
    cepa: Optional[str] = None
    origen: Optional[str] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None


@app.get(f"{API_PREFIX}/catalogo/listar", response_model=Response, tags=["Catálogo"])
def listar_catalogo():
    """Devuelve todo el catálogo que usan los HTML."""
    return Response(data=[p.dict() for p in CATALOGO], message="Catálogo completo")


@app.get(f"{API_PREFIX}/catalogo/producto", response_model=Response, tags=["Catálogo"])
def obtener_producto(producto_id: str):
    prod = next((p for p in CATALOGO if p.id == producto_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(data=prod.dict(), message="Producto encontrado")


@app.get(f"{API_PREFIX}/catalogo/filtrar", response_model=Response, tags=["Catálogo"])
def filtrar_catalogo(filtros: CatalogFilter = Depends()):
    print(f"Aplicando filtros: {filtros}")
    filtrados: List[Producto] = []

    for p in CATALOGO:
        if filtros.tipo and filtros.tipo.lower() != p.tipo.lower():
            continue
        if filtros.cepa and filtros.cepa.lower() not in p.cepa.lower():
            continue
        if filtros.origen and filtros.origen.lower() not in p.origen.lower():
            continue
        if filtros.precio_min is not None and p.precio < filtros.precio_min:
            continue
        if filtros.precio_max is not None and p.precio > filtros.precio_max:
            continue
        filtrados.append(p)

    return Response(data=[f.dict() for f in filtrados], message="Resultados del filtro")


# ============================================================
# ENDPOINTS EXTRA FRONT: OFERTAS, TIENDAS
# ============================================================

@app.get(f"{API_PREFIX}/ofertas", response_model=Response, tags=["Catálogo"])
def listar_ofertas():
    """Ofertas alineadas con ofertas.html"""
    return Response(
        data=[o.dict() for o in OFERTAS],
        message="Ofertas activas",
    )


@app.get(f"{API_PREFIX}/tiendas", response_model=Response, tags=["Tiendas"])
def listar_tiendas(comuna: Optional[str] = None):
    """Tiendas físicas (Providencia, Las Condes, Ñuñoa)."""
    if comuna:
        filtradas = [t for t in TIENDAS if t.comuna.lower() == comuna.lower()]
        return Response(data=[t.dict() for t in filtradas], message="Tiendas filtradas")
    return Response(data=[t.dict() for t in TIENDAS], message="Tiendas disponibles")


# ============================================================
# H-03: Membresía con beneficios
# ============================================================

class MembresiaInput(BaseModel):
    tipo: str  # Silver, Gold, etc.
    activa: bool = True


@app.post(f"{API_PREFIX}/membresias/activar", response_model=Response, tags=["Membresías"])
def activar_membresia(input: MembresiaInput, user: User = Depends(get_current_user)):
    registro = {
        "usuario": user.email,
        "tipo": input.tipo,
        "activa": input.activa,
        "fecha": datetime.now(),
    }
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
    registro = {
        "usuario": user.email,
        "canal": input.canal,
        "mensaje": input.mensaje,
        "horario_inicio": input.horario_inicio,
        "horario_fin": input.horario_fin,
        "fecha": datetime.now(),
    }
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


@app.post(f"{API_PREFIX}/pedidos/crear", response_model=Pedido, tags=["Pedidos"])
def crear_pedido(user: User = Depends(get_current_user)):
    pedido = Pedido(
        usuario=user.email,
        estado="Preparando",
        tracking=f"TRK-{random.randint(1000, 9999)}",
    )
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
    return Response(
        data={"id": str(pedido.id), "estado": pedido.estado, "tracking": pedido.tracking},
        message="Estado actualizado",
    )


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
        "queso": "Carmenere",
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


@app.post(f"{API_PREFIX}/soporte/ticket", response_model=Response, tags=["Atención Cliente"])
def crear_ticket(input: TicketInput, user: User = Depends(get_current_user)):
    tiempo = {"email": "24h", "whatsapp": "5min", "telefono": "10min"}
    registro = {
        "usuario": user.email,
        "canal": input.canal,
        "prioridad": input.prioridad,
        "mensaje": input.mensaje,
        "SLA": tiempo.get(input.canal, "24h"),
        "fecha": datetime.now(),
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


@app.post(f"{API_PREFIX}/marketplace/sincronizar", response_model=Response, tags=["Integraciones"])
def sincronizar_marketplace(input: MarketplaceSyncInput):
    registro = {
        "producto": input.producto,
        "stock": input.stock,
        "precio": input.precio,
        "activo": input.activo,
        "fecha": datetime.now(),
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


@app.post(f"{API_PREFIX}/alianzas/registrar", response_model=Response, tags=["Alianzas"])
def registrar_alianza(input: AlianzaInput):
    registro = {
        "restaurante": input.restaurante,
        "beneficio": input.beneficio,
        "qr_valido": input.qr_valido,
        "fecha": datetime.now(),
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
        "fecha": datetime.now().strftime("%Y-%m-%d"),
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
    return Response(
        message="Predicción de demanda generada",
        data={"cepa": input.cepa, "mes": input.mes, "estimado": demanda},
    )


# ============================================================
# H-13: Etiqueta digital con huella de carbono
# ============================================================

class EtiquetaDigital(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    vino: str
    huella_carbono: float
    certificaciones: List[str]
    vigente: bool = True


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


@app.post(f"{API_PREFIX}/donaciones/aportar", response_model=Response, tags=["Responsabilidad Social"])
def registrar_donacion(input: DonacionInput, user: User = Depends(get_current_user)):
    aporte = round(input.monto_compra * input.porcentaje, 2)
    registro = {
        "usuario": user.email,
        "ong": input.ong,
        "aporte": aporte,
        "fecha": datetime.now(),
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


@app.post(f"{API_PREFIX}/visitas/registrar", response_model=Response, tags=["Experiencias"])
def registrar_visita(input: VisitaVirtual):
    db_visitas.append(input)
    print(f"Visita virtual registrada: {input.bodega}")
    return Response(message="Visita registrada", data=input.dict())


@app.get(f"{API_PREFIX}/visitas/listar", response_model=Response, tags=["Experiencias"])
def listar_visitas():
    return Response(
        message="Listado de experiencias virtuales",
        data=[v.dict() for v in db_visitas],
    )


# ============================================================
# H-16: Maridajes interactivos en etiqueta
# ============================================================

class MaridajeInteractivo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    vino: str
    sugerencias: List[str]
    disponible_offline: bool = False


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

print("API Viña Urbana lista. Ejecuta: uvicorn main_vinaurbanafinal:app --reload")
