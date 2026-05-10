```
// ============================================================
// PSEUDOCÓDIGO: ESP32 - FIRMWARE PRINCIPAL
// ============================================================

INICIALIZAR:
    Conectar WiFi(SSID, PASSWORD)
    Conectar MQTT(broker_IP, puerto=1883)
    Configurar pines:
        LED = GPIO2 como salida
        SWITCH = GPIO4 como entrada con pull-up
        SERVO = GPIO5 como salida PWM
        DS18B20 = GPIO18 como bus 1-wire
    
    MQTT_subscribir("home/livingroom/led/set")
    MQTT_subscribir("home/livingroom/servo/set")
    
    Publicar MQTT("home/livingroom/led/state", "OFF")
    Publicar MQTT("home/livingroom/servo/state", "0")
    
    timer_temp = 0
    estado_switch_anterior = LeerSwitch()

// ============================================================
BUCLE_PRINCIPAL (cada 100ms):
// ============================================================
    // 1. Mantener conexiones
    Si WiFi desconectado: Reconectar()
    Si MQTT desconectado: ReconectarMQTT()
    
    // 2. Leer switch físico (con debounce)
    estado_actual_switch = LeerSwitch()
    Si estado_actual_switch != estado_switch_anterior:
        MQTT_publicar("home/livingroom/switch/state", estado_actual_switch)
        estado_switch_anterior = estado_actual_switch
    
    // 3. Procesar comandos MQTT entrantes (callback)
    SI llega mensaje en "home/livingroom/led/set":
        nuevo_estado = payload (ON/OFF)
        Escribir LED = nuevo_estado
        MQTT_publicar("home/livingroom/led/state", nuevo_estado)
    
    SI llega mensaje en "home/livingroom/servo/set":
        angulo = payload (0-180)
        MoverServo(angulo)
        MQTT_publicar("home/livingroom/servo/state", angulo)
    
    // 4. Leer temperatura cada 30 segundos
    SI (millis() - timer_temp >= 30000):
        temperatura = LeerDS18B20()
        Si temperatura válida:
            MQTT_publicar("home/livingroom/temp", temperatura)
        timer_temp = millis()
    
    Pequeña_demora(10ms)  // evitar sobrecarga de CPU

// ============================================================
FUNCIONES AUXILIARES:
// ============================================================
FUNCION LeerSwitch():
    // Debounce por software (30ms)
    lectura_actual = digitalRead(SWITCH)
    Si (lectura_actual == prev_debounced):
        contador_debounce = 0
    Sino:
        contador_debounce++
        Si contador_debounce > 3:
            prev_debounced = lectura_actual
    Devolver prev_debounced (0 = presionado, 1 = liberado)

FUNCION MoverServo(angulo):
    Señal PWM = map(angulo, 0, 180, 500, 2400) microsegundos
    Escribir en GPIO5
```