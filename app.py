import streamlit as st
from datetime import datetime
import math
import random
import pickle
import os

# --- CONFIGURACIÓN DE LA CIUDAD ---
CANALES_LISTA = [
    "🦾acciones", "🚘registro-vehículo", "🗒️registrar-propiedad",
    "🚗vehículo", "🏘️propiedades", "🎒inventario", "💵gestión-dinero",
    "🚔agentes", "⛓️‍💥detenciones", "💻lspd", "💬charla-pol",
    "⛽atracar", "🧰recolectar", "🪙vender", "💰blanquear", "💬charla-maf"
]

DB_FILE = "datos_ciudad.pkl"

def guardar_datos():
    """Escribe todo el estado actual en el archivo local."""
    datos = {
        "usuarios_db": st.session_state.usuarios_db,
        "historial_chat": st.session_state.historial_chat,
        "inventarios_vehiculos": st.session_state.inventarios_vehiculos,
        "inventarios_propiedades": st.session_state.inventarios_propiedades,
        "inventario_personal": st.session_state.inventario_personal,
        "banca": st.session_state.banca,
        "servicio_policia": st.session_state.servicio_policia
    }
    with open(DB_FILE, "wb") as f:
        pickle.dump(datos, f)

def cargar_datos():
    """Busca el archivo y devuelve los datos si existen."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            try:
                return pickle.load(f)
            except:
                return None
    return None

# Intentamos cargar los datos antes de inicializar la sesión
datos_cargados = cargar_datos()

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Ciudad RP - Sistema Central", layout="wide", initial_sidebar_state="expanded")

# --- INICIALIZACIÓN DE MEMORIA ---
if 'usuarios_db' not in st.session_state:
    st.session_state.usuarios_db = datos_cargados["usuarios_db"] if datos_cargados else {}

if 'historial_chat' not in st.session_state:
    st.session_state.historial_chat = datos_cargados["historial_chat"] if datos_cargados else {canal: [] for canal in CANALES_LISTA}

if 'inventarios_vehiculos' not in st.session_state:
    st.session_state.inventarios_vehiculos = datos_cargados["inventarios_vehiculos"] if datos_cargados else {}

if 'inventarios_propiedades' not in st.session_state:
    st.session_state.inventarios_propiedades = datos_cargados["inventarios_propiedades"] if datos_cargados else {}

if 'inventario_personal' not in st.session_state:
    st.session_state.inventario_personal = datos_cargados["inventario_personal"] if datos_cargados else {}

if 'banca' not in st.session_state:
    st.session_state.banca = datos_cargados["banca"] if datos_cargados else {}

if 'servicio_policia' not in st.session_state:
    st.session_state.servicio_policia = datos_cargados["servicio_policia"] if datos_cargados else {}

# Estas dos no necesitan guardarse porque dependen de la sesión actual
if 'usuario_identificado' not in st.session_state:
    st.session_state.usuario_identificado = None 
if 'canal_actual' not in st.session_state:
    st.session_state.canal_actual = "🦾acciones"

with st.sidebar.expander("🔐 SISTEMA DE ADMIN"):
    admin_password = st.text_input("Contraseña Admin", type="password")
    
    if admin_password == "rol": # <--- Tu contraseña
        st.subheader("Herramientas de Control")
        
        # --- FUNCIÓN: ELIMINAR JUGADOR ---
        st.markdown("---")
        st.write("🗑️ **Eliminar Ciudadano**")
        # Usamos un formulario para evitar que el código se ejecute solo
        with st.form("form_borrado"):
            dni_para_borrar = st.text_input("Introduce el DNI exacto")
            boton_borrar = st.form_submit_button("Confirmar Borrado")
            
            if boton_borrar:
                if dni_para_borrar in datos['ciudadanos']:
                    del datos['ciudadanos'][dni_para_borrar]
                    guardar_datos(datos)
                    st.success(f"DNI {dni_para_borrar} eliminado.")
                    st.rerun()
                else:
                    st.error("Ese DNI no existe.")

        # --- FUNCIÓN: DAR DINERO ---
        st.markdown("---")
        st.write("💰 **Inyectar Dinero (Blanco)**")
        with st.form("form_dinero"):
            dni_destino = st.text_input("DNI del ciudadano")
            monto = st.number_input("Cantidad a sumar", min_value=0, step=100)
            boton_dinero = st.form_submit_button("Enviar Dinero")
            
            if boton_dinero:
                if dni_destino in datos['ciudadanos']:
                    # Sumamos el dinero
                    datos['ciudadanos'][dni_destino]['dinero'] += monto
                    guardar_datos(datos)
                    st.success(f"Se han sumado {monto}€ al DNI {dni_destino}")
                    st.rerun()
                else:
                    st.error("DNI no encontrado.")

# --- FUNCIONES AUXILIARES ---
def asegurar_cuenta(dni):
    """Inicializa la cuenta con 500.000€ si el DNI no existe."""
    if dni not in st.session_state.banca:
        st.session_state.banca[dni] = {
            "banco": 500000,
            "efectivo": 0,
            "negro": 0
        }

# --- LÓGICA DE ENVÍO DE MENSAJES ---
def enviar_mensaje():
    nuevo_txt = st.session_state.input_usuario.strip()
    canal_actual = st.session_state.canal_actual
    rol_usuario = st.session_state.usuario_identificado['rol']
    
    if nuevo_txt:
        # RESTRICCIÓN DE ESCRITURA: Solo policía escribe en agentes y detenciones
        canales_solo_lectura_pol = ["🚔agentes", "⛓️‍💥detenciones"]
        if rol_usuario != "Policía" and canal_actual in canales_solo_lectura_pol:
            st.toast("⚠️ Tienes este canal en modo SOLO LECTURA.")
            st.session_state.input_usuario = ""
            return

        # El autor ahora es el nombre del personaje registrado
        autor = st.session_state.usuario_identificado['nombre']
        hora_actual = datetime.now()
        hora_str = hora_actual.strftime("%H:%M")
        mensaje_formateado = None
        
        # 1. COMANDO /ACTION
        if nuevo_txt.startswith("/action "):
            if canal_actual == "🦾acciones":
                accion = nuevo_txt.replace("/action ", "")
                mensaje_formateado = f"<i>* {accion} *</i>"
            else:
                st.toast("❌ El comando /action solo puede usarse en el canal de acciones.")

        # 2. COMANDOS DE VEHÍCULO
        elif nuevo_txt.startswith("/meter "):
            if canal_actual == "🚗vehículo":
                try:
                    partes = nuevo_txt.split(" ", 3)
                    mat_in, lug, obj = partes[1].upper(), partes[2].lower(), partes[3]
                    registros = st.session_state.historial_chat["🚘registro-vehículo"]
                    if any(st.session_state.usuario_identificado['nombre'] in r['msg'] and f"[`{mat_in}`]" in r['msg'] for r in registros):
                        if mat_in not in st.session_state.inventarios_vehiculos:
                            st.session_state.inventarios_vehiculos[mat_in] = {"guantera": [], "maletero": []}
                        st.session_state.inventarios_vehiculos[mat_in][lug].append(obj)
                        mensaje_formateado = f"📦 **[{mat_in}]** Has guardado **{obj}** en el **{lug}**."
                    else: st.toast(f"❌ La matrícula {mat_in} no te pertenece.")
                except: st.toast("❌ Uso: /meter [matrícula] [lugar] [objeto]")
            else: st.toast("❌ Solo en canal 🚗vehículo.")

        elif nuevo_txt.startswith("/sacar "):
            if canal_actual == "🚗vehículo":
                try:
                    partes = nuevo_txt.split(" ", 3)
                    mat_in, lug, obj = partes[1].upper(), partes[2].lower(), partes[3]
                    inv = st.session_state.inventarios_vehiculos.get(mat_in, {}).get(lug, [])
                    if obj in inv:
                        inv.remove(obj)
                        mensaje_formateado = f"📤 **[{mat_in}]** Has sacado **{obj}** del **{lug}**."
                    else: st.toast(f"❌ No hay '{obj}' en el/la {lug}.")
                except: st.toast("❌ Uso: /sacar [matrícula] [lugar] [objeto]")

        elif nuevo_txt.startswith("/revisar"):
            if canal_actual == "🚗vehículo":
                try:
                    mat_in = nuevo_txt.split(" ")[1].upper()
                    inv = st.session_state.inventarios_vehiculos.get(mat_in, {"guantera": [], "maletero": []})
                    mensaje_formateado = f"🔍 **Inventario [{mat_in}]:**\n- **Guantera:** {', '.join(inv['guantera']) or 'Vacía'}\n- **Maletero:** {', '.join(inv['maletero']) or 'Vacío'}"
                except: st.toast("❌ Uso: /revisar [matrícula]")

        # 3. COMANDOS DE PROPIEDAD
        elif nuevo_txt.startswith("/guardar "):
            if canal_actual == "🏘️propiedades":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dir_in, obj_p = partes[1], partes[2]
                    registros_p = st.session_state.historial_chat["🗒️registrar-propiedad"]
                    if any(st.session_state.usuario_identificado['nombre'] in r['msg'] and f"`{dir_in}`" in r['msg'] for r in registros_p):
                        if dir_in not in st.session_state.inventarios_propiedades: st.session_state.inventarios_propiedades[dir_in] = []
                        st.session_state.inventarios_propiedades[dir_in].append(obj_p)
                        mensaje_formateado = f"🏠 **[{dir_in}]** Has guardado **{obj_p}** en el armario."
                    else: st.toast(f"❌ No tienes esa propiedad.")
                except: st.toast("❌ Uso: /guardar [dirección] [objeto]")

        elif nuevo_txt.startswith("/retirar "):
            if canal_actual == "🏘️propiedades":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dir_in, obj_p = partes[1], partes[2]
                    inv = st.session_state.inventarios_propiedades.get(dir_in, [])
                    if obj_p in inv:
                        inv.remove(obj_p)
                        mensaje_formateado = f"🗝️ **[{dir_in}]** Has retirado **{obj_p}** del armario."
                    else: st.toast(f"❌ No se encuentra '{obj_p}' en esta propiedad.")
                except: st.toast("❌ Uso: /retirar [dirección] [objeto]")

        # 4. COMANDOS DE INVENTARIO PERSONAL
        elif nuevo_txt.startswith("/recoger "):
            if canal_actual == "🎒inventario":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dni_in, obj_i = partes[1], partes[2]
                    if dni_in not in st.session_state.inventario_personal: st.session_state.inventario_personal[dni_in] = []
                    st.session_state.inventario_personal[dni_in].append(obj_i)
                    mensaje_formateado = f"🎒 **[DNI: {dni_in}]** Has recogido **{obj_i}**."
                except: st.toast("❌ Uso: /recoger [DNI] [objeto]")

        elif nuevo_txt.startswith("/tirar "):
            if canal_actual == "🎒inventario":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dni_in, obj_i = partes[1], partes[2]
                    inv = st.session_state.inventario_personal.get(dni_in, [])
                    if obj_i in inv:
                        inv.remove(obj_i)
                        mensaje_formateado = f"🗑️ **[DNI: {dni_in}]** Has tirado/entregado **{obj_i}**."
                    else: st.toast(f"❌ No tienes '{obj_i}' en tu mochila.")
                except: st.toast("❌ Uso: /tirar [DNI] [objeto]")

        elif nuevo_txt.startswith("/mochila"):
            if canal_actual == "🎒inventario":
                try:
                    dni_in = nuevo_txt.split(" ")[1]
                    inv_p = st.session_state.inventario_personal.get(dni_in, [])
                    mensaje_formateado = f"🎒 **Mochila (DNI: {dni_in}):**\n{', '.join(inv_p) if inv_p else 'Vacía'}"
                except: st.toast("❌ Uso: /mochila [DNI]")

        # 5. COMANDOS DE DINERO
        elif nuevo_txt.startswith("/cartera"):
            if canal_actual == "💵gestión-dinero":
                try:
                    dni_in = nuevo_txt.split(" ")[1]
                    asegurar_cuenta(dni_in)
                    c = st.session_state.banca[dni_in]
                    mensaje_formateado = f"🏦 **Estado Financiero (DNI: {dni_in}):**\n- 💳 **Banco:** {c['banco']:,}€\n- 💵 **Efectivo:** {c['efectivo']:,}€\n- 💀 **Dinero Negro:** {c['negro']:,}€"
                except: st.toast("❌ Uso: /cartera [DNI]")

        elif nuevo_txt.startswith("/depositar "):
            if canal_actual == "💵gestión-dinero":
                try:
                    partes = nuevo_txt.split(" ")
                    dni_in, cant = partes[1], int(partes[2])
                    asegurar_cuenta(dni_in)
                    if st.session_state.banca[dni_in]['efectivo'] >= cant:
                        st.session_state.banca[dni_in]['efectivo'] -= cant
                        st.session_state.banca[dni_in]['banco'] += cant
                        mensaje_formateado = f"🏧 **Cajero:** Has depositado **{cant:,}€** en tu cuenta bancaria."
                    else: st.toast("❌ No tienes suficiente efectivo.")
                except: st.toast("❌ Uso: /depositar [DNI] [cantidad]")

        elif nuevo_txt.startswith("/retirar-banco "):
            if canal_actual == "💵gestión-dinero":
                try:
                    partes = nuevo_txt.split(" ")
                    dni_in, cant = partes[1], int(partes[2])
                    asegurar_cuenta(dni_in)
                    if st.session_state.banca[dni_in]['banco'] >= cant:
                        st.session_state.banca[dni_in]['banco'] -= cant
                        st.session_state.banca[dni_in]['efectivo'] += cant
                        mensaje_formateado = f"🏧 **Cajero:** Has retirado **{cant:,}€** de tu cuenta bancaria."
                    else: st.toast("❌ Saldo bancario insuficiente.")
                except: st.toast("❌ Uso: /retirar-banco [DNI] [cantidad]")

        elif nuevo_txt.startswith("/pagar "):
            if canal_actual == "💵gestión-dinero":
                try:
                    partes = nuevo_txt.split(" ")
                    dni_orig, dni_dest, cant = partes[1], partes[2], int(partes[3])
                    asegurar_cuenta(dni_orig)
                    asegurar_cuenta(dni_dest)
                    if st.session_state.banca[dni_orig]['efectivo'] >= cant:
                        st.session_state.banca[dni_orig]['efectivo'] -= cant
                        st.session_state.banca[dni_dest]['efectivo'] += cant
                        mensaje_formateado = f"💸 **Pago:** El DNI {dni_orig} ha entregado **{cant:,}€** en mano al DNI {dni_dest}."
                    else: st.toast("❌ No tienes suficiente efectivo para pagar.")
                except: st.toast("❌ Uso: /pagar [DNI_Origen] [DNI_Destino] [cantidad]")

        # 6. COMANDOS DE AGENTES (SERVICIO)
        elif nuevo_txt.startswith("/entrar-servicio "):
            if canal_actual == "🚔agentes":
                try:
                    dni_in = nuevo_txt.split(" ")[1]
                    if dni_in not in st.session_state.servicio_policia:
                        st.session_state.servicio_policia[dni_in] = datetime.now()
                        mensaje_formateado = f"🔵 **SERVICIO:** El agente con DNI **{dni_in}** ha entrado en servicio."
                    else:
                        st.toast("❌ Ya estás en servicio.")
                except: st.toast("❌ Uso: /entrar-servicio [DNI]")

        elif nuevo_txt.startswith("/salir-servicio "):
            if canal_actual == "🚔agentes":
                try:
                    dni_in = nuevo_txt.split(" ")[1]
                    if dni_in in st.session_state.servicio_policia:
                        entrada = st.session_state.servicio_policia.pop(dni_in)
                        salida = datetime.now()
                        diferencia = salida - entrada
                        minutos_totales = diferencia.total_seconds() / 60
                        periodos_20min = minutos_totales / 20
                        salario = math.floor(periodos_20min * 1000)
                        asegurar_cuenta(dni_in)
                        st.session_state.banca[dni_in]['banco'] += salario
                        mensaje_formateado = f"🔴 **SERVICIO:** El agente **{dni_in}** sale de servicio.\n- **Tiempo:** {int(minutos_totales)} min.\n- **Sueldo ganado:** {salario:,}€ (Ingresados en banco)."
                    else:
                        st.toast("❌ No estaba en servicio.")
                except: st.toast("❌ Uso: /salir-servicio [DNI]")

        # 7. COMANDOS DE DETENCIONES (POLICÍA)
        elif nuevo_txt.startswith("/cachear "):
            if canal_actual == "⛓️‍💥detenciones":
                try:
                    dni_in = nuevo_txt.split(" ")[1]
                    inv = st.session_state.inventario_personal.get(dni_in, [])
                    mensaje_formateado = f"👮 **CACHEO (DNI: {dni_in}):**\n- **Objetos:** {', '.join(inv) if inv else 'Nada de valor.'}"
                except: st.toast("❌ Uso: /cachear [DNI]")

        elif nuevo_txt.startswith("/inspeccionar "):
            if canal_actual == "⛓️‍💥detenciones":
                try:
                    mat_in = nuevo_txt.split(" ")[1].upper()
                    inv = st.session_state.inventarios_vehiculos.get(mat_in, {"guantera": [], "maletero": []})
                    mensaje_formateado = f"👮 **INSPECCIÓN (Matrícula: {mat_in}):**\n- **Guantera:** {', '.join(inv['guantera']) or 'Vacía'}\n- **Maletero:** {', '.join(inv['maletero']) or 'Vacío'}"
                except: st.toast("❌ Uso: /inspeccionar [Matrícula]")

        elif nuevo_txt.startswith("/confiscar-persona "):
            if canal_actual == "⛓️‍💥detenciones":
                try:
                    partes = nuevo_txt.split(" ", 3)
                    dni_suj, dni_pol, obj = partes[1], partes[2], partes[3]
                    inv_suj = st.session_state.inventario_personal.get(dni_suj, [])
                    if obj in inv_suj:
                        inv_suj.remove(obj)
                        if dni_pol not in st.session_state.inventario_personal: st.session_state.inventario_personal[dni_pol] = []
                        st.session_state.inventario_personal[dni_pol].append(obj)
                        mensaje_formateado = f"⚠️ **CONFISCACIÓN:** El agente **{dni_pol}** ha confiscado **{obj}** al civil **{dni_suj}**."
                    else: st.toast(f"❌ El sujeto no tiene '{obj}'.")
                except: st.toast("❌ Uso: /confiscar-persona [DNI_Sujeto] [DNI_Agente] [Objeto]")

        elif nuevo_txt.startswith("/confiscar-vehiculo "):
            if canal_actual == "⛓️‍💥detenciones":
                try:
                    partes = nuevo_txt.split(" ", 4)
                    mat, lug, dni_pol, obj = partes[1].upper(), partes[2].lower(), partes[3], partes[4]
                    inv_v = st.session_state.inventarios_vehiculos.get(mat, {}).get(lug, [])
                    if obj in inv_v:
                        inv_v.remove(obj)
                        if dni_pol not in st.session_state.inventario_personal: st.session_state.inventario_personal[dni_pol] = []
                        st.session_state.inventario_personal[dni_pol].append(obj)
                        mensaje_formateado = f"⚠️ **CONFISCACIÓN:** El agente **{dni_pol}** ha confiscado **{obj}** del **{lug}** del vehículo **{mat}**."
                    else: st.toast(f"❌ No hay '{obj}' en el {lug}.")
                except: st.toast("❌ Uso: /confiscar-vehiculo [Matrícula] [Lugar] [DNI_Agente] [Objeto]")

        elif nuevo_txt.startswith("/detener "):
            if canal_actual == "⛓️‍💥detenciones":
                try:
                    partes = nuevo_txt.split(" ", 3)
                    dni_suj, tiempo, motivo = partes[1], partes[2], partes[3]
                    mensaje_formateado = f"⛓️ **ARRESTO OFICIAL:**\n- **Sujeto:** {dni_suj}\n- **Condena:** {tiempo} meses\n- **Motivo:** {motivo}"
                except: st.toast("❌ Uso: /detener [DNI] [Tiempo] [Motivo]")

        # 8. COMANDO /ATRACAR (MAFIA)
        elif nuevo_txt.startswith("/atracar "):
            if canal_actual == "⛽atracar":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dni_atr, lugar = partes[1], partes[2].lower()
                    config_atraco = {
                        "supermercado": {"exito": 80, "min": 2000, "max": 5000},
                        "gasolinera": {"exito": 70, "min": 5000, "max": 10000},
                        "banco": {"exito": 40, "min": 50000, "max": 150000}
                    }
                    if lugar in config_atraco:
                        asegurar_cuenta(dni_atr)
                        suerte = random.randint(1, 100)
                        conf = config_atraco[lugar]
                        if suerte <= conf["exito"]:
                            botin = random.randint(conf["min"], conf["max"])
                            st.session_state.banca[dni_atr]["negro"] += botin
                            mensaje_formateado = f"💰 **ATRACO LOGRADO:** El DNI {dni_atr} ha atracado el/la **{lugar}** con éxito.\n- **Botín:** {botin:,}€ (Dinero Negro)."
                        else:
                            mensaje_formateado = f"🚨 **ATRACO FALLIDO:** El DNI {dni_atr} ha fallado el atraco en **{lugar}**. ¡La policía ha sido alertada!"
                            st.session_state.historial_chat["💬charla-pol"].append({
                                "autor": "CENTRALITA 112", "hora": hora_str,
                                "msg": f"📢 **ALERTA:** Salto de alarma en **{lugar.upper()}**. Posible autor DNI: {dni_atr}."
                            })
                    else:
                        st.toast("❌ Lugares válidos: supermercado, gasolinera, banco.")
                except: st.toast("❌ Uso: /atracar [DNI] [lugar]")
            else:
                st.toast("❌ Este comando solo funciona en #⛽atracar.")

        # 9. COMANDO /RECOLECTAR (MAFIA)
        elif nuevo_txt.startswith("/recolectar "):
            if canal_actual == "🧰recolectar":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dni_rec, tipo_droga = partes[1], partes[2].lower()
                    config_recolecta = {
                        "marihuana": {"exito": 90, "min": 5, "max": 15, "item": "Cogollo de Marihuana"},
                        "cocaina": {"exito": 70, "min": 2, "max": 8, "item": "Polvo Blanco"},
                        "metanfetamina": {"exito": 60, "min": 1, "max": 5, "item": "Cristal Azul"}
                    }
                    if tipo_droga in config_recolecta:
                        conf = config_recolecta[tipo_droga]
                        suerte = random.randint(1, 100)
                        if suerte <= conf["exito"]:
                            cantidad = random.randint(conf["min"], conf["max"])
                            if dni_rec not in st.session_state.inventario_personal: 
                                st.session_state.inventario_personal[dni_rec] = []
                            for _ in range(cantidad):
                                st.session_state.inventario_personal[dni_rec].append(conf["item"])
                            mensaje_formateado = f"🌿 **RECOLECCIÓN:** El DNI {dni_rec} ha recolectado **{cantidad}x {conf['item']}**."
                        else:
                            mensaje_formateado = f"🥀 **FALLO:** El DNI {dni_rec} ha intentado recolectar **{tipo_droga}** pero la cosecha se ha echado a perder."
                    else:
                        st.toast("❌ Drogas válidas: marihuana, cocaina, metanfetamina.")
                except: st.toast("❌ Uso: /recolectar [DNI] [tipo]")
            else:
                st.toast("❌ Este comando solo funciona en #🧰recolectar.")

        # 10. COMANDO /VENDER (MAFIA)
        elif nuevo_txt.startswith("/vender "):
            if canal_actual == "🪙vender":
                try:
                    partes = nuevo_txt.split(" ", 2)
                    dni_ven, tipo_droga = partes[1], partes[2].lower()
                    config_venta = {
                        "marihuana": {"item": "Cogollo de Marihuana", "precio": 200, "riesgo": 15},
                        "cocaina": {"item": "Polvo Blanco", "precio": 800, "riesgo": 30},
                        "metanfetamina": {"item": "Cristal Azul", "precio": 1200, "riesgo": 40}
                    }
                    if tipo_droga in config_venta:
                        conf = config_venta[tipo_droga]
                        inv = st.session_state.inventario_personal.get(dni_ven, [])
                        cantidad_poseida = inv.count(conf["item"])
                        if cantidad_poseida > 0:
                            asegurar_cuenta(dni_ven)
                            suerte = random.randint(1, 100)
                            if suerte > conf["riesgo"]:
                                st.session_state.inventario_personal[dni_ven] = [i for i in inv if i != conf["item"]]
                                pago_total = cantidad_poseida * conf["precio"]
                                st.session_state.banca[dni_ven]["negro"] += pago_total
                                mensaje_formateado = f"🤝 **TRATO CERRADO:** El DNI {dni_ven} ha vendido **{cantidad_poseida}x {conf['item']}**.\n- **Ganancia:** {pago_total:,}€ (Dinero Negro)."
                            else:
                                mensaje_formateado = f"🚔 **¡EMBOSCADA!:** Un civil ha llamado a la policía mientras el DNI {dni_ven} intentaba vender **{tipo_droga}**."
                                st.session_state.historial_chat["💬charla-pol"].append({
                                    "autor": "CENTRALITA 112", "hora": hora_str,
                                    "msg": f"📢 **AVISO CIUDADANO:** Sospechoso vendiendo sustancias ilícitas (**{tipo_droga}**) avistado. DNI: {dni_ven}."
                                })
                        else: st.toast(f"❌ No tienes '{conf['item']}' en tu mochila.")
                except: st.toast("❌ Uso: /vender [DNI] [tipo]")

        # 11. COMANDO /BLANQUEAR (MAFIA)
        elif nuevo_txt.startswith("/blanquear "):
            if canal_actual == "💰blanquear":
                try:
                    partes = nuevo_txt.split(" ")
                    dni_blan, cant_blan = partes[1], int(partes[2])
                    asegurar_cuenta(dni_blan)
                    if st.session_state.banca[dni_blan]['negro'] >= cant_blan:
                        comision = math.floor(cant_blan * 0.20)
                        limpio = cant_blan - comision
                        st.session_state.banca[dni_blan]['negro'] -= cant_blan
                        st.session_state.banca[dni_blan]['banco'] += limpio
                        mensaje_formateado = (f"🧼 **BLANQUEO COMPLETADO:** DNI {dni_blan} lavó dinero.\n- **Total:** {cant_blan:,}€ (Negro)\n- **Limpio:** {limpio:,}€")
                    else: st.toast("❌ No tienes suficiente dinero negro.")
                except: st.toast("❌ Uso: /blanquear [DNI] [cantidad]")

        else: mensaje_formateado = nuevo_txt

        # --- GUARDADO FINAL ---
        if mensaje_formateado:
            st.session_state.historial_chat[canal_actual].append({
                "autor": autor, "hora": hora_str, "msg": mensaje_formateado
            })
            # FORZAR PERSISTENCIA (Punto 4)
            guardar_datos()
        
        st.session_state.input_usuario = ""
# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #313338; color: #ffffff; }
    .stSidebar { background-color: #2b2d31 !important; }
    .chat-bubble { background-color: #383a40; padding: 8px 15px; border-radius: 5px; margin-bottom: 5px; }
    .user-name { font-weight: bold; color: #00a8fc; }
    .timestamp { font-size: 0.7rem; color: #949ba4; margin-left: 10px; }
    .role-header { font-size: 0.75rem; font-weight: bold; color: #949ba4; text-transform: uppercase; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #4e5058; padding-bottom: 2px; }
    .member-item { font-size: 0.85rem; color: #dbdee1; margin-left: 5px; padding: 2px 0; }
    .empty-role { font-size: 0.8rem; color: #4e5058; font-style: italic; margin-left: 10px; }
    .login-container { max-width: 400px; margin: 0 auto; padding: 20px; background: #2b2d31; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICACIÓN ---
if st.session_state.usuario_identificado is None:
    st.title("🏙️ Bienvenido a Ciudad Virtual RP")
    
    tab_login, tab_register = st.tabs(["🔑 Iniciar Sesión", "📝 Registro de Ciudadano"])
    
    with tab_login:
        with st.form("form_login"):
            dni_log = st.text_input("Introduce tu DNI")
            submit_log = st.form_submit_button("Entrar a la Ciudad")
            if submit_log:
                if dni_log in st.session_state.usuarios_db:
                    st.session_state.usuario_identificado = st.session_state.usuarios_db[dni_log]
                    st.success(f"Bienvenido de nuevo, {st.session_state.usuario_identificado['nombre']}")
                    st.rerun()
                else:
                    st.error("DNI no encontrado. Por favor, regístrate.")
    
    with tab_register:
        with st.form("form_reg"):
            st.info("Completa tus datos para obtener tu DNI y acceso.")
            nombre_reg = st.text_input("Nombre del Personaje")
            edad_reg = st.number_input("Edad", min_value=18, max_value=99, value=25)
            proc_reg = st.text_input("Procedencia (Ciudad/País)")
            rol_reg = st.selectbox("Selecciona tu Rol Principal", ["Civil", "Policía", "Mafia", "Médico", "Mecánico"])
            
            submit_reg = st.form_submit_button("Registrarse")
            
            if submit_reg:
                if nombre_reg and proc_reg:
                    # Generar DNI aleatorio de 5 cifras
                    nuevo_dni = str(random.randint(10000, 99999))
                    # Guardar en "base de datos"
                    st.session_state.usuarios_db[nuevo_dni] = {
                        "nombre": nombre_reg,
                        "edad": edad_reg,
                        "procedencia": proc_reg,
                        "rol": rol_reg,
                        "dni": nuevo_dni
                    }
                    # Inicializar su cuenta bancaria
                    asegurar_cuenta(nuevo_dni)
                    
                    # --- GUARDADO PERSISTENTE ---
                    guardar_datos()
                    
                    st.balloons()
                    st.success(f"✅ ¡Registro completado!")
                    st.warning(f"TU NÚMERO DE DNI ES: {nuevo_dni}")
                    st.info("Usa este número para iniciar sesión ahora.")
                else:
                    st.error("Por favor, rellena todos los campos.")
    st.stop() # No mostrar el resto de la app hasta loguearse

# --- 1. BARRA LATERAL ---
with st.sidebar:
    st.title("🏙️ Ciudad Virtual")
    st.markdown(f"👤 **{st.session_state.usuario_identificado['nombre']}**")
    st.caption(f"DNI: {st.session_state.usuario_identificado['dni']} | Rol: {st.session_state.usuario_identificado['rol']}")
    
    if st.button("🚪 Cerrar Sesión"):
        # Guardamos antes de salir para asegurar inventarios
        guardar_datos()
        st.session_state.usuario_identificado = None
        st.rerun()
        
    st.markdown("---")
    menu = {
        "🏙️ CIUDAD": ["🦾acciones", "🚘registro-vehículo", "🗒️registrar-propiedad"],
        "💳 PERFIL": ["🚗vehículo", "🏘️propiedades", "🎒inventario", "💵gestión-dinero"],
        "🔫 POLICIA": ["🚔agentes", "⛓️‍💥detenciones", "💻lspd", "💬charla-pol"],
        "🚨 MAFIA": ["⛽atracar", "🧰recolectar", "🪙vender", "💰blanquear", "💬charla-maf"]
    }
    for cat, icons in menu.items():
        st.markdown(f"### {cat}")
        for c in icons:
            if st.button(f"#️⃣ {c}"): st.session_state.canal_actual = c

# --- 2. CUERPO CENTRAL ---
col_chat, col_members = st.columns([4, 1])

with col_chat:
    st.subheader(f"#️⃣ {st.session_state.canal_actual}")
    
    if st.session_state.canal_actual == "🚘registro-vehículo":
        st.markdown("### 📝 Registro Vehículo")
        with st.form("form_v", clear_on_submit=True):
            col1, col2 = st.columns(2)
            mod = col1.text_input("Modelo")
            mat = col2.text_input("Matrícula").upper()
            prop = st.text_input("Propietario (Nombre)", value=st.session_state.usuario_identificado['nombre'])
            if st.form_submit_button("Registrar"):
                if mod and mat and prop:
                    st.session_state.historial_chat["🚘registro-vehículo"].append({
                        "autor": "SISTEMA DGT", "hora": datetime.now().strftime("%H:%M"),
                        "msg": f"✅ **NUEVO REGISTRO:** {mod} [`{mat}`] - Propietario: **{prop}**"
                    })
                    # Guardar registro de vehículo
                    guardar_datos()
                    st.rerun()

    elif st.session_state.canal_actual == "🗒️registrar-propiedad":
        st.markdown("### 🏘️ Registro Propiedad")
        with st.form("form_p", clear_on_submit=True):
            direc = st.text_input("Dirección (Ej: Altair15)")
            tipo = st.selectbox("Tipo", ["Vivienda", "Garaje", "Local"])
            prop_p = st.text_input("Propietario", value=st.session_state.usuario_identificado['nombre'])
            if st.form_submit_button("Registrar"):
                if direc and prop_p:
                    st.session_state.historial_chat["🗒️registrar-propiedad"].append({
                        "autor": "REGISTRO CIVIL", "hora": datetime.now().strftime("%H:%M"),
                        "msg": f"🏠 **NUEVA PROPIEDAD:** {tipo} en `{direc}` registrada a **{prop_p}**"
                    })
                    # Guardar registro de propiedad
                    guardar_datos()
                    st.rerun()

    elif st.session_state.canal_actual == "💻lspd":
        st.markdown("### 🚓 Sistema de Base de Datos LSPD")
        tab1, tab2 = st.tabs(["🔍 Revisar Antecedentes", "📝 Registrar Delito"])
        
        with tab1:
            dni_consulta = st.text_input("DNI del Ciudadano a consultar")
            if st.button("Consultar Base de Datos"):
                if dni_consulta:
                    registros = st.session_state.antecedentes.get(dni_consulta, [])
                    if registros:
                        st.warning(f"⚠️ **Antecedentes encontrados para DNI: {dni_consulta}**")
                        for r in registros:
                            st.markdown(f"**Fecha:** {r['fecha']} | **Delito:** {r['delito']} | **Agente:** {r['agente']}")
                    else:
                        st.success(f"✅ El DNI {dni_consulta} no tiene antecedentes penales.")
        
        with tab2:
            # RESTRICCIÓN: Solo policías registran delitos
            if st.session_state.usuario_identificado['rol'] == "Policía":
                with st.form("delito_f"):
                    dni_del = st.text_input("DNI Infractor")
                    delito_txt = st.text_area("Descripción del Delito")
                    agente_n = st.text_input("Agente reportante", value=st.session_state.usuario_identificado['nombre'])
                    if st.form_submit_button("Registrar en Archivo"):
                        if dni_del and delito_txt:
                            if dni_del not in st.session_state.antecedentes: st.session_state.antecedentes[dni_del] = []
                            st.session_state.antecedentes[dni_del].append({
                                "fecha": datetime.now().strftime("%d/%m/%Y"),
                                "delito": delito_txt,
                                "agente": agente_n
                            })
                            # Guardar base de datos policial
                            guardar_datos()
                            st.success("Expediente actualizado.")
            else:
                st.error("Acceso denegado. Solo personal autorizado (Policía) puede registrar delitos.")

    # Renderizado del chat
    st.markdown("---")
    chat_container = st.container(height=400)
    for m in st.session_state.historial_chat[st.session_state.canal_actual]:
        chat_container.markdown(f"""
        <div class="chat-bubble">
            <span class="user-name">{m['autor']}</span>
            <span class="timestamp">{m['hora']}</span><br>
            <div style="margin-top:5px;">{m['msg']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.chat_input("Escribe un mensaje o comando...", key="input_usuario", on_submit=enviar_mensaje)

# --- PANEL DE ADMINISTRACIÓN (Solo tú deberías usarlo) ---
with st.sidebar.expander("🛠️ Administración"):
    password = st.text_input("Contraseña Admin", type="password")
    if password == "TU_CONTRASEÑA_SECRETA": # Cambia esto
        st.subheader("Eliminar Ciudadano")
        dni_a_borrar = st.text_input("DNI del ciudadano a borrar")
        if st.button("❌ Eliminar Permanentemente"):
            # Cargamos los datos actuales
            datos = cargar_datos() 
            if dni_a_borrar in datos['ciudadanos']:
                del datos['ciudadanos'][dni_a_borrar]
                guardar_datos(datos)
                st.success(f"Ciudadano con DNI {dni_a_borrar} eliminado.")
                st.rerun()
            else:
                st.error("Ese DNI no existe.")
                

# --- 3. COLUMNA DE MIEMBROS ---
with col_members:
    st.markdown("### 👥 Ciudadanos")
    roles_posibles = ["Policía", "Mafia", "Médico", "Mecánico", "Civil"]
    usuarios_por_rol = {rol: [] for rol in roles_posibles}
    
    for dni, datos in st.session_state.usuarios_db.items():
        rol = datos.get('rol', 'Civil')
        if rol in usuarios_por_rol:
            usuarios_por_rol[rol].append(datos['nombre'])
        else:
            usuarios_por_rol["Civil"].append(datos['nombre'])

    for rol in roles_posibles:
        st.markdown(f'<div class="role-header">{rol} — {len(usuarios_por_rol[rol])}</div>', unsafe_allow_html=True)
        if usuarios_por_rol[rol]:
            for nombre in usuarios_por_rol[rol]:
                st.markdown(f'<div class="member-item">🟢 {nombre}</div>', unsafe_allow_html=True)
        else:

            st.markdown('<div class="empty-role">Nadie en la ciudad</div>', unsafe_allow_html=True)


