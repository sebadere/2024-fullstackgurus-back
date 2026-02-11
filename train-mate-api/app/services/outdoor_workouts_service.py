from datetime import datetime
from firebase_admin import firestore
from firebase_setup import db


VALID_ACTIVITY_TYPES = {"RUNNING", "CYCLING", "HIKING", "WALKING"}


def _parse_date(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.replace(hour=10, minute=0)


def _parse_number(value, default=None):
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def add_outdoor_workout(uid, data):
    try:
        activity_type = str(data.get('activity_type', '')).upper()
        if activity_type not in VALID_ACTIVITY_TYPES:
            return False, {"error": "Invalid activity_type"}

        duration_minutes = _parse_number(data.get('duration_minutes'))
        calories = _parse_number(data.get('calories'))
        date_str = data.get('date')

        if not date_str:
            return False, {"error": "date is required"}

        if duration_minutes is None:
            return False, {"error": "duration_minutes is required"}
        if duration_minutes <= 0:
            return False, {"error": "duration_minutes must be > 0"}

        if calories is None:
            return False, {"error": "calories is required"}
        if calories <= 0:
            return False, {"error": "calories must be > 0"}

        distance_km = _parse_number(data.get('distance_km'), default=0)
        elevation_gain_m = _parse_number(data.get('elevation_gain_m'), default=0)
        notes = data.get('notes', '')

        if distance_km is None:
            return False, {"error": "distance_km must be numeric"}
        if distance_km < 0:
            return False, {"error": "distance_km must be >= 0"}

        if elevation_gain_m is None:
            return False, {"error": "elevation_gain_m must be numeric"}
        if elevation_gain_m < 0:
            return False, {"error": "elevation_gain_m must be >= 0"}

        try:
            date_obj = _parse_date(date_str)
        except ValueError:
            return False, {"error": "date must use YYYY-MM-DD format"}

        user_ref = db.collection('outdoor_workouts').document(uid)
        if not user_ref.get().exists:
            user_ref.set({})

        workouts_ref = user_ref.collection('user_outdoor_workouts')
        workout_ref = workouts_ref.add({
            'activity_type': activity_type,
            'date': date_obj,
            'duration_minutes': duration_minutes,
            'distance_km': distance_km,
            'elevation_gain_m': elevation_gain_m,
            'calories': calories,
            'notes': str(notes) if notes is not None else '',
        })

        workout_id = workout_ref[1].id
        saved = {
            'id': workout_id,
            'activity_type': activity_type,
            'date': date_obj.isoformat(),
            'duration_minutes': duration_minutes,
            'distance_km': distance_km,
            'elevation_gain_m': elevation_gain_m,
            'calories': calories,
            'notes': notes,
        }

        return True, saved
    except Exception as e:
        print(f"Error saving outdoor workout: {e}")
        return False, {"error": "Failed to save outdoor workout"}


def list_outdoor_workouts(uid, start_date=None, end_date=None, activity_type=None):
    try:
        workouts_ref = db.collection('outdoor_workouts').document(uid).collection('user_outdoor_workouts')

        if start_date:
            workouts_ref = workouts_ref.where('date', '>=', _parse_date(start_date))
        if end_date:
            workouts_ref = workouts_ref.where('date', '<=', _parse_date(end_date))

        if activity_type:
            workouts_ref = workouts_ref.where('activity_type', '==', activity_type.upper())

        workouts_ref = workouts_ref.order_by('date', direction=firestore.Query.DESCENDING)
        workouts = workouts_ref.stream()

        result = []
        for workout in workouts:
            data = workout.to_dict()
            date_value = data.get('date')
            result.append({
                'id': workout.id,
                'activity_type': data.get('activity_type'),
                'date': date_value.isoformat() if hasattr(date_value, 'isoformat') else date_value,
                'duration_minutes': data.get('duration_minutes'),
                'distance_km': data.get('distance_km', 0),
                'elevation_gain_m': data.get('elevation_gain_m', 0),
                'calories': data.get('calories'),
                'notes': data.get('notes', ''),
            })

        return True, result
    except Exception as e:
        print(f"Error listing outdoor workouts: {e}")
        return False, []


def update_outdoor_workout(uid, workout_id, data):
    try:
        workout_ref = db.collection('outdoor_workouts').document(uid).collection('user_outdoor_workouts').document(workout_id)
        workout_doc = workout_ref.get()
        if not workout_doc.exists:
            return False, {"error": "Outdoor workout not found"}

        activity_type = str(data.get('activity_type', '')).upper()
        if activity_type not in VALID_ACTIVITY_TYPES:
            return False, {"error": "Invalid activity_type"}

        duration_minutes = _parse_number(data.get('duration_minutes'))
        calories = _parse_number(data.get('calories'))
        date_str = data.get('date')

        if not date_str:
            return False, {"error": "date is required"}
        if duration_minutes is None or duration_minutes <= 0:
            return False, {"error": "duration_minutes must be > 0"}
        if calories is None or calories <= 0:
            return False, {"error": "calories must be > 0"}

        distance_km = _parse_number(data.get('distance_km'), default=0)
        elevation_gain_m = _parse_number(data.get('elevation_gain_m'), default=0)
        notes = data.get('notes', '')

        if distance_km is None or distance_km < 0:
            return False, {"error": "distance_km must be >= 0"}
        if elevation_gain_m is None or elevation_gain_m < 0:
            return False, {"error": "elevation_gain_m must be >= 0"}

        try:
            date_obj = _parse_date(date_str)
        except ValueError:
            return False, {"error": "date must use YYYY-MM-DD format"}

        updated_data = {
            'activity_type': activity_type,
            'date': date_obj,
            'duration_minutes': duration_minutes,
            'distance_km': distance_km,
            'elevation_gain_m': elevation_gain_m,
            'calories': calories,
            'notes': str(notes) if notes is not None else '',
        }
        workout_ref.update(updated_data)

        return True, {
            'id': workout_id,
            'activity_type': activity_type,
            'date': date_obj.isoformat(),
            'duration_minutes': duration_minutes,
            'distance_km': distance_km,
            'elevation_gain_m': elevation_gain_m,
            'calories': calories,
            'notes': notes,
        }
    except Exception as e:
        print(f"Error updating outdoor workout: {e}")
        return False, {"error": "Failed to update outdoor workout"}


def delete_outdoor_workout(uid, workout_id):
    try:
        workout_ref = db.collection('outdoor_workouts').document(uid).collection('user_outdoor_workouts').document(workout_id)
        workout_doc = workout_ref.get()
        if not workout_doc.exists:
            return False
        workout_ref.delete()
        return True
    except Exception as e:
        print(f"Error deleting outdoor workout: {e}")
        return False
