# Diagram:

```
[INICIO] → [ESP32 se conecta a WiFi y MQTT] → [ESP32 publica estado inicial de dispositivos]
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ESP32 - Bucle principal (cada 100ms)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  │                                                                          │
│  ├──> ¿Cambió el estado físico del Switch? ──Sí──> Publicar MQTT "switch"  │
│  │                                                                          │
│  ├──> ¿Llegó mensaje MQTT "led/set"? ──Sí──> Cambiar LED                    │
│  │                                                                          │
│  ├──> ¿Llegó mensaje MQTT "servo/set"? ──Sí──> Mover servomotor             │
│  │                                                                          │
│  └──> ¿Han pasado 30s desde último temp? ──Sí──> Leer DS18B20 → Publicar    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼ MQTT
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HOME ASSISTANT (Raspberry Pi / PC)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [MQTT Broker Mosquitto] ←── Recibe topics: temp, switch, state             │
│         │                                                                    │
│         ▼                                                                    │
│  [Home Assistant Core]                                                       │
│         │                                                                    │
│         ├──> Actualiza entidades (LED, temp, switch, servo)                 │
│         │                                                                    │
│         ├──> [Automation: Cada 10 min]                                      │
│         │         │                                                          │
│         │         ▼                                                          │
│         │    Llama a Open-Meteo (clima ciudad)                              │
│         │         │                                                          │
│         │         ▼                                                          │
│         │    Compara temp_indoor vs temp_outdoor                            │
│         │         │                                                          │
│         │         ├──> Genera sugerencia textual (reglas)                   │
│         │         │                                                          │
│         │         └──> (Opcional) Envía sugerencia a Ollama (LLM local)    │
│         │                   │                                                │
│         │                   └──> LLM devuelve sugerencia en lenguaje natural│
│         │                                                                    │
│         ├──> [Logging] Guarda cada evento y sensor en InfluxDB/SQLite       │
│         │                                                                    │
│         └──> [Dashboard Web] Muestra en PC:                                 │
│                  - Temperatura actual                                        │
│                  - Botón LED                                                 │
│                  - Slider servomotor                                        │
│                  - Sugerencia de confort                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Puertos 8123 (HTTP) y 1883 (MQTT)
                                       ▼
                              [PC del Usuario - Navegador]
                               (monitoreo y control manual)
```