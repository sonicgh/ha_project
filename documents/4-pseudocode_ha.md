```
# ============================================================
# PSEUDOCÓDIGO: HOME ASSISTANT - AUTOMATION Y LLM
# ============================================================

# Automation 1: Obtener clima externo cada 10 minutos
TRIGGER:
    - platform: time_pattern
      minutes: "/10"
ACTION:
    - service: weather.get_forecast
      target:
        entity_id: weather.openmeteo_home
      data:
        type: "current"
    - service: input_number.set_value
      target:
        entity_id: input_number.external_temp
      data:
        value: "{{ state_attr('weather.openmeteo_home', 'temperature') }}"

# Automation 2: Comparar temperaturas y sugerir acción
TRIGGER:
    - platform: state
      entity_id: sensor.livingroom_temp
    - platform: state
      entity_id: input_number.external_temp
ACTION:
    - variables:
        indoor: "{{ states('sensor.livingroom_temp') | float }}"
        outdoor: "{{ states('input_number.external_temp') | float }}"
    - service: input_text.set_value
      target:
        entity_id: input_text.suggestion_basic
      data:
        value: >
          {% if indoor > outdoor + 2 %}
            Hace más calor dentro. Abre una ventana o activa ventilación.
          {% elif indoor < outdoor - 2 %}
            Hace más frío dentro. Cierra ventanas o aumenta calefacción.
          {% else %}
            Temperatura equilibrada. No se requiere acción.
          {% endif %}
    
    # (Opcional) Enviar a LLM local
    if (llm_available == true):
        - service: ollama.generate
          data:
            prompt: "Reescribe esta sugerencia de forma amigable y natural: {{ states('input_text.suggestion_basic') }}"
            model: "llama3.2:latest"
          response_variable: llm_response
        - service: input_text.set_value
          target:
            entity_id: input_text.suggestion_llm
          data:
            value: "{{ llm_response.text }}"

# Automation 3: Loggear todos los cambios de estado
TRIGGER:
    - platform: state
      entity_id: 
        - sensor.livingroom_temp
        - binary_sensor.switch
        - light.led
        - number.servo_position
ACTION:
    - service: system_log.write
      data:
        message: "{{ trigger.entity_id }} cambió a {{ trigger.to_state.state }}"
        level: "info"
```