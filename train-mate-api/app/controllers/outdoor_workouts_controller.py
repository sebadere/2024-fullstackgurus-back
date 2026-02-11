from flask import Blueprint, request, jsonify
from app.services.auth_service import verify_token_service
from app.services.outdoor_workouts_service import add_outdoor_workout, list_outdoor_workouts, update_outdoor_workout, delete_outdoor_workout


outdoor_workouts_bp = Blueprint('outdoor_workouts_bp', __name__)


@outdoor_workouts_bp.route('/add', methods=['POST'])
def add_outdoor_workout_view():
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        data = request.get_json() or {}
        success, result = add_outdoor_workout(uid, data)
        if not success:
            return jsonify(result), 400

        return jsonify(result), 201
    except Exception as e:
        print(f"Error adding outdoor workout: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@outdoor_workouts_bp.route('/list', methods=['GET'])
def list_outdoor_workouts_view():
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        activity_type = request.args.get('activity_type')

        success, workouts = list_outdoor_workouts(uid, start_date, end_date, activity_type)
        if not success:
            return jsonify({"error": "Failed to list outdoor workouts"}), 500

        return jsonify({"outdoor_workouts": workouts}), 200
    except Exception as e:
        print(f"Error listing outdoor workouts: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@outdoor_workouts_bp.route('/update/<workout_id>', methods=['PUT'])
def update_outdoor_workout_view(workout_id):
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        data = request.get_json() or {}
        success, result = update_outdoor_workout(uid, workout_id, data)
        if not success:
            return jsonify(result), 400

        return jsonify(result), 200
    except Exception as e:
        print(f"Error updating outdoor workout: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@outdoor_workouts_bp.route('/delete/<workout_id>', methods=['DELETE'])
def delete_outdoor_workout_view(workout_id):
    try:
        token = request.headers.get('Authorization')
        if not token or 'Bearer ' not in token:
            return jsonify({"error": "Authorization token missing"}), 403

        token = token.split(' ')[1]
        uid = verify_token_service(token)
        if not uid:
            return jsonify({"error": "Invalid token"}), 403

        success = delete_outdoor_workout(uid, workout_id)
        if not success:
            return jsonify({"error": "Outdoor workout not found"}), 404

        return jsonify({"message": "Outdoor workout deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting outdoor workout: {e}")
        return jsonify({"error": "Something went wrong"}), 500
