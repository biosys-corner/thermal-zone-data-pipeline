# Thermal Zone Data Pipeline & Stability Analytics

Un pipeline en Python diseñado para la adquisición de datos de temperatura en tiempo real vía puerto serial (ESP32) y el posterior análisis estadístico de estabilidad térmica en sistemas multizona independientes.

## Descripción General

Este proyecto contiene las herramientas de procesamiento de datos desarrolladas como parte de un trabajo de tesis de ingeniería para la evaluación experimental de prototipos de incubación multizona.

El sistema está compuesto por **5 zonas térmicas independientes**, lo que permite configurar *setpoints* de temperatura individuales (diferentes o iguales entre sí) para evaluar el comportamiento del prototipo bajo múltiples escenarios simultáneos.

El pipeline consta de dos etapas principales:

1. **Adquisición Serial (`scripts/capturar_datos.py`):** Escucha las tramas de datos emitidas por un microcontrolador ESP32 mediante comunicación USB-Serial y las estructura dinámicamente en archivos `.csv` dentro de la carpeta `data/`con marcas de tiempo.
2. **Análisis de Estabilidad (`scripts/analizar_estabilidad_v6.py`):** Procesa los registros `.csv`, evalúa el tiempo necesario para alcanzar y mantener la estabilidad térmica en cada zona dentro de rangos de tolerancia específicos (±0.5°C), realiza pruebas de varianza estadística (**ANOVA**) entre los canales independientes y genera gráficos generales y por zona en la carpeta `outputs/`.

> **Nota sobre el Hardware:** El script de captura está adaptado a la estructura de tramas emitida por el firmware del prototipo. El script de análisis estadístico es modular y compatible con cualquier archivo CSV que mantenga una estructura similar de registros de temperatura por canal y timestamp.

---

## Estructura del Repositorio

```text
thermal-zone-data-pipeline/
├── README.md                  # Documentación del proyecto
├── requirements.txt           # Dependencias de Python
├── .gitignore                 # Archivos excluidos del control de versiones
├── assets/
│   └── console_output.png     # Captura de pantalla de la ejecución en consola
├── data/
│   └── raw_sample.csv         # Registro experimental de prueba (24h)
├── outputs/
│   └── .gitkeep               # Carpeta de destino para gráficos generados
└── scripts/
    ├── capturar_datos.py      # Captura de datos por puerto serial
    └── analizar_estabilidad_v6.py # Procesamiento de datos y gráficos
```

Demostración de Salida (CLI)

Ejemplo del reporte de análisis térmico y prueba ANOVA generado directamente en la consola al procesar el archivo de prueba data/raw_sample.csv:

![Demostración de la consola](./assets/console.output.png)

Tecnologías y Librerías

    Python 3.x

    PySerial: Comunicación con microcontroladores vía puerto serie.

    Pandas y NumPy: Manipulación, filtrado y cálculo de series de tiempo.

    SciPy: Evaluación estadística e inferencia mediante pruebas ANOVA (One-way ANOVA).

    Matplotlib: Renderizado y exportación de gráficos de estabilidad térmica a 300 DPI.

 Guía de Instalación y Uso

1. Instalación de Dependencias

Puedes instalar los requisitos usando el gestor de paquetes de tu distribución Linux o mediante un entorno virtual de Python (venv).

Basados en Debian / Ubuntu  (apt):

```pruebas
sudo apt update
sudo apt install python3-pandas python3-matplotlib python3-scipy python3-numpy python3-serial
```

Basados en Arch Linux (pacman):

```Bash
sudo pacman -S python-pandas python-matplotlib python-scipy python-numpy python-pyserial
```

Fedora (dnf):

```Bash
sudo dnf install python3-pandas python3-matplotlib python3-scipy python3-numpy python3-pyserial
```

Entorno Virtual (Windows / Genérico):

```Bash
python3 -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
# .\venv\Scripts\activate

pip install -r requirements.txt
```

1. Captura de Datos Seriales

Conecta el microcontrolador al puerto serial correspondiente (ej. /dev/ttyUSB0 en Linux o COM3 en Windows) y ejecuta:

```Bash
python3 scripts/capturar_datos.py
```

1. Análisis de Estabilidad y Generación de Reportes

Para procesar un dataset existente y generar los gráficos de estabilidad térmica:

```Bash
python3 scripts/analizar_estabilidad_v6.py
```

Los gráficos de salida se guardarán automáticamente en la carpeta `outputs/`.

Resultados del Análisis

El módulo de análisis calcula automáticamente:

    Time-to-Setpoint: Tiempo transcurrido hasta lograr una racha de estabilidad continua predefinida por canal independiente.

    Estabilidad Global del Sistema: Porcentaje de tiempo que cada zona permanece dentro de la ventana de tolerancia respecto a su setpoint individual.

    ANOVA (Comparación Multizona): Evaluación de diferencias significativas entre la respuesta térmica de los distintos canales.

    Visualización: Gráficos generales de comportamiento del sistema y reportes individuales por celda/zona.
