from firebase_setup import db
import json
from collections import Counter
from datetime import datetime


def _normalize_equipment_list(items):
    if not items:
        return []
    return [str(item).upper() for item in items if isinstance(item, str)]


def _is_compatible(required, available):
    if not required:
        return True
    required_set = set(_normalize_equipment_list(required))
    available_set = set(_normalize_equipment_list(available))
    if "ANY" in required_set:
        return True
    return required_set.issubset(available_set)


def _pick_alternative(original, alternatives, available):
    compatible = [alt for alt in alternatives if _is_compatible(alt.get("equipment_required"), available)]
    if not compatible:
        return None

    for alt in compatible:
        if alt.get("category_id") == original.get("category_id"):
            return alt
        if alt.get("training_muscle") and alt.get("training_muscle") == original.get("training_muscle"):
            return alt

    return compatible[0]


def adapt_training(exercise_ids, available_equipment):
    adapted_exercises = []
    replacements = []
    missing = []

    for exercise_id in exercise_ids:
        exercise_ref = db.collection('exercises').document(exercise_id)
        exercise_doc = exercise_ref.get()
        if not exercise_doc.exists:
            missing.append(exercise_id)
            continue

        exercise_data = exercise_doc.to_dict()
        exercise_data['id'] = exercise_id
        required = exercise_data.get("equipment_required")

        if _is_compatible(required, available_equipment):
            adapted_exercises.append(exercise_data)
            continue

        alternative_ids = exercise_data.get("alternative_exercise_ids") or []
        alternatives = []
        for alt_id in alternative_ids:
            alt_ref = db.collection('exercises').document(alt_id)
            alt_doc = alt_ref.get()
            if not alt_doc.exists:
                continue
            alt_data = alt_doc.to_dict()
            alt_data['id'] = alt_id
            alternatives.append(alt_data)

        chosen = _pick_alternative(exercise_data, alternatives, available_equipment)
        if chosen:
            adapted_exercises.append(chosen)
            replacements.append({"from": exercise_id, "to": chosen.get("id")})
        else:
            missing.append(exercise_id)

    return {
        "adapted_exercises": adapted_exercises,
        "replacements": replacements,
        "missing": missing,
    }

def save_user_training(uid, data, exercises_ids, calories_per_hour_mean):
    user_ref = db.collection('trainings').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        user_ref.set({})

    user_trainings_ref = db.collection('trainings').document(uid).collection('user_trainings')

    training_ref = user_trainings_ref.add({
        'calories_per_hour_mean': calories_per_hour_mean,
        'exercises': exercises_ids,
        'name': data['name'],
        'owner': uid
    })

    training_id = training_ref[1].id

    saved_training = {
        'id': training_id,
        'calories_per_hour_mean': calories_per_hour_mean,
        'exercises': exercises_ids,
        'owner': uid,
    }

    return saved_training

def get_user_trainings(uid):

    user_trainings_ref = db.collection('trainings').document(uid).collection('user_trainings')

    try:
        trainings = user_trainings_ref.stream()
        training_list = []
        for training in trainings:
            training_data = training.to_dict()
            exercise_ids = training_data.get('exercises', [])
            training_data['exercises'] = []
            for exercise_id in exercise_ids:
                exercise_doc = db.collection('exercises').document(exercise_id).get()
                if exercise_doc.exists:
                    exercise_data = exercise_doc.to_dict()
                    exercise_data['exercise_id'] = exercise_id
                    training_data['exercises'].append(exercise_data)
            training_data['id'] = training.id
            training_list.append(training_data)
        return training_list

    except Exception as e:
        print(f"Error getting trainings from Firestore: {e}")
        return []

def get_training_by_id(uid, training_id):
    training_ref = db.collection('trainings').document(uid).collection('user_trainings').document(training_id)
    training = training_ref.get()

    if not training.exists:
        return None

    training_data = training.to_dict()
    return training_data

def get_popular_exercises():
    try:
        # Acceder a todos los documentos en la colección `trainings`
        trainings_ref = db.collection_group('user_trainings')  # Esto accede a todos los user_trainings de todos los usuarios
        trainings = trainings_ref.stream()

        # Crear un contador para contar la frecuencia de cada ejercicio
        exercise_counter = Counter()

        # Recorrer todos los entrenamientos y contar los ejercicios
        for training in trainings:
            training_data = training.to_dict()
            exercise_ids = training_data.get('exercises', [])
            
            # Contar cuántas veces aparece cada ejercicio
            for exercise_id in exercise_ids:
                # Asegurarse de que el ejercicio es público
                exercise_doc = db.collection('exercises').document(exercise_id).get()
                if exercise_doc.exists:
                    exercise_data = exercise_doc.to_dict()
                    if exercise_data.get('public', False):  # Solo contar ejercicios públicos
                        exercise_counter[exercise_id] += 1

        # Obtener los 5 ejercicios más populares
        most_common_exercises = exercise_counter.most_common(5)

        # Formatear los resultados para devolver ejercicio_id, nombre y cantidad de veces que lo hicieron
        popular_exercises = []
        for exercise_id, count in most_common_exercises:
            exercise_doc = db.collection('exercises').document(exercise_id).get()
            if exercise_doc.exists:
                exercise_data = exercise_doc.to_dict()
                popular_exercises.append({
                    'exercise_id': exercise_id,
                    'name': exercise_data.get('name'),
                    'count': count
                })

        return popular_exercises

    except Exception as e:
        print(f"Error getting popular exercises: {e}")
        return []
