"""Interfaz de escritorio sencilla para escribir o dictar comandos."""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime


class InterfazComandos:
    FONDO = "#0B1220"
    PANEL = "#121D2E"
    PANEL_CLARO = "#1B2A40"
    TEXTO = "#F3F7FC"
    SUAVE = "#9AABC0"
    CELESTE = "#4CC9F0"
    VERDE = "#64D6A5"
    ROJO = "#FF7885"

    def __init__(self, agente, robot, modo_voz: bool = False):
        self.agente = agente
        self.robot = robot
        self.modo = "voz" if modo_voz else "texto"
        self.ocupado = False
        self.orden_activa = False
        self.cierre_pendiente = False

        self.ventana = tk.Tk()
        self.ventana.title("OTTO · Control del robot")
        self.ventana.configure(bg=self.FONDO)
        self.ventana.geometry("1060x760")
        self.ventana.minsize(920, 640)
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._construir()
        self._agregar_mensaje(
            "OTTO", "Conectado y listo. Escribí una orden o elegí el modo voz.",
            "sistema")
        self._actualizar_modo()

    def iniciar(self) -> None:
        self.ventana.mainloop()

    def _construir(self) -> None:
        principal = tk.Frame(self.ventana, bg=self.FONDO, padx=28, pady=24)
        principal.pack(fill="both", expand=True)
        principal.grid_columnconfigure(0, weight=1)
        principal.grid_columnconfigure(1, minsize=270)
        principal.grid_rowconfigure(2, weight=1)

        cabecera = tk.Frame(principal, bg=self.FONDO)
        cabecera.grid(row=0, column=0, sticky="ew", pady=(0, 22))
        tk.Label(cabecera, text="OTTO", bg=self.FONDO, fg=self.CELESTE,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(cabecera, text="Control del robot", bg=self.FONDO,
                 fg=self.TEXTO, font=("Segoe UI", 24, "bold")).pack(anchor="w")
        modelo = getattr(self.robot, "modelo", "robot").upper()
        tk.Label(cabecera, text=f"●  {modelo} CONECTADO", bg=self.FONDO,
                 fg=self.VERDE, font=("Segoe UI", 10, "bold")).pack(
                     anchor="w", pady=(5, 0))

        selector = tk.Frame(principal, bg=self.PANEL, padx=16, pady=14)
        selector.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        selector.grid_columnconfigure(0, weight=1)
        tk.Label(selector, text="MODO DE ENTRADA", bg=self.PANEL,
                 fg=self.SUAVE, font=("Segoe UI", 9, "bold")).grid(
                     row=0, column=0, sticky="w", pady=(0, 10))
        modos = tk.Frame(selector, bg=self.PANEL)
        modos.grid(row=1, column=0, sticky="ew")
        modos.grid_columnconfigure(0, weight=1, uniform="modo")
        modos.grid_columnconfigure(1, weight=1, uniform="modo")
        self.boton_texto = tk.Button(
            modos, text="⌨  Texto", command=lambda: self._cambiar_modo("texto"),
            relief="flat", bd=0, padx=14, pady=11, cursor="hand2",
            font=("Segoe UI", 11, "bold"))
        self.boton_voz = tk.Button(
            modos, text="🎙  Voz", command=lambda: self._cambiar_modo("voz"),
            relief="flat", bd=0, padx=14, pady=11, cursor="hand2",
            font=("Segoe UI", 11, "bold"))
        self.boton_texto.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.boton_voz.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        historial_panel = tk.Frame(principal, bg=self.PANEL, padx=2, pady=2)
        historial_panel.grid(row=2, column=0, sticky="nsew", pady=(0, 16))
        historial_panel.grid_rowconfigure(0, weight=1)
        historial_panel.grid_columnconfigure(0, weight=1)
        self.historial = tk.Text(
            historial_panel, wrap="word", state="disabled", relief="flat",
            bd=0, padx=18, pady=16, bg=self.PANEL, fg=self.TEXTO,
            insertbackground=self.TEXTO, font=("Segoe UI", 11),
            spacing1=2, spacing3=8)
        self.historial.grid(row=0, column=0, sticky="nsew")
        barra = tk.Scrollbar(historial_panel, command=self.historial.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.historial.configure(yscrollcommand=barra.set)
        self.historial.tag_configure("meta_usuario", foreground=self.CELESTE,
                                     font=("Segoe UI", 9, "bold"))
        self.historial.tag_configure("meta_otto", foreground=self.VERDE,
                                     font=("Segoe UI", 9, "bold"))
        self.historial.tag_configure("orden", foreground=self.TEXTO,
                                     font=("Segoe UI", 12))
        self.historial.tag_configure("respuesta", foreground="#D5DFEC",
                                     font=("Segoe UI", 11))
        self.historial.tag_configure("bloqueado", foreground=self.ROJO,
                                     font=("Segoe UI", 11, "bold"))
        self.historial.tag_configure("sistema", foreground=self.SUAVE,
                                     font=("Segoe UI", 10, "italic"))

        self.estado = tk.StringVar(value="Listo para recibir una orden")
        tk.Label(principal, textvariable=self.estado, anchor="w",
                 bg=self.FONDO, fg=self.SUAVE,
                 font=("Segoe UI", 9)).grid(row=3, column=0, sticky="ew",
                                             pady=(0, 9))

        self.area_texto = tk.Frame(principal, bg=self.FONDO)
        self.area_texto.grid_columnconfigure(0, weight=1)
        self.entrada = tk.Entry(
            self.area_texto, relief="flat", bd=0, bg=self.PANEL_CLARO,
            fg=self.TEXTO, insertbackground=self.TEXTO,
            font=("Segoe UI", 12),
        )
        self.placeholder = "Escribí una orden para el robot..."
        self.entrada.insert(0, self.placeholder)
        self.entrada.configure(fg=self.SUAVE)
        self.entrada.grid(row=0, column=0, sticky="ew", ipady=14, padx=(0, 10))
        self.entrada.bind("<Return>", self._enviar_texto)
        self.entrada.bind("<FocusIn>", self._quitar_placeholder)
        self.entrada.bind("<FocusOut>", self._poner_placeholder)
        self.boton_enviar = tk.Button(
            self.area_texto, text="Enviar  →", command=self._enviar_texto,
            relief="flat", bd=0, bg=self.CELESTE, fg=self.FONDO,
            activebackground="#7BD8F5", padx=18, pady=12, cursor="hand2",
            font=("Segoe UI", 10, "bold"))
        self.boton_enviar.grid(row=0, column=1, sticky="ew")

        self.area_voz = tk.Frame(principal, bg=self.PANEL, padx=16, pady=14)
        self.area_voz.grid_columnconfigure(0, weight=1)
        tk.Label(self.area_voz, text="Dictá una orden en voz alta",
                 bg=self.PANEL, fg=self.TEXTO,
                 font=("Segoe UI", 11, "bold")).grid(
                     row=0, column=0, sticky="w")
        tk.Label(self.area_voz, text="Se escucha una frase por vez.",
                 bg=self.PANEL, fg=self.SUAVE,
                 font=("Segoe UI", 9)).grid(
                     row=1, column=0, sticky="w", pady=(3, 10))
        self.boton_escuchar = tk.Button(
            self.area_voz, text="🎙  Escuchar comando",
            command=self._escuchar_comando, relief="flat", bd=0,
            bg=self.CELESTE, fg=self.FONDO, activebackground="#7BD8F5",
            padx=18, pady=12, cursor="hand2", font=("Segoe UI", 11, "bold"))
        self.boton_escuchar.grid(row=2, column=0, sticky="ew")
        self._construir_comandos(principal)

    def _construir_comandos(self, principal) -> None:
        panel = tk.Frame(principal, bg=self.PANEL, width=270, padx=14, pady=16)
        panel.grid(row=0, column=1, rowspan=5, sticky="nsew", padx=(20, 0))
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        tk.Label(panel, text="Comandos disponibles", bg=self.PANEL,
                 fg=self.TEXTO, font=("Segoe UI", 12, "bold"),
                 anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(panel, text="Elegí un ejemplo para editarlo y enviarlo.",
                 bg=self.PANEL, fg=self.SUAVE, font=("Segoe UI", 9),
                 wraplength=235, justify="left", anchor="w").grid(
                     row=1, column=0, columnspan=2, sticky="ew", pady=(5, 12))

        lienzo = tk.Canvas(panel, bg=self.PANEL, highlightthickness=0,
                           width=235, bd=0)
        lienzo.grid(row=2, column=0, sticky="nsew")
        barra = tk.Scrollbar(panel, command=lienzo.yview)
        barra.grid(row=2, column=1, sticky="ns")
        lienzo.configure(yscrollcommand=barra.set)
        lista = tk.Frame(lienzo, bg=self.PANEL)
        ventana_lista = lienzo.create_window((0, 0), window=lista, anchor="nw")
        lista.bind("<Configure>", lambda _e: lienzo.configure(
            scrollregion=lienzo.bbox("all")))
        lienzo.bind("<Configure>", lambda e: lienzo.itemconfigure(
            ventana_lista, width=e.width))

        def desplazar(evento):
            if evento.delta:
                lienzo.yview_scroll(-1 if evento.delta > 0 else 1, "units")
            return "break"

        lienzo.bind("<MouseWheel>", desplazar)
        lista.bind("<MouseWheel>", desplazar)
        es_g1 = getattr(self.robot, "modelo", "").lower() == "g1"
        es_local = getattr(self.robot, "transporte", "") == "local"
        grupos = (
            ("MOVIMIENTO", (
                ("Avanzar", "Avanzá 30 centímetros", True),
                ("Retroceder", "Retrocedé 30 centímetros", True),
                ("Girar a la izquierda", "Girá 45 grados a la izquierda", True),
                ("Girar a la derecha", "Girá 45 grados a la derecha", True),
                ("Detenerse", "Frená", True),
            )),
            ("SALUDO Y CONSULTAS", (
                ("Saludar", "Saludá", True),
                ("Estado y batería", "¿Cuánta batería tenés?", True),
            )),
            ("GESTOS · SOLO G1", (
                ("Dar la mano", "Dame la mano", es_g1),
                ("Hacer el 67", "Hacé el 67", es_g1 and es_local),
                ("Bailar", "Bailá", es_g1 and es_local),
                ("Festejar", "Festejá", es_g1 and es_local),
                ("Doble bíceps", "Hacé doble bíceps", es_g1 and es_local),
            )),
            ("MEMORIA Y SECUENCIAS", (
                ("Repetir la última acción", "Hacelo otra vez", True),
                ("Combinar órdenes", "Girá 45 grados y después avanzá 30 centímetros",
                 True),
            )),
        )
        self.botones_comandos = []
        for grupo, comandos in grupos:
            titulo = tk.Label(lista, text=grupo, bg=self.PANEL, fg=self.SUAVE,
                              font=("Segoe UI", 8, "bold"), anchor="w")
            titulo.pack(fill="x", pady=(12, 7))
            titulo.bind("<MouseWheel>", desplazar)
            for nombre, ejemplo, disponible in comandos:
                boton = tk.Button(
                    lista, text=f"{nombre}\n{ejemplo}",
                    command=lambda texto=ejemplo: self._cargar_comando(texto),
                    bg=self.PANEL_CLARO, fg=self.TEXTO,
                    activebackground="#263A55", activeforeground=self.CELESTE,
                    disabledforeground="#607188", relief="flat", bd=0,
                    anchor="w", justify="left", wraplength=210,
                    padx=10, pady=9, font=("Segoe UI", 9), cursor="hand2",
                    state="normal" if disponible else "disabled")
                boton.pack(fill="x", pady=(0, 6))
                boton.bind("<MouseWheel>", desplazar)
                self.botones_comandos.append((boton, disponible))

        tk.Label(panel, text="También podés dictar estas frases.\n"
                 "Las distancias y los ángulos son editables.",
                 bg=self.PANEL, fg=self.SUAVE, font=("Segoe UI", 8),
                 wraplength=235, justify="left", anchor="w").grid(
                     row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    def _cargar_comando(self, texto: str) -> None:
        if self.ocupado:
            return
        self.modo = "texto"
        self._actualizar_modo()
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)
        self.entrada.configure(fg=self.TEXTO)
        self.entrada.icursor("end")
        self.entrada.focus_set()
        self.estado.set("Ejemplo cargado · podés editarlo antes de enviarlo")

    def _cambiar_modo(self, modo: str) -> None:
        if self.ocupado or modo == self.modo:
            return
        self.modo = modo
        self.estado.set("Modo texto · escribí y presioná Enter" if modo == "texto"
                        else "Modo voz · presioná Escuchar comando")
        self._actualizar_modo()

    def _actualizar_modo(self) -> None:
        self.area_texto.grid_forget()
        self.area_voz.grid_forget()
        if self.modo == "texto":
            self.boton_texto.configure(bg=self.CELESTE, fg=self.FONDO,
                                       activebackground="#7BD8F5")
            self.boton_voz.configure(bg=self.PANEL_CLARO, fg=self.TEXTO,
                                     activebackground="#263A55")
            self.area_texto.grid(row=4, column=0, sticky="ew")
            if not self.ocupado:
                self.entrada.focus_set()
        else:
            self.boton_voz.configure(bg=self.CELESTE, fg=self.FONDO,
                                     activebackground="#7BD8F5")
            self.boton_texto.configure(bg=self.PANEL_CLARO, fg=self.TEXTO,
                                       activebackground="#263A55")
            self.area_voz.grid(row=4, column=0, sticky="ew")
        estado_botones = "disabled" if self.ocupado else "normal"
        self.boton_texto.configure(state=estado_botones)
        self.boton_voz.configure(state=estado_botones)
        self.entrada.configure(state=("disabled" if self.ocupado else "normal"))
        self.boton_enviar.configure(state=("disabled" if self.ocupado else "normal"))
        self.boton_escuchar.configure(state=("disabled" if self.ocupado else "normal"))
        for boton, disponible in self.botones_comandos:
            boton.configure(state=("normal" if disponible and not self.ocupado
                                   else "disabled"))

    def _agregar_mensaje(self, emisor: str, texto: str, clase: str) -> None:
        hora = datetime.now().strftime("%H:%M")
        self.historial.configure(state="normal")
        if clase == "sistema":
            self.historial.insert("end", f"{texto}\n\n", "sistema")
        else:
            etiqueta = "meta_usuario" if emisor == "VOS" else "meta_otto"
            cuerpo = "orden" if emisor == "VOS" else clase
            self.historial.insert("end", f"{emisor}  ·  {hora}\n", etiqueta)
            self.historial.insert("end", f"{texto}\n\n", cuerpo)
        self.historial.configure(state="disabled")
        self.historial.see("end")

    def _enviar_texto(self, _evento=None):
        texto = self.entrada.get().strip()
        if not texto or texto == self.placeholder or self.ocupado:
            return "break"
        self.entrada.delete(0, "end")
        self.entrada.configure(fg=self.TEXTO)
        self._procesar(texto)
        return "break"

    def _quitar_placeholder(self, _evento=None):
        if self.entrada.get() == self.placeholder:
            self.entrada.delete(0, "end")
            self.entrada.configure(fg=self.TEXTO)

    def _poner_placeholder(self, _evento=None):
        if not self.entrada.get().strip():
            self.entrada.insert(0, self.placeholder)
            self.entrada.configure(fg=self.SUAVE)

    def _escuchar_comando(self) -> None:
        if self.ocupado:
            return
        self.ocupado = True
        self.estado.set("Ajustando el micrófono y esperando una frase...")
        self._actualizar_modo()

        def capturar():
            try:
                from voz import ReconocedorVoz

                texto = ReconocedorVoz().escuchar().strip()
                self._enviar_a_ui(self._voz_recibida, texto, None)
            except Exception as exc:  # dependencia, microfono o reconocimiento
                self._enviar_a_ui(self._voz_recibida, "", str(exc))

        threading.Thread(target=capturar, daemon=True).start()

    def _voz_recibida(self, texto: str, error: str | None) -> None:
        self.ocupado = False
        if error:
            self.estado.set("No se pudo recibir el comando")
            self._agregar_mensaje("OTTO", f"Voz no disponible: {error}", "respuesta")
            self._actualizar_modo()
            return
        if not texto:
            self.estado.set("No se recibió ninguna frase")
            self._actualizar_modo()
            return
        self._procesar(texto)

    def _procesar(self, texto: str) -> None:
        self._agregar_mensaje("VOS", texto, "orden")
        self.ocupado = True
        self.orden_activa = True
        self.estado.set("Procesando la orden...")
        self._actualizar_modo()

        def ejecutar():
            try:
                respuesta = self.agente.procesar(texto)
                self._enviar_a_ui(self._mostrar_respuesta, respuesta)
            except Exception as exc:  # muestra fallos de conexión y del agente
                self._enviar_a_ui(self._mostrar_error, str(exc))

        threading.Thread(target=ejecutar, daemon=True).start()

    def _mostrar_respuesta(self, respuesta: dict) -> None:
        self.ocupado = False
        self.orden_activa = False
        tipo = respuesta.get("tipo", "ORDEN")
        mensaje = respuesta.get("mensaje", "")
        bloqueado = respuesta.get("bloqueado", False)
        cuerpo = f"{tipo} · {mensaje}"
        self._agregar_mensaje("OTTO", cuerpo,
                              "bloqueado" if bloqueado else "respuesta")
        self.estado.set("Orden bloqueada por seguridad" if bloqueado
                        else "Listo para otra orden")
        self._actualizar_modo()
        self._cerrar_si_corresponde()

    def _mostrar_error(self, mensaje: str) -> None:
        self.ocupado = False
        self.orden_activa = False
        self._agregar_mensaje("OTTO", mensaje, "bloqueado")
        self.estado.set("No se pudo ejecutar la orden")
        self._actualizar_modo()
        self._cerrar_si_corresponde()

    def _cerrar(self) -> None:
        if self.orden_activa:
            self.cierre_pendiente = True
            self.estado.set("Terminando la orden activa antes de cerrar...")
            self.boton_texto.configure(state="disabled")
            self.boton_voz.configure(state="disabled")
            self.boton_enviar.configure(state="disabled")
            self.boton_escuchar.configure(state="disabled")
            return
        self.ventana.destroy()

    def _cerrar_si_corresponde(self) -> None:
        if not self.cierre_pendiente:
            return
        try:
            self.robot.detenerse()
        finally:
            self.ventana.destroy()

    def _enviar_a_ui(self, funcion, *argumentos) -> None:
        try:
            self.ventana.after(0, funcion, *argumentos)
        except tk.TclError:
            pass  # La ventana pudo cerrarse mientras esperaba al microfono.
