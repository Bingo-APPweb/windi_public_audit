"""
WINDI Container API Routes
Flask blueprint para manipulação de containers.

Endpoints:
- POST   /containers              - Criar container
- GET    /containers/<id>         - Obter container
- GET    /containers/session/<id> - Listar containers de sessão
- POST   /containers/<id>/reasoning   - Adicionar micro-pensamento
- DELETE /containers/<id>/reasoning/<idx> - Apagar micro-pensamento (só FREE)
- POST   /containers/<id>/evidence    - Adicionar evidência
- PUT    /containers/<id>/graph       - Actualizar grafo
- POST   /containers/<id>/change-of-mind - Registar mudança de direcção
"""

from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# Add store to path
sys.path.insert(0, str(Path(__file__).parent.parent / "store"))
from container_store import (
    create_container,
    get_container,
    get_containers_by_session,
    add_reasoning,
    add_evidence,
    update_graph,
    delete_reasoning,
    record_change_of_mind
)

container_bp = Blueprint('containers', __name__, url_prefix='/api/containers')


@container_bp.route('', methods=['POST'])
def create():
    """Create a new container."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    container = create_container(session_id)
    return jsonify({
        "success": True,
        "container": container
    }), 201


@container_bp.route('/<container_id>', methods=['GET'])
def get(container_id: str):
    """Get a container by ID."""
    container = get_container(container_id)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    return jsonify({
        "success": True,
        "container": container
    })


@container_bp.route('/session/<session_id>', methods=['GET'])
def list_by_session(session_id: str):
    """List all containers for a session."""
    containers = get_containers_by_session(session_id)

    return jsonify({
        "success": True,
        "count": len(containers),
        "containers": containers
    })


@container_bp.route('/<container_id>/reasoning', methods=['POST'])
def add_thought(container_id: str):
    """Add a micro-thought to the container."""
    data = request.get_json() or {}
    thought = data.get('thought')
    entry_type = data.get('type', 'human')  # I14: explicit type for DIFF filtering

    if not thought:
        return jsonify({
            "success": False,
            "error": "Missing 'thought' field"
        }), 400

    container = add_reasoning(container_id, thought, entry_type)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    return jsonify({
        "success": True,
        "container": container
    })


@container_bp.route('/<container_id>/reasoning/<int:index>', methods=['DELETE'])
def remove_thought(container_id: str, index: int):
    """
    Delete a micro-thought by index.
    Only works in FREE mode (right to forget).
    """
    container = get_container(container_id)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    if container["constitutional"]:
        return jsonify({
            "success": False,
            "error": "Cannot delete from constitutional container (I11)"
        }), 403

    result = delete_reasoning(container_id, index)

    return jsonify({
        "success": True,
        "container": result
    })


@container_bp.route('/<container_id>/evidence', methods=['POST'])
def add_event(container_id: str):
    """Add an evidence event to the container."""
    data = request.get_json() or {}
    event_type = data.get('event_type')
    event_data = data.get('data', {})

    if not event_type:
        return jsonify({
            "success": False,
            "error": "Missing 'event_type' field"
        }), 400

    container = add_evidence(container_id, event_type, event_data)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    return jsonify({
        "success": True,
        "container": container
    })


@container_bp.route('/<container_id>/graph', methods=['PUT'])
def set_graph(container_id: str):
    """Update the ProjectGraph."""
    data = request.get_json() or {}
    graph = data.get('graph', {})

    container = update_graph(container_id, graph)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    return jsonify({
        "success": True,
        "container": container
    })


@container_bp.route('/<container_id>/change-of-mind', methods=['POST'])
def change_direction(container_id: str):
    """
    Record a change-of-mind event.
    This is a first-class event in WINDI.
    """
    data = request.get_json() or {}
    old_direction = data.get('old_direction', '')
    new_direction = data.get('new_direction', '')

    if not new_direction:
        return jsonify({
            "success": False,
            "error": "Missing 'new_direction' field"
        }), 400

    container = record_change_of_mind(container_id, old_direction, new_direction)

    if not container:
        return jsonify({
            "success": False,
            "error": "Container not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Change of mind recorded as cognitive evidence",
        "container": container
    })


@container_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "service": "windi-container-store",
        "status": "healthy",
        "version": "0.1.0"
    })
