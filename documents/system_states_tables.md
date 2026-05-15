```
Estado del sistema	ESP32 acción	                                            HA acción	                                          UI en PC
Arranque	          Conectar WiFi/MQTT, inicializar sensores	                Esperar MQTT	                                      "Conectando..."
Normal	            Publicar temp c/30s, switch c/cambio, escuchar comandos	  Mostrar dash, ejecutar automatizaciones	            Controles activos, gráficas actualizadas
Sin WiFi	          Intentar reconexión cada 5s	                              Mostrar "ESP32 offline"	                            Mensaje de error, controles deshabilitados
Sugerencia activa	  (sin cambio)	                                            Comparar indoor/outdoor, generar texto	            Caja de sugerencia visible
LLM consultando	    (sin cambio)	                                            Enviar prompt a Ollama, esperar respuesta (máx 5s)	"Generando sugerencia avanzada..."
Logging	            (sin cambio)	                                            Guardar en BD	                                      Historial accesible
```