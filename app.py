from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

SERVICIOS = [
    {
        "id": 1,
        "nombre": "Consulta General Veterinaria",
        "descripcion": "Revisión médica completa a cargo de un veterinario certificado.",
        "precio": "80.000",
        "icono": "🩺",
        "stock": 12
    },
    {
        "id": 2,
        "nombre": "Vacuna Antirrábica",
        "descripcion": "Aplicación de vacuna antirrábica para perros y gatos.",
        "precio": "60.000",
        "icono": "💉",
        "stock": 25
    },
    {
        "id": 3,
        "nombre": "Baño y Peluquería Canina",
        "descripcion": "Baño medicado, corte de pelo y limpieza de oídos.",
        "precio": "55.000",
        "icono": "🛁",
        "stock": 10
    },
    {
        "id": 4,
        "nombre": "Desparasitación Interna y Externa",
        "descripcion": "Tratamiento antiparasitario para perros y gatos de cualquier edad.",
        "precio": "45.000",
        "icono": "💊",
        "stock": 20
    },
    {
        "id": 5,
        "nombre": "Alimento Premium para Perros 15kg",
        "descripcion": "Nutrición balanceada para perros adultos de todas las razas.",
        "precio": "189.900",
        "icono": "🐶",
        "stock": 14
    },
    {
        "id": 6,
        "nombre": "Alimento Premium para Gatos 10kg",
        "descripcion": "Fórmula especial para el cuidado renal y urinario felino.",
        "precio": "159.900",
        "icono": "🐱",
        "stock": 16
    },
    {
        "id": 7,
        "nombre": "Kit de Primeros Auxilios para Mascotas",
        "descripcion": "Vendas, antisépticos y elementos básicos para emergencias.",
        "precio": "69.900",
        "icono": "🩹",
        "stock": 18
    },
    {
        "id": 8,
        "nombre": "Transportadora para Mascotas",
        "descripcion": "Resistente y ventilada, ideal para viajes y visitas al veterinario.",
        "precio": "129.900",
        "icono": "🧳",
        "stock": 9
    },
    {
        "id": 9,
        "nombre": "Juguete Interactivo para Mascotas",
        "descripcion": "Estimula la mente de tu mascota y reduce la ansiedad.",
        "precio": "34.900",
        "icono": "🎾",
        "stock": 30
    },
    {
        "id": 10,
        "nombre": "Cirugía Menor (Esterilización)",
        "descripcion": "Procedimiento quirúrgico ambulatorio con seguimiento post-operatorio.",
        "precio": "250.000",
        "icono": "🏥",
        "stock": 4
    }
]


@app.route('/')
def inicio():
    return render_template('index.html', servicios=SERVICIOS)


@app.route('/api/servicios')
def api_servicios():
    # Endpoint (GET) 
    return jsonify({"estado": "exito", "datos": SERVICIOS})


# METODO POST
@app.route('/api/servicios/<int:servicio_id>/reservar', methods=['POST'])
def reservar_servicio(servicio_id):
    # Reserva 1 cupo/unidad del servicio o producto indicado: descuenta su disponibilidad
    for servicio in SERVICIOS:
        if servicio['id'] == servicio_id:
            if servicio['stock'] <= 0:
                return jsonify({"estado": "error", "mensaje": "Sin cupos disponibles"}), 400
            servicio['stock'] -= 1
            return jsonify({"estado": "exito", "datos": servicio})
    return jsonify({"estado": "error", "mensaje": "Servicio no encontrado"}), 404


# METODO PUT
@app.route('/api/servicios/<int:servicio_id>', methods=['PUT'])
def reemplazar_servicio(servicio_id):
    datos = request.get_json()

    campos_requeridos = [
        'nombre',
        'descripcion',
        'precio',
        'icono',
        'stock'
    ]

    for campo in campos_requeridos:
        if campo not in datos:
            return jsonify({
                "estado": "error",
                "mensaje": f"Falta el campo: {campo}"
            }), 400

    for servicio in SERVICIOS:
        if servicio['id'] == servicio_id:
            servicio['nombre'] = datos['nombre']
            servicio['descripcion'] = datos['descripcion']
            servicio['precio'] = datos['precio']
            servicio['icono'] = datos['icono']
            servicio['stock'] = datos['stock']

            return jsonify({
                "estado": "exito",
                "mensaje": "Servicio actualizado correctamente",
                "datos": servicio
            })

    return jsonify({
        "estado": "error",
        "mensaje": "Servicio no encontrado"
    }), 404


# METODO DELETE
@app.route('/api/servicios/<int:servicio_id>', methods=['DELETE'])
def eliminar_servicio(servicio_id):
    # Elimina el servicio o producto indicado
    for servicio in SERVICIOS:
        if servicio['id'] == servicio_id:
            SERVICIOS.remove(servicio)

            return jsonify({
                "estado": "exito",
                "mensaje": "Servicio eliminado correctamente",
                "datos": servicio
            })

    return jsonify({
        "estado": "error",
        "mensaje": "Servicio no encontrado"
    }), 404


if __name__ == '__main__':
    # host='0.0.0.0' permite acceder desde otros dispositivos en tu red
    app.run(debug=True, host='0.0.0.0', port=5000)