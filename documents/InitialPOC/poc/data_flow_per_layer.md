```
Capa	                    Componente	                Entrada	                   Salida
Percepción (ESP32)	      Sensor DS18B20	            Temperatura física (ºC)	   Valor digital float
                          Switch físico	              Presión mecánica	         0/1 digital
Comunicación (MQTT)	      Publicador ESP32	          Topic + payload	           Mensaje a broker
                          Suscriptor HA	              Mensaje MQTT	             Actualización de entidad
Procesamiento (HA Core)	  Comparador indoor/outdoor	  2 valores float	           Texto sugerencia
                          LLM (Ollama)	              Texto base	               Texto enriquecido
Actuación (ESP32)	        LED/Servo	                  Comando MQTT	             Movimiento físico
Visualización (HA UI)   	Dashboard	                  Estados + sugerencias	     HTML en PC
```