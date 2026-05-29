# Sistema de Encuestas

Aplicación web para crear y gestionar encuestas con panel de resultados.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación

```bash
# 1. Abre una terminal en la carpeta del proyecto

# 2. Crea un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Inicia la aplicación
python run.py
```

La aplicación queda disponible en: **http://localhost:5000**

## Acceso inicial

| Campo     | Valor      |
|-----------|------------|
| Documento | `admin`    |
| Contraseña| `admin1234`|

> ⚠️ Cambia la contraseña del admin después del primer acceso.

## Contraseña de usuarios

La contraseña inicial de cada residente importado desde Excel es su **número de documento**. El admin puede restablecerla desde el panel de usuarios.

## Flujo de uso

1. **Importar usuarios**: Admin → Usuarios → Importar Excel  
   - Columnas requeridas: `documento`, `residente`, `grupo primario`  
   - Se omiten filas sin grupo primario  
   - Columnas opcionales: `email`, `app`

2. **Crear encuesta**: Admin → Nueva encuesta  
   - Definir título, descripción, fechas de inicio y cierre  
   - Marcar como "activa" para que sea visible

3. **Agregar preguntas**: Desde la pantalla de edición de la encuesta  
   - Tipos: opción múltiple (una), selección múltiple, escala de valoración, texto libre  
   - Cada pregunta puede tener **subpreguntas condicionales** (se muestran según la respuesta elegida)  
   - Se puede marcar cada pregunta como obligatoria o no

4. **Responder**: Los residentes ingresan con su documento y contraseña  
   - Solo pueden responder una vez por encuesta  
   - La encuesta solo está disponible entre las fechas configuradas

5. **Ver resultados**: Admin → Resultados  
   - Gráficos por pregunta  
   - Participación por grupo  
   - Respuestas de texto libre

## Estructura del proyecto

```
encuesta/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuración
│   ├── factory.py         # App factory + seed admin
│   ├── models.py          # Modelos SQLAlchemy
│   ├── routes_auth.py     # Login / logout
│   ├── routes_admin.py    # Panel de administración
│   └── routes_survey.py   # Encuesta para usuarios
├── templates/
│   ├── base.html
│   ├── auth/login.html
│   ├── admin/             # Panel admin
│   └── survey/            # Vistas de encuesta
├── requirements.txt
├── run.py                 # Punto de entrada
└── encuesta.db            # Base de datos SQLite (se crea automáticamente)
```

## Variables de entorno (opcional)

| Variable       | Default                        | Descripción              |
|----------------|--------------------------------|--------------------------|
| `SECRET_KEY`   | valor de desarrollo            | Clave de sesión Flask    |
| `DATABASE_URL` | `sqlite:///encuesta.db`        | URL de base de datos     |
