# Flujo del robot LabHabeasData (EP-001: HU-002, HU-003, HU-004)

Comandos por tipo: evaluateIf=19, execScriptPython=21, for=1, group=5, log_message=1, setVar=35, trycatch=2. Total: 84.

- **Control de errores**: Control de ejecución
  - **Grupo**: HU002HU003HU004 - Inicializar el Asistente
    - **Asignar**: Estado de la ejecución: estado, motivo si la selección queda vacía (HU-002), total de radicados y motivo de detención
    - **Asignar**: Radicados seleccionados por HU-002
    - **Asignar**: Radicados descartados por identificación ausente (HU-002)
    - **Asignar**: Radicados que avanzan a la validación de deuda (HU-004)
    - **Asignar**: Radicados en excepción de negocio 1 (HU-004)
    - **Asignar**: Radicados en excepción de sistema (HU-003, HU-004)
    - **Paso (componente)**: Carga los tres JSON de configuración, crea la estructura de carpetas y los dos logs del día
    - **Paso (componente)**: Lee los parámetros de negocio de la configuración (tipología, campo, literal de ausencia, lote, orden)
  - **Control de errores**: Proceso principal
    - **Grupo**: HU002 - Filtrar radicados de Exclusión de Datos
      - **Paso (componente)**: Solicita el token OAuth (client_credentials, vigencia 300 s); el secreto sale del Administrador de credenciales
      - **Si**: El token se obtuvo
        - **Asignar**: Arma la consulta de HU-002: filtro OData de la tipología ($filter, base de la selección), campos ($select), lote ($first) y orden ($orderby)
        - **Si**: Se descartan los radicados sin identificación (parámetro)
          - **Asignar**: Agrega al filtro: identificación distinta de «NO APORTA»
        - **Paso (componente)**: Consulta los radicados de exclusión (GET OData con $filter, $select, $first y $orderby)
        - **Si**: La consulta respondió
          - **Asignar**: Guarda los radicados seleccionados
          - **Paso (componente)**: Deja constancia en el log de auditoría de los radicados identificados
          - **Si**: Se descartan los radicados sin identificación (parámetro)
            - **Asignar**: Arma el filtro de los descartados: identificación igual a «NO APORTA»
            - **Paso (componente)**: Consulta los radicados descartados para no perderlos en silencio
            - **Si**: La consulta de descartados respondió
              - **Asignar**: Guarda los radicados descartados
              - **Paso (componente)**: Deja los descartados en el log de auditoría y en el reporte
              *(en caso contrario)*
              - **Asignar**: Marca la ejecución como detenida y guarda el motivo del paso que falló
          - **Si**: La selección quedó vacía y no hubo fallos
            - **Paso (componente)**: Consulta el total de radicados (consulta general, sin $filter)
            - **Si**: La consulta general respondió
              - **Asignar**: Total de radicados de la consulta general
              - **Si**: Todos los de la tipología fueron descartados
                - **Asignar**: Motivo: solo descartados
                *(en caso contrario)*
                - **Si**: Hay radicados, pero ninguno de la tipología
                  - **Asignar**: Motivo: tipología ausente
                  *(en caso contrario)*
                  - **Asignar**: Motivo: bandeja vacía
              - **Paso (componente)**: Registra «0 casos» y la cadencia del reintento (CADENCIA_REINTENTO_BANDEJA_VACIA)
              *(en caso contrario)*
              - **Asignar**: Marca la ejecución como detenida y guarda el motivo del paso que falló
          *(en caso contrario)*
          - **Asignar**: Marca la ejecución como detenida y guarda el motivo del paso que falló
        *(en caso contrario)*
        - **Asignar**: Marca la ejecución como detenida y guarda el motivo del paso que falló
    - **Si**: Hay radicados que procesar
      - **Para cada**: Iteración por radicado de exclusión
        - **Paso (componente)**: Deja constancia del inicio del radicado en el log de auditoría
        - **Grupo**: HU003 - Leer datos paramétricos
          - **Paso (componente)**: Lee el radicado por IDRADICADO (GET individual)
          - **Si**: El radicado se pudo leer
            - **Paso (componente)**: Limpia «No aporta» y vacíos (= ausente) y separa los valores de cada canal por «/»
            - **Paso (componente)**: Clasifica cada teléfono por dígitos: celular, fijo o sin clasificar
            *(en caso contrario)*
            - **Paso (componente)**: Registra la excepción de sistema del radicado (log de errores y reporte)
            - **Asignar**: Anota el radicado en excepciones de sistema
        - **Grupo**: HU004 - Validar campos obligatorios
          - **Asignar**: Lista de motivos de incompletitud (vacía al empezar cada radicado)
          - **Si**: Falta el nombre del cliente
            - **Asignar**: Agrega el motivo
          - **Si**: Falta el tipo de identificación
            - **Asignar**: Agrega el motivo
          - **Si**: Falta el número de identificación
            - **Asignar**: Agrega el motivo
          - **Si**: No hay ningún canal de contacto (ni correo ni teléfono)
            - **Asignar**: Agrega el motivo
          - **Si**: El caso está completo
            - **Paso (componente)**: Registra el avance a la validación de deuda en el reporte
            - **Asignar**: Anota el radicado en los que avanzan
          - **Si**: El caso está incompleto: excepción de negocio 1
            - **Paso (componente)**: Escribe el comentario de la excepción de negocio 1 en Gestión → Detalle
            - **Si**: El comentario quedó registrado
              - **Paso (componente)**: Registra la excepción de negocio 1 en el reporte
              - **Asignar**: Anota el radicado en excepciones de negocio 1
              *(en caso contrario)*
              - **Paso (componente)**: Registra la excepción de sistema (no se pudo escribir el comentario)
              - **Asignar**: Anota el radicado en excepciones de sistema
        - **Paso (componente)**: Deja constancia del fin del radicado en el log de auditoría
    *(en caso contrario)*
    - **Asignar**: Marca fallo de sistema en el proceso principal
    - **Asignar**: Estado de la ejecución: detenido por excepción de sistema
  - **Grupo**: HU002HU003HU004 - Cierre y registro de ejecución
    - **Si**: La ejecución se detuvo
      - **Paso (componente)**: Registra la detención en el log de errores y prepara el aviso «Detenido»
      - **Asignar**: Asunto del aviso que se enviará al equipo técnico
    - **Paso (componente)**: Cierra la ejecución y deja el resumen sin PII (en modo real los datos personales se enmascaran)
    - **Asignar**: Observación final de la corrida
    - **Asignar**: El proceso terminó sin detenerse
  *(en caso contrario)*
  - **Asignar**: Marca fallo de sistema
  - **Asignar**: Observación de la excepción de sistema
- **Log**: Traza final de la ejecución
