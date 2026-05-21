from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import json

def seed_db():
    # Dropping and recreating tables to apply schema changes
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    exercises = [
        # PECHO (Chest)
        {
            "name": "Press de Banca con Barra",
            "muscle_group": "Pecho",
            "equipment": "Barra",
            "difficulty": "Intermedio",
            "description": "El ejercicio básico para la fuerza y masa del pectoral.",
            "technique": "1. Acuéstate en el banco con los pies plantados. 2. Baja la barra al pecho medio. 3. Empuja con fuerza manteniendo los codos a 45 grados.",
            "tips": "No bloquees los codos totalmente arriba para mantener la tensión.",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Mayor, Deltoides Anterior, Tríceps"
        },
        {
            "name": "Press en Maquina Convergente",
            "muscle_group": "Pecho",
            "equipment": "Maquinaria",
            "difficulty": "Principiante",
            "description": "Trayectoria guiada para maximo aislamiento pectoral.",
            "technique": "1. Ajusta el asiento para que los agarres esten a nivel del pecho medio. 2. Empuja hacia adelante extendiendo brazos. 3. Regresa controlando la carga.",
            "tips": "Mantén los hombros pegados al respaldo.",
            "image_url": "https://images.unsplash.com/photo-1594737625785-a239f56d0bd1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Mayor, Triceps"
        },
        {
            "name": "Press Inclinado con Mancuernas",
            "muscle_group": "Pecho",
            "equipment": "Mancuernas",
            "difficulty": "Intermedio",
            "description": "Enfoque en la parte superior del pectoral (clavicular).",
            "technique": "1. Banco a 30-45 grados. 2. Baja las mancuernas a los lados del pecho. 3. Junta arriba sin chocar las pesas.",
            "tips": "Siente el estiramiento en la parte superior del pecho.",
            "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Superior, Deltoides Anterior"
        },
        {
            "name": "Aperturas en Peck Deck",
            "muscle_group": "Pecho",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Aislamiento pectoral sin fatiga de tríceps.",
            "technique": "1. Ajusta los brazos de la máquina. 2. Junta las manos frente al pecho. 3. Abre lentamente controlando el peso.",
            "tips": "Mantén una ligera flexión en los codos.",
            "image_url": "https://images.unsplash.com/photo-1594737625785-a239f56d0bd1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Mayor, Pectoral Menor"
        },
        {
            "name": "Cruces de Polea Alta",
            "muscle_group": "Pecho",
            "equipment": "Cables",
            "difficulty": "Intermedio",
            "description": "Tensión constante para la parte inferior y externa del pecho.",
            "technique": "1. Una polea en cada mano. 2. Paso al frente e inclina el torso. 3. Cruza las manos a la altura de la cintura.",
            "tips": "Aprieta el pecho un segundo en el punto máximo de contracción.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Mayor (Fibras Inferiores)"
        },
        {
            "name": "Flexiones de Pecho (Push-ups)",
            "muscle_group": "Pecho",
            "equipment": "Corporal",
            "difficulty": "Principiante",
            "description": "Ejercicio basico de empuje con peso corporal.",
            "technique": "1. Posicion de plancha alta. 2. Baja el pecho casi al suelo. 3. Empuja hacia arriba manteniendo el core firme.",
            "tips": "No dejes que la cadera caiga.",
            "image_url": "https://images.unsplash.com/photo-1598971639058-aba7c18f2a2e?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Pectoral Mayor, Triceps, Core"
        },

        # ESPALDA (Back)
        {
            "name": "Jalón al Pecho (Agarre Ancho)",
            "muscle_group": "Espalda",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Alternativa fundamental a las dominadas para anchura de espalda.",
            "technique": "1. Siéntate con los muslos fijos. 2. Tira de la barra hacia la parte superior del esternón. 3. Estira los brazos completamente arriba.",
            "tips": "No uses el impulso del cuerpo hacia atrás.",
            "image_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Dorsal Ancho, Bíceps, Braquial"
        },
        {
            "name": "Dominadas (Pull-ups)",
            "muscle_group": "Espalda",
            "equipment": "Barra Fija",
            "difficulty": "Avanzado",
            "description": "El rey de los ejercicios de traccion para espalda.",
            "technique": "1. Cuelgate de la barra con agarre ancho. 2. Tira hacia arriba hasta que la barbilla supere la barra. 3. Baja lentamente.",
            "tips": "Retrae las escapulas antes de iniciar el tiron.",
            "image_url": "https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Dorsal Ancho, Trapecio, Biceps"
        },
        {
            "name": "Remo con Barra",
            "muscle_group": "Espalda",
            "equipment": "Barra",
            "difficulty": "Intermedio",
            "description": "Constructor de densidad y fuerza en la espalda media.",
            "technique": "1. Flexiona rodillas y torso a 45 grados. 2. Tira de la barra al ombligo. 3. Retrae las escápulas atrás.",
            "tips": "Mantén la espalda recta en todo momento.",
            "image_url": "https://images.unsplash.com/photo-1590487949411-2c58ed91cdef?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Dorsales, Trapecio Medio, Romboides"
        },
        {
            "name": "Remo en Polea Baja (Gironda)",
            "muscle_group": "Espalda",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Control máximo del movimiento de tracción.",
            "technique": "1. Pies apoyados y rodillas semi-flexas. 2. Tira del triángulo al abdomen. 3. Extiende brazos sin perder la postura.",
            "tips": "Lleva los codos lo más atrás posible.",
            "image_url": "https://images.unsplash.com/photo-1591940742878-13aba4b7a35e?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Espalda Baja, Dorsales, Trapecio"
        },
        {
            "name": "Remo en Maquina T-Bar",
            "muscle_group": "Espalda",
            "equipment": "Maquinaria",
            "difficulty": "Intermedio",
            "description": "Densidad brutal para la espalda media.",
            "technique": "1. Apoya el pecho en el pad. 2. Sujeta los agarres y tira hacia arriba. 3. Estira brazos al maximo abajo.",
            "tips": "No levantes el pecho del apoyo.",
            "image_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Trapecio, Romboides, Dorsal"
        },
        {
            "name": "Pull-Over en Polea Alta",
            "muscle_group": "Espalda",
            "equipment": "Cables",
            "difficulty": "Intermedio",
            "description": "Aislamiento de dorsales sin involucrar el bíceps.",
            "technique": "1. Brazos casi rectos. 2. Tira de la barra hacia los muslos en un arco. 3. Sube controlando el estiramiento.",
            "tips": "Mantén el core firme para no arquear la espalda.",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Dorsal Ancho, Tríceps (Cabeza Larga)"
        },

        # PIERNAS (Legs)
        {
            "name": "Sentadilla Hack",
            "muscle_group": "Piernas",
            "equipment": "Máquina",
            "difficulty": "Intermedio",
            "description": "Aislamiento masivo de cuádriceps con soporte lumbar.",
            "technique": "1. Apoya la espalda en el respaldo. 2. Baja hasta que los muslos rompan el paralelo. 3. Empuja sin bloquear rodillas.",
            "tips": "Mantén los talones siempre apoyados en la plataforma.",
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Cuádriceps, Glúteos"
        },
        {
            "name": "Prensa de Piernas 45°",
            "muscle_group": "Piernas",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Ejercicio compuesto seguro para desarrollar tren inferior.",
            "technique": "1. Pies a la anchura de hombros. 2. Baja la plataforma controladamente. 3. Empuja con toda la planta del pie.",
            "tips": "No bajes tanto que se despegue la pelvis del asiento.",
            "image_url": "https://images.unsplash.com/photo-1591940742878-13aba4b7a35e?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Cuádriceps, Glúteos, Isquiotibiales"
        },
        {
            "name": "Extensión de Cuádriceps",
            "muscle_group": "Piernas",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Aislamiento directo de la parte frontal del muslo.",
            "technique": "1. Ajusta el rodillo a los tobillos. 2. Extiende piernas al máximo. 3. Baja pausadamente.",
            "tips": "Sujétate de los mangos laterales para no levantarte del asiento.",
            "image_url": "https://images.unsplash.com/photo-1541600391308-e8599619227d?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Cuádriceps"
        },
        {
            "name": "Curl Femoral Tumbado",
            "muscle_group": "Piernas",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Trabajo específico de la parte posterior de la pierna.",
            "technique": "1. Boca abajo, rodillo en talones. 2. Flexiona rodillas llevando el peso a glúteos. 3. Baja lento.",
            "tips": "Mantén la cadera pegada al banco.",
            "image_url": "https://images.unsplash.com/photo-1590487949411-2c58ed91cdef?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Isquiotibiales, Gastrocnemio"
        },
        {
            "name": "Peso Muerto Rumano",
            "muscle_group": "Piernas",
            "equipment": "Barra",
            "difficulty": "Intermedio",
            "description": "Mejor ejercicio para isquiotibiales y gluteos.",
            "technique": "1. Baja la barra rozando las piernas. 2. Lleva la cadera hacia atras hasta sentir tension atras. 3. Sube apretando gluteos.",
            "tips": "No arquees la espalda baja.",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Isquiotibiales, Gluteo Mayor, Erector de la Columna"
        },
        {
            "name": "Zancadas con Mancuernas",
            "muscle_group": "Piernas",
            "equipment": "Mancuernas",
            "difficulty": "Intermedio",
            "description": "Estabilidad y trabajo unilateral de piernas.",
            "technique": "1. Una mancuerna en cada mano. 2. Paso al frente y baja la rodilla trasera casi al suelo. 3. Empuja atrás.",
            "tips": "Mantén el torso erguido.",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Glúteos, Cuádriceps, Core"
        },
        {
            "name": "Elevacion de Gemelos de Pie",
            "muscle_group": "Piernas",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Desarrollo del gastrocnemio.",
            "technique": "1. Apoya hombros en los pads. 2. Ponte de puntillas al maximo. 3. Baja talones por debajo del nivel de la plataforma.",
            "tips": "Aguanta un segundo arriba.",
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Gemelos"
        },

        # HOMBROS (Shoulders)
        {
            "name": "Press Militar en Máquina",
            "muscle_group": "Hombros",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Fuerza vertical de hombro con trayectoria estable.",
            "technique": "1. Ajusta el asiento. 2. Empuja los agarres hacia el techo. 3. Baja hasta la altura de las orejas.",
            "tips": "No bloquees los codos arriba.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Deltoides (Cabeza Lateral y Anterior), Tríceps"
        },
        {
            "name": "Elevaciones Laterales con Mancuernas",
            "muscle_group": "Hombros",
            "equipment": "Mancuernas",
            "difficulty": "Principiante",
            "description": "Clave para la anchura de hombros (deltoides lateral).",
            "technique": "1. Eleva brazos a los lados con codos semi-flexos. 2. Sube hasta la altura del hombro. 3. Baja lento.",
            "tips": "No uses el impulso de las piernas.",
            "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Deltoides Lateral"
        },
        {
            "name": "Elevaciones Laterales en Polea",
            "muscle_group": "Hombros",
            "equipment": "Cables",
            "difficulty": "Intermedio",
            "description": "Tension constante para el hombro lateral.",
            "technique": "1. Polea baja a un lado. 2. Eleva el brazo hacia afuera hasta nivel del hombro. 3. Controla la bajada.",
            "tips": "Cruza el cable por detras para mayor rango.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Deltoides Lateral"
        },
        {
            "name": "Face Pulls",
            "muscle_group": "Hombros",
            "equipment": "Cables",
            "difficulty": "Intermedio",
            "description": "Postura y salud del hombro (deltoides posterior).",
            "technique": "1. Polea a la altura de la cara con cuerda. 2. Tira de la cuerda hacia la frente separando las manos. 3. Aprieta escápulas.",
            "tips": "Lidera con los codos hacia afuera.",
            "image_url": "https://images.unsplash.com/photo-1594737625785-a239f56d0bd1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Deltoides Posterior, Trapecio, Rotadores"
        },

        # BRAZOS (Arms)
        {
            "name": "Curl de Bíceps en Maquina",
            "muscle_group": "Brazos",
            "equipment": "Maquinaria",
            "difficulty": "Principiante",
            "description": "Aislamiento total del biceps.",
            "technique": "1. Apoya brazos en el pad. 2. Flexiona brazos hacia los hombros. 3. Extiende completamente.",
            "tips": "No levantes los hombros del pad.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Bíceps Braquial"
        },
        {
            "name": "Curl de Bíceps con Barra EZ",
            "muscle_group": "Brazos",
            "equipment": "Barra",
            "difficulty": "Principiante",
            "description": "Constructor principal de masa en el bíceps.",
            "technique": "1. Sujeta la barra EZ en los agarres curvos. 2. Flexiona codos hacia hombros. 3. Baja controladamente.",
            "tips": "No muevas los codos hacia adelante o atrás.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Bíceps Braquial, Braquial"
        },
        {
            "name": "Press Francés",
            "muscle_group": "Brazos",
            "equipment": "Barra",
            "difficulty": "Intermedio",
            "description": "Aislamiento de la cabeza larga del tríceps.",
            "technique": "1. Tumbado, barra sobre la cara. 2. Baja la barra a la frente flexionando solo codos. 3. Extiende arriba.",
            "tips": "Mantén los codos cerrados.",
            "image_url": "https://images.unsplash.com/photo-1594737625785-a239f56d0bd1?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Tríceps Braquial"
        },
        {
            "name": "Extensiones de Tríceps en Polea",
            "muscle_group": "Brazos",
            "equipment": "Cables",
            "difficulty": "Principiante",
            "description": "Bombeo y definición de tríceps.",
            "technique": "1. Cuerda en polea alta. 2. Empuja hacia abajo separando la cuerda al final. 3. Sube hasta 90 grados.",
            "tips": "Pega los codos a las costillas.",
            "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Tríceps (Cabezas Lateral y Medial)"
        },
        {
            "name": "Curl Martillo con Mancuernas",
            "muscle_group": "Brazos",
            "equipment": "Mancuernas",
            "difficulty": "Principiante",
            "description": "Trabajo de bíceps y antebrazo (braquiorradial).",
            "technique": "1. Agarre neutro (palmas enfrentadas). 2. Flexiona codo. 3. Baja lento.",
            "tips": "Excelente para dar grosor al brazo.",
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef03a7403f?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Bíceps, Braquiorradial"
        },

        # CORE (Abs)
        {
            "name": "Crunch en Máquina",
            "muscle_group": "Core",
            "equipment": "Máquina",
            "difficulty": "Principiante",
            "description": "Abdominales con resistencia ajustable.",
            "technique": "1. Sujeta los mangos superiores. 2. Flexiona el torso hacia abajo apretando el abdomen. 3. Regresa lento.",
            "tips": "Exhala todo el aire al bajar.",
            "image_url": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Recto Abdominal"
        },
        {
            "name": "Elevación de Piernas Colgado",
            "muscle_group": "Core",
            "equipment": "Corporal",
            "difficulty": "Avanzado",
            "description": "Abdominales inferiores y fuerza de agarre.",
            "technique": "1. Cuélgate de la barra. 2. Eleva piernas estiradas hasta 90 grados. 3. Baja sin balancearte.",
            "tips": "Si es muy difícil, dobla las rodillas.",
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Abdominales Inferiores, Flexores de Cadera"
        },
        {
            "name": "Plancha Abdominal (Plank)",
            "muscle_group": "Core",
            "equipment": "Corporal",
            "difficulty": "Principiante",
            "description": "Resistencia isometrica para todo el core.",
            "technique": "1. Apoyado en antebrazos y pies. 2. Cuerpo recto como una tabla. 3. Mantén la posicion apretando abdomen.",
            "tips": "No subas el gluteo.",
            "image_url": "https://images.unsplash.com/photo-1598971639058-aba7c18f2a2e?q=80&w=500&auto=format&fit=crop",
            "muscle_highlights": "Transverso del Abdomen, Recto Abdominal, Core"
        }
    ]
    
    for ex in exercises:
        db_ex = models.Exercise(**ex)
        db.add(db_ex)
    
    # Usuario de prueba si no existe
    if not db.query(models.User).filter(models.User.id == 1).first():
        user = models.User(id=1, username="IronWarrior", weight_kg=85.0, height_cm=182.0)
        db.add(user)
        
    db.commit()
    print("Base de Datos Premium Poblada con Éxito")

if __name__ == "__main__":
    seed_db()
