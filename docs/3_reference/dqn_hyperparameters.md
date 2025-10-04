# 🧠 DQN Hiperparámetros - Entrenamiento Simplificado

## 📚 Conceptos Base

### ¿Qué es DQN?
**Deep Q-Network (DQN)** es un algoritmo de aprendizaje por refuerzo que usa redes neuronales para aprender políticas de control. En nuestro caso, aprende a controlar semáforos para optimizar el flujo de tráfico.

### Conceptos Fundamentales

#### Q-Value (Valor Q)
Es una estimación de "qué tan buena" es una acción específica en un estado determinado. El modelo aprende a predecir estos valores para cada acción posible (cambio de semáforo) en cada estado (configuración actual del tráfico).

#### Target Network (Red Objetivo)
Es una copia de la red neuronal principal que se actualiza menos frecuentemente. Ayuda a estabilizar el entrenamiento evitando que el modelo "persiga un objetivo que está cambiando constantemente". Es como aprender a tirar al arco: necesitas una canasta fija para practicar, no una que se mueva cada vez que lanzas.

#### Experience Replay (Repetición de Experiencias)
Mecanismo que almacena las experiencias del agente [estado, acción, recompensa, estado_siguiente] en un búfer y las utiliza para entrenar de forma más eficiente, rompiendo la correlación temporal entre experiencias consecutivas. Es como estudiar: en lugar de repasar solo la última lección, revisas aleatoriamente diferentes temas de todo lo aprendido.

#### Epsilon-Greedy
Estrategia de exploración que balancea entre explotar conocimiento actual (elegir la mejor acción conocida) y explorar nuevas acciones (elegir aleatoriamente). Epsilon controla este balance. Es como elegir restaurante: a veces vas al que sabes que es bueno (explotación) y a veces pruebas uno nuevo (exploración).

#### Gradiente
Es la derivada de la función de pérdida (loss function) con respecto a los pesos de la red. Muestra la dirección y magnitud del cambio necesario en los pesos de la red neuronal para mejorar las predicciones. Es como bajar una montaña para llegar al valle más profundo (mínimo error): si das pasos largos puedes saltarte el valle óptimo, pero si das pasos muy cortos puedes quedarte atascado en una hondonada poco profunda (mínimo local).

#### Backpropagation (Retropropagación)
Proceso de propagar el gradiente basado en el error (TD-Error) desde la última capa hacia la primera. Empieza en las neuronas de salida y finaliza en la capa de entrada. Es el equivalente a juzgar los resultados de una empresa: se empieza por el CEO y se van repartiendo las responsabilidades en todo el árbol organizacional hacia abajo.

#### Gradient Clipping (Recorte de Gradientes)
Mecanismo crucial de protección que limita la magnitud de los gradientes. Es importante porque durante el entrenamiento puede haber momentos donde el error se dispara, provocando gradientes extremadamente grandes. Una acción de exploración aleatoria catastróficamente mala es una de las principales causas de la **explosión de gradientes**, donde un solo error puede desestabilizar toda la red. Gradient clipping protege la red completa de este colapso limitando los gradientes a un valor máximo seguro.

#### TD-Error (Error de Diferencia Temporal)
Número escalar que es el motor que impulsa el aprendizaje al cuantificar la "sorpresa" del agente. Indica la diferencia entre lo que pensaba antes vs ahora (predicción Q-value vs valor objetivo mejorado).

**Interpretación:**
- **Grande y positiva**: La decisión (Q-value) fue buena pero debe incrementarse porque tenía poca confianza
- **Cerca de cero**: La decisión fue acertada y el modelo "está seguro de ella"
- **Grande y negativa**: La decisión fue errónea y hay que bajar el valor Q

El "valor objetivo" no es realmente "real", sino una mejor estimación: `Recompensa + gamma * max_q_del_siguiente_estado`

### Diferencias Importantes

#### Hiperparámetro vs Parámetro vs Métrica
- **Hiperparámetro**: Configuración que defines antes del entrenamiento (ej: learning_rate, batch_size)
- **Parámetro**: Valores internos de la red neuronal que se aprenden automáticamente (pesos, sesgos)
- **Métrica**: Medida de rendimiento que observas después del entrenamiento (precisión, pérdida)

#### Overfitting (Sobreajuste)
El modelo aprende los resultados de memoria en vez de aprender la lógica o los patrones subyacentes. Cuando le das una experiencia que desconoce, no sabe qué hacer porque memorizó casos específicos en lugar de generalizar.

#### Hidden Layers (Capas Ocultas)
Todas las capas intermedias entre la capa de entrada y la capa de salida. Son las responsables de extraer y aprender características progresivamente más complejas de los datos.

#### Capas Densas (Dense Layers)
Capas donde cada neurona se conecta con cada neurona de la siguiente capa. Por ejemplo: una capa de 128 neuronas conectada a una de 64 tiene 128 × 64 = 8,192 conexiones. Esto permite que la red detecte más patrones y más rápido, pero aumenta el riesgo de overfitting.

#### Función de Activación ReLU
**ReLU** (Rectified Linear Unit) convierte valores negativos en 0 y mantiene los positivos sin cambios. Es muy eficiente computacionalmente y ayuda en el backpropagation. Sin embargo, algunas neuronas pueden "morir" al pasar permanentemente a valer cero (problema conocido como "dying ReLU").

#### He Initialization (Inicialización He)
Método de inicializar los pesos de las neuronas antes de empezar el entrenamiento. Es específico para redes que usan ReLU (ya que ReLU "mata" neuronas con valores negativos) y busca:
- Usar pesos más grandes para compensar
- Favorecer el correcto funcionamiento del backpropagation
- Prevenir problemas de desvanecimiento o explosión de gradientes

Los pesos son aleatorios pero se ajustan en función de la arquitectura de la red para un mejor inicio del entrenamiento.

#### Huber Loss (Pérdida de Huber)
Función de pérdida que tiene el mismo objetivo que MSE (Mean Squared Error) pero busca ser más estable para redes DQN. Combina lo mejor de dos mundos: se comporta como MSE para errores pequeños (cuadrático) y como MAE (error absoluto) para errores grandes, haciéndola más robusta ante valores atípicos.

#### Double DQN vs DQN Estándar
- **DQN Estándar**: Debe estimar el valor futuro de sus acciones (valor Q) pero usa la misma red tanto para seleccionar la mejor acción futura como para evaluar su valor. Esto es equivalente a un estudiante que debe elegir su mejor tarea y también ponerle la nota. Como él mismo la hizo, tiene un sesgo optimista. Si cree erróneamente que una tarea es la mejor, la elegirá y además le pondrá una nota altísima, reforzando su propio sesgo. Este problema se conoce como **sesgo de maximización**.

- **Double DQN**: Resuelve el sesgo de maximización utilizando las dos redes (Online y Target) de forma más inteligente:
  1. **Red Online** (entrenada continuamente): Mira el siguiente estado y selecciona cuál cree que es la mejor acción
  2. **Red Target** (checkpoint estable): Toma esa acción seleccionada y la evalúa, proporcionando el valor Q final

  Hay dos "entidades" diferentes: una que propone la mejor jugada (estudiante actualizado) y otra más conservadora e imparcial que le pone la nota (evaluador externo). Esto requiere dos inferencias durante el cálculo del valor objetivo en el entrenamiento, pero reduce drásticamente la sobreestimación.

#### Dueling DQN vs DQN Estándar
- **DQN Estándar**: Aprende directamente Q(s,a) = valor de hacer acción 'a' en estado 's'

- **Dueling DQN**: Cambia la arquitectura interna de la red. En lugar de calcular directamente el valor Q, la red se divide en dos flujos que calculan dos componentes por separado:
  - **Valor del Estado V(s)**: Qué tan bueno o malo es el estado actual en general, sin importar la acción
  - **Ventaja de la Acción A(s,a)**: Qué tan buena es cada acción en comparación con las otras en ese estado específico

  Al final, la red combina estas dos estimaciones para obtener el valor Q final. Esto permite un aprendizaje más eficiente, especialmente en estados donde el valor no depende fuertemente de la acción que se tome.

  **Implementación:**
  ```
                                      +--> [Dense x2] --> [Dense 1 (V)] --+
                                      |                                    |
          Input --> [Dense x1] --(bifurcación)                      [Combinación] --> Q-Values
                                      |                                    |
                                      +--> [Dense x2] --> [Dense 16 (A)]--+
  ```
  - **x1**: Todas menos la última capa oculta
  - **x2**: Última capa oculta para cada stream (V y A)

---

## ⚙️ Hiperparámetros del Entrenamiento Simplificado

### 🎯 Entrenamiento Principal

#### `entrenar`
Activa o desactiva el proceso de entrenamiento del agente DQN. Cuando está en `false`, el sistema usa un modelo pre-entrenado para tomar decisiones.

#### `num_epocas`
Número total de ciclos completos de entrenamiento. Cada época incluye múltiples episodios de simulación donde el agente aprende de sus decisiones.

#### `steps`
Cantidad de pasos de simulación SUMO entre cada decisión del agente. Un valor más alto significa que el agente toma decisiones menos frecuentemente, dando más tiempo para observar los efectos de sus acciones.

### 💾 Sistema de Memoria (Experience Replay)

#### `memory`
Tamaño total del búfer de repetición de experiencias. Es como un libro de texto completo que contiene todas las experiencias [estado, acción, recompensa, estado_futuro] que el agente ha vivido.

#### `min_replay_size`
Número mínimo de experiencias que debe tener el búfer antes de empezar el entrenamiento. Es la regla: "No empezaré a hacer tests de práctica hasta que haya leído al menos los primeros capítulos para tener una base sólida".

#### `batch_size`
Cantidad de experiencias aleatorias que se seleccionan del búfer para cada actualización de la red. Es como estudiar para un examen: cada día tomas 256 páginas al azar del libro y repasas esos ejemplos, en lugar de releer todo el libro o estudiar una sola frase.

### 🔍 Exploración (Epsilon-Greedy)

#### `epsilon`
Nivel inicial de exploración (1.0 = 100% aleatorio). Al principio el modelo no sabe nada, por lo que debe tomar decisiones completamente aleatorias para evaluarlas y aprender si son buenas o malas.

#### `epsilon_decay`
Factor por el que se reduce epsilon cada época. Un valor de 0.95 significa que el nivel de exploración se reduce al 95% del valor anterior cada época, disminuyendo gradualmente la aleatoriedad.

#### `epsilon_min`
Nivel mínimo de exploración (0.1 = 10% aleatorio). Incluso cuando el modelo está bien entrenado, mantiene un 10% de acciones aleatorias para seguir descubriendo nuevas estrategias.

### 🧠 Arquitectura de Red

#### `learning_rate`
Controla qué tan agresivamente la red neuronal actualiza sus pesos en cada paso de entrenamiento. Un valor conservador que permite aprendizaje estable sin oscilaciones.

#### `gamma`
Factor de descuento que determina qué tan importantes son las recompensas futuras versus las inmediatas. Un valor de 0.90 significa que una recompensa futura vale 90% de una recompensa inmediata.

#### `hidden_layers`
Define la arquitectura de la red neuronal: dos capas ocultas con 128 y 64 neuronas respectivamente. Esta configuración balanceada permite suficiente capacidad de aprendizaje sin complejidad excesiva.

### 🎯 Algoritmos DQN

#### `use_double_dqn`
Activa Double DQN, una mejora que reduce la sobreestimación de Q-values usando dos redes neuronales para decisiones más estables.

#### `use_dueling_dqn`
Activa Dueling DQN, que separa la estimación del valor del estado de la ventaja de cada acción, mejorando el aprendizaje en estados donde las acciones tienen efectos similares.

#### `target_update_frequency`
Frecuencia (en steps de entrenamiento) con la que se actualiza la target network. Una actualización menos frecuente proporciona objetivos más estables durante el entrenamiento.

### ⚙️ Estabilización del Entrenamiento

#### `warmup_steps`
Pasos iniciales donde el modelo solo recolecta experiencias sin entrenar, permitiendo que la simulación se estabilice antes de comenzar el aprendizaje.

#### `use_gradient_clipping`
Activa el recorte de gradientes para prevenir el "gradient explosion", donde los gradientes se vuelven demasiado grandes y desestabilizan el entrenamiento.

#### `gradient_clip_norm`
Valor máximo permitido para la norma de los gradientes. Si un gradiente excede este valor, se escala hacia abajo para mantener la estabilidad.

#### `use_huber_loss`
Activa la función de pérdida Huber, que es más robusta a valores atípicos que el error cuadrático medio (MSE), proporcionando entrenamiento más estable.

#### `use_he_initialization`
Activa la inicialización He para los pesos de la red neuronal, una técnica estándar que ayuda a prevenir problemas de gradientes desvanecidos al inicio del entrenamiento.

### 📊 Evaluación y Monitoreo

#### `enable_evaluation`
Activa la evaluación periódica del modelo durante el entrenamiento, permitiendo monitorear el progreso y detectar problemas de convergencia.

#### `evaluation_episodes`
Número de episodios de simulación usados para cada evaluación. Más episodios proporcionan evaluaciones más precisas pero requieren más tiempo computacional.

#### `evaluation_frequency`
Frecuencia (en épocas) con la que se realizan las evaluaciones. Una evaluación cada 5 épocas permite monitoreo regular sin impacto significativo en el tiempo de entrenamiento.

### ⏹️ Early Stopping

#### `patience`
Número de épocas consecutivas sin mejora antes de detener automáticamente el entrenamiento. Previene el entrenamiento innecesario cuando el modelo ya ha convergido.

#### `min_improvement`
Mejora mínima requerida en la métrica de evaluación para considerar que el modelo está progresando. Ayuda a distinguir mejoras reales del ruido estadístico.

---

## 📁 Archivos de Resultados

#### `path_resultado`
Directorio donde se guardan todos los resultados del entrenamiento:
- **Modelos entrenados** (archivos .h5)
- **Métricas de entrenamiento** (CSV con loss, recompensas, etc.)
- **Logs de configuración** (hiperparámetros usados)
- **Gráficos de progreso** (si están habilitados)
