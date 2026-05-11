from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clave-ultra-secreta-2026'

# Contenido del juego (títulos, textos, preguntas, opciones, respuesta correcta)
zonas = {
    1: {
        "nombre": "Cámara de las Reglas",
        "texto": [
            "Asistencia mínima del 80%.",
            "Tolerancia de 10 minutos.",
            "Por cada 3 faltas se descuenta 1 punto."
        ],
        "preguntas": [
            {
                "pregunta": "¿Asistencia mínima requerida?",
                "opciones": ["70%", "80%", "90%"],
                "correcta": 1   # índice: 0=70%, 1=80%, 2=90%
            },
            {
                "pregunta": "¿Minutos de tolerancia?",
                "opciones": ["5 min", "10 min", "15 min"],
                "correcta": 1
            }
        ]
    },
    2: {
        "nombre": "Oráculo de las Notas",
        "texto": [
            "Exámenes parciales (2): 30%",
            "Proyecto integrador: 40%",
            "Tareas y prácticas: 20%",
            "Participación: 10%"
        ],
        "preguntas": [
            {
                "pregunta": "Porcentaje del proyecto integrador",
                "opciones": ["30%", "40%", "50%"],
                "correcta": 1
            },
            {
                "pregunta": "¿Cuánto suman los dos parciales?",
                "opciones": ["30%", "40%", "50%"],
                "correcta": 0
            }
        ]
    },
    3: {
        "nombre": "Skills a desbloquear",
        "texto": [
            "Objetivo general: Desarrollar apps móviles nativas Android.",
            "Objetivos particulares:",
            "- Arquitectura Android y ciclo de vida.",
            "- Diseño de UI con XML/Compose.",
            "- Persistencia con Room.",
            "- Consumo de APIs con Retrofit."
        ],
        "preguntas": [
            {
                "pregunta": "¿Objetivo general?",
                "opciones": ["Apps web", "Apps Android", "Bases de datos", "Redes"],
                "correcta": 1
            },
            {
                "pregunta": "Librería recomendada para persistencia local:",
                "opciones": ["Retrofit", "Room", "Firestore", "SQLite puro"],
                "correcta": 1
            }
        ]
    },
    4: {
        "nombre": "Línea del Tiempo",
        "texto": [
            "Inicio de clases: 4 de agosto 2026",
            "Primer parcial: 22-26 sept 2026",
            "Avance de proyecto: 10 oct 2026",
            "Segundo parcial: 17-21 nov 2026",
            "Entrega final: 8 dic 2026",
            "Fin de cursos: 12 dic 2026"
        ],
        "preguntas": [
            {
                "pregunta": "¿Cuándo se entrega el proyecto final?",
                "opciones": ["10 octubre", "22 septiembre", "8 diciembre", "12 diciembre"],
                "correcta": 2
            },
            {
                "pregunta": "¿Fecha de inicio del semestre?",
                "opciones": ["1 agosto", "4 agosto", "11 agosto", "18 agosto"],
                "correcta": 1
            }
        ]
    }
}

# Inicializar la sesión (todo bloqueado menos la zona 1)
@app.before_request
def iniciar_sesion():
    if 'progreso' not in session:
        session['progreso'] = {}
        for num in range(1, 5):
            session['progreso'][str(num)] = {
                'quiz_ok': False,
                'compromiso': False
            }
        session.modified = True

# Página principal (el mapa del juego)
@app.route('/')
def mapa():
    # Preparamos lista con el estado de cada zona
    info_zonas = []
    for num in range(1, 5):
        zona = zonas[num]
        estado = session['progreso'][str(num)]
        # ¿Está desbloqueada?
        if num == 1:
            desbloqueada = True
        else:
            anterior = session['progreso'][str(num-1)]
            desbloqueada = anterior['compromiso']

        # Determinar estado visual
        if not desbloqueada:
            estado_str = 'bloqueada'
        elif not estado['quiz_ok']:
            estado_str = 'pendiente_quiz'
        elif not estado['compromiso']:
            estado_str = 'pendiente_compromiso'
        else:
            estado_str = 'completada'

        info_zonas.append({
            'num': num,
            'nombre': zona['nombre'],
            'estado_str': estado_str,
            'desbloqueada': desbloqueada
        })

    return render_template('index.html', zonas_info=info_zonas)

# Ruta para cada zona
@app.route('/zona/<int:num>')
def zona(num):
    if num < 1 or num > 4:
        return redirect(url_for('mapa'))
    # Verificar desbloqueo
    if num != 1 and not session['progreso'][str(num-1)]['compromiso']:
        flash("Debes completar la zona anterior antes de entrar aquí.", "danger")
        return redirect(url_for('mapa'))

    zona_data = zonas[num]
    estado = session['progreso'][str(num)]
    # Pasamos los datos necesarios a la plantilla
    return render_template('index.html',
                           zona_activa=num,
                           zona=zona_data,
                           estado=estado,
                           mostrar_zona=True)

# Procesar el quiz de una zona
@app.route('/zona/<int:num>/quiz', methods=['POST'])
def evaluar_quiz(num):
    zona_data = zonas[num]
    preguntas = zona_data['preguntas']
    aciertos = 0
    for i, p in enumerate(preguntas):
        resp = request.form.get(f'q{i}')
        if resp is not None and int(resp) == p['correcta']:
            aciertos += 1
    if aciertos == len(preguntas):
        session['progreso'][str(num)]['quiz_ok'] = True
        session.modified = True
        flash("✅ ¡Has superado las preguntas! Ahora marca tu compromiso.", "success")
    else:
        flash(f"❌ Solo {aciertos} de {len(preguntas)} correctas. Vuelve a intentarlo.", "danger")
    return redirect(url_for('zona', num=num))

# Procesar el compromiso
@app.route('/zona/<int:num>/compromiso', methods=['POST'])
def marcar_compromiso(num):
    if 'compromiso' in request.form:
        session['progreso'][str(num)]['compromiso'] = True
        session.modified = True
        flash("Compromiso sellado. La siguiente zona se ha desbloqueado.", "success")
        if num < 4:
            return redirect(url_for('zona', num=num+1))
        else:
            flash("¡Has completado todas las zonas! Conoces la materia.", "success")
            return redirect(url_for('mapa'))
    else:
        flash("Debes marcar la casilla de compromiso.", "warning")
        return redirect(url_for('zona', num=num))

# Reiniciar la aventura
@app.route('/reiniciar')
def reiniciar():
    session.clear()
    flash("Aventura reiniciada. Empieza desde la Cámara de las Reglas.", "info")
    return redirect(url_for('mapa'))

if __name__ == '__main__':
    app.run(debug=True)