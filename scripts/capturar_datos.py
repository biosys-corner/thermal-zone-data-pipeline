import serial
import datetime
from pathlib import Path

# --- RUTAS DINÁMICAS ---
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"

# Crear la carpeta data si no existe
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuración
# Encuentra el puerto correcto. Conecta el ESP32 y ejecuta en la terminal: dmesg | grep tty
SERIAL_PORT = "/dev/ttyUSB0"  # Cambia esto por tu puerto serial
BAUD_RATE = 115200

# Inicio del Script
print("Bienvenido al script de captura de datos para el test de estabilidad.")
print(f"Escuchando en el puerto: {SERIAL_PORT} a {BAUD_RATE} baudios.")
print("Presiona el botón '#' en el control remoto para iniciar/detener el registro.")
print("Presiona Ctrl+C en esta terminal para salir del script.")

try:
    # Inicia la conexión con el ESP32
    esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    csv_file = None
    is_logging = False

    while True:
        # Lee una línea de datos desde el ESP32
        line = esp32.readline().decode("utf-8").strip()

        if line == "LOGGING_START":
            if not is_logging:
                is_logging = True
                # Crea un nombre de archivo único con la fecha y hora actual
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = DATA_DIR / f"estabilidad_test_{timestamp}.csv"
                csv_file = open(filename, "w", newline="")
                # Escribe la cabecera del CSV
                csv_file.write(
                    "timestamp_ms,peltier1_C,peltier2_C,peltier3_C,peltier4_C,peltier5_C\n"
                )
                print(f"\n>>> REGISTRO INICIADO. Guardando datos en '{filename}'...")

        elif line == "LOGGING_END":
            if is_logging:
                is_logging = False
                if csv_file:
                    csv_file.close()
                    print(f">>> REGISTRO DETENIDO. Archivo '{filename}' guardado.")
                    csv_file = None

        elif is_logging and csv_file and "," in line:
            # Si el registro está activo y la línea parece ser un CSV válido, la guardamos
            csv_file.write(line + "\n")
            # Imprime la última línea en la consola para ver el progreso (opcional)
            print(f"  Datos: {line}", end="\r")


except serial.SerialException as e:
    print(f"\nError: No se pudo abrir el puerto serial '{SERIAL_PORT}'.")
    print(
        "Asegúrate de que el ESP32 esté conectado y que el nombre del puerto sea correcto."
    )
    print(f"Detalle del error: {e}")

except KeyboardInterrupt:
    print("\n\nScript interrumpido por el usuario. Cerrando archivos...")

finally:
    if csv_file:
        csv_file.close()
        print("Archivo CSV cerrado correctamente.")
    print("Programa finalizado.")
