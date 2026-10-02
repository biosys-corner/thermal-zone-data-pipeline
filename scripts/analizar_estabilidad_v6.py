import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
from matplotlib.patches import Patch
from pathlib import Path

# --- RUTAS DINÁMICAS (Multiplataforma y seguras) ---
# __file__ es este script (scripts/analizar_estabilidad_v6.py)
# .parent es la carpeta 'scripts'
# .parent.parent es la raíz del proyecto ('thermal-zone-data-pipeline')
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

# Carpetas de datos y salidas relativas a la raíz
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

# Crear la carpeta outputs si no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Configuración del analisis
# Archivo de entrada
CSV_FILENAME = (
    DATA_DIR / "raw_sample.csv"
)  # Dentro de las comillas debe ir el nombre del .csv a analizar
SETPOINTS_C = [
    10.0,
    20.0,
    28.0,
    37.0,
    46.0,
]  # Dentro de los corchetes debe ir las temperaturas setpoint a analizar, de izquierda a derecha
TOLERANCE_C = 0.5
STABILITY_THRESHOLD_PERCENT = 95.0
MIN_CONTINUOUS_STABILITY_MINUTES = 5


# Función auxiliar
def format_minutes_to_mmss(decimal_minutes):
    """Convierte minutos decimales a un formato de string MM:SS."""
    if decimal_minutes == float("inf"):
        return "N/A"
    minutes = int(decimal_minutes)
    seconds = int(round((decimal_minutes - minutes) * 60))
    return f"{minutes}:{seconds:02d}"


# Inicio del script de análisis
try:
    print(f"--- Cargando datos desde '{CSV_FILENAME}' ---")
    df = pd.read_csv(CSV_FILENAME)
except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{CSV_FILENAME}'.")
    exit()

# 1. Resumen y Duración del Experimento
print("\n--- 1. Resumen del Experimento ---")
df["time_hours"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / (1000 * 3600)
duration_hours = df["time_hours"].iloc[-1]
duration_ms = df["timestamp_ms"].iloc[-1] - df["timestamp_ms"].iloc[0]
total_seconds = int(duration_ms // 1000)
hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60
duration_str = f"{hours}h {minutes}m {seconds}s"
print(f"Duración precisa del registro: {duration_str}")

# 2A. Análisis de Estabilidad Individual
print(f"\n--- 2A. Análisis de Estabilidad Individual ---")
print(
    f"Buscando el inicio de la estabilidad (temp. en rango por {MIN_CONTINUOUS_STABILITY_MINUTES} min. continuos)"
)
window_size = int(MIN_CONTINUOUS_STABILITY_MINUTES * 60 * 2)
time_to_setpoint_results = {}
stability_start_times_hours = {}
for i in range(5):
    peltier_col = f"peltier{i + 1}_C"
    setpoint = SETPOINTS_C[i]
    lower_bound = setpoint - TOLERANCE_C
    upper_bound = setpoint + TOLERANCE_C
    df["in_range"] = df[peltier_col].between(lower_bound, upper_bound)
    df["stable_streak"] = df["in_range"].rolling(window=window_size).sum()
    first_stable_series = df[df["stable_streak"] == window_size]
    if not first_stable_series.empty:
        first_stable_index = first_stable_series.index[0]
        time_to_setpoint_ms = (
            df["timestamp_ms"].loc[first_stable_index] - df["timestamp_ms"].iloc[0]
        )
        time_to_setpoint_results[peltier_col] = time_to_setpoint_ms / 60000.0
        stability_start_times_hours[peltier_col] = df["time_hours"].loc[
            first_stable_index
        ]
    else:
        print(f"  - ADVERTENCIA: ¡{peltier_col} nunca alcanzó la estabilidad continua!")
        time_to_setpoint_results[peltier_col] = float("inf")
        stability_start_times_hours[peltier_col] = None
print("\nResultados de 'Tiempo para Alcanzar Estabilidad Sostenida':")
for peltier, minutes in time_to_setpoint_results.items():
    time_str = format_minutes_to_mmss(minutes)
    print(f"  - {peltier}: {time_str} (min:seg)")

# 2B. Análisis de Estabilidad del Sistema (Inicio Global)
print("\n--- 2B. Análisis de Estabilidad del Sistema (Inicio Global) ---")
global_start_time_ms = 0
for peltier, minutes in time_to_setpoint_results.items():
    if minutes != float("inf"):
        ms = minutes * 60000
        if ms > global_start_time_ms:
            global_start_time_ms = ms
global_start_minutes = global_start_time_ms / 60000.0
print(
    f"El sistema completo se considera estable después de {format_minutes_to_mmss(global_start_minutes)} (min:seg)."
)
global_start_timestamp = df["timestamp_ms"].iloc[0] + global_start_time_ms
df_stable_global = df[df["timestamp_ms"] >= global_start_timestamp].copy()
global_stability_results = {}
all_stable_global = True
for i in range(5):
    peltier_col = f"peltier{i + 1}_C"
    setpoint = SETPOINTS_C[i]
    lower_bound = setpoint - TOLERANCE_C
    upper_bound = setpoint + TOLERANCE_C
    stable_points = (
        df_stable_global[peltier_col].between(lower_bound, upper_bound).sum()
    )
    total_points = len(df_stable_global)
    if total_points > 0:
        percentage = (stable_points / total_points) * 100
        global_stability_results[peltier_col] = percentage
        if percentage < STABILITY_THRESHOLD_PERCENT:
            all_stable_global = False
    else:
        global_stability_results[peltier_col] = 0
print("\nPorcentaje de tiempo dentro del rango (en el periodo de estabilidad global):")
for peltier, perc in global_stability_results.items():
    print(f"  - {peltier}: {perc:.2f}%")
print(
    f"\n¿Sistema globalmente estable? (Todas las celdas > {STABILITY_THRESHOLD_PERCENT}%): {all_stable_global}"
)


# 3. Análisis Estadístico ANOVA
print("\n--- 3. Análisis ANOVA (Comparación de Medias en PERIODO ESTABLE GLOBAL) ---")
if not df_stable_global.empty:
    f_stat_total, p_value_total = stats.f_oneway(
        df_stable_global["peltier1_C"],
        df_stable_global["peltier2_C"],
        df_stable_global["peltier3_C"],
        df_stable_global["peltier4_C"],
        df_stable_global["peltier5_C"],
    )
    print("\nResultados ANOVA para el TIEMPO TOTAL del periodo estable global:")
    print(f"  - Estadístico F: {f_stat_total:.4f}")
    print(f"  - P-valor: {p_value_total:.4f}")
    if p_value_total < 0.05:
        print(
            "  - Conclusión: Se encontraron diferencias significativas entre las medias de las celdas."
        )
    else:
        print(
            "  - Conclusión: No hay evidencia de diferencias significativas entre las medias."
        )
else:
    print("No hay datos en el periodo estable global para realizar el análisis ANOVA.")

# 4. Generación de Gráfico General
print("\n--- 4. Generando Gráfico General ---")
plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(15, 8))
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# Dibuja las curvas y las líneas de estabilización
for i in range(5):
    peltier_col = f"peltier{i + 1}_C"
    setpoint = SETPOINTS_C[i]

    # Dibuja la curva principal de temperatura
    ax.plot(
        df["time_hours"],
        df[peltier_col],
        color=colors[i],
        linewidth=1.5,
        label=f"Peltier {i + 1} ({setpoint:.1f}°C)",
    )

    # Dibuja la línea de setpoint
    ax.axhline(y=setpoint, color=colors[i], linestyle="--", linewidth=1, alpha=0.8)

    # Dibuja las bandas de tolerancia (sin etiqueta)
    ax.fill_between(
        df["time_hours"],
        setpoint - TOLERANCE_C,
        setpoint + TOLERANCE_C,
        color=colors[i],
        alpha=0.1,
    )

    # Dibuja la línea vertical de estabilización (sin texto)
    start_hour = stability_start_times_hours.get(peltier_col)
    if start_hour is not None:
        ax.axvline(x=start_hour, color=colors[i], linestyle=":", linewidth=2)

# Construye la leyenda
handles, labels = ax.get_legend_handles_labels()
# Añade un elemento único para la tolerancia a la leyenda
tolerance_patch = Patch(
    facecolor="gray",
    edgecolor="none",
    alpha=0.3,
    label=f"Tolerancia (±{TOLERANCE_C}°C)",
)
handles.append(tolerance_patch)
ax.legend(handles=handles, title=None, bbox_to_anchor=(1.04, 1), loc="upper left")

# Configuración final del gráfico
ax.set_title(f"Análisis de Estabilidad Térmica ({duration_str})", fontsize=16)
ax.set_xlabel("Tiempo (t) en horas", fontsize=12)
ax.set_ylabel("Temperatura (T) en °C", fontsize=12)
ax.grid(True, which="both", linestyle="--", linewidth=0.5)
fig.tight_layout(rect=[0, 0, 0.9, 1])

# Guardar el gráfico
plot_filename = OUTPUT_DIR / f"{CSV_FILENAME.stem}_plot.png"
plt.savefig(plot_filename, dpi=300, bbox_inches="tight")
print(f"Gráfico guardado como '{plot_filename}'")
plt.show()

# 5. Generación de Gráficos Individuales
print("\n--- 5. Generando Gráficos Individuales ---")
for i in range(5):
    peltier_col = f"peltier{i + 1}_C"
    setpoint = SETPOINTS_C[i]
    fig_ind, ax_ind = plt.subplots(figsize=(12, 7))
    ax_ind.plot(
        df["time_hours"],
        df[peltier_col],
        label=f"Peltier {i + 1} Temp.",
        color=colors[i],
        linewidth=1.5,
    )
    ax_ind.axhline(
        y=setpoint,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Setpoint ({setpoint}°C)",
    )
    ax_ind.fill_between(
        df["time_hours"],
        setpoint - TOLERANCE_C,
        setpoint + TOLERANCE_C,
        color="gray",
        alpha=0.3,
        label=f"Tolerancia (±{TOLERANCE_C}°C)",
    )
    ax_ind.set_ylim(setpoint - (TOLERANCE_C * 4), setpoint + (TOLERANCE_C * 4))

    ax_ind.set_title(
        f"Análisis de Estabilidad - Peltier {i + 1} a {setpoint}°C", fontsize=16
    )
    ax_ind.set_xlabel("Tiempo (t) en horas", fontsize=12)
    ax_ind.set_ylabel("Temperatura (T) en °C", fontsize=12)

    minutes_to_stable = time_to_setpoint_results.get(peltier_col, 0)
    time_str = format_minutes_to_mmss(minutes_to_stable)
    text_label = f"Tiempo de Estabilidad:\n{time_str} (min:seg)"
    ax_ind.text(
        0.95,
        0.95,
        text_label,
        transform=ax_ind.transAxes,
        fontsize=12,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.7),
    )

    ax_ind.legend()
    ax_ind.grid(True, which="both", linestyle="--", linewidth=0.5)
    plot_ind_filename = OUTPUT_DIR / f"{CSV_FILENAME.stem}_plot_Peltier_{i + 1}.png"
    plt.savefig(plot_ind_filename, dpi=300, bbox_inches="tight")
    plt.close(fig_ind)
    print(f"Gráfico individual guardado como '{plot_ind_filename}'")
