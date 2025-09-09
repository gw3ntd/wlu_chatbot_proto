from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    redirect,
    abort,
    flash,
)

from flask_login import current_user, login_required  # type: ignore


from ucr_chatbot.db.models import (
    Session,
    get_engine,
    Messages,
    MessageType,
    Conversations,
    ConversationState,
    Courses,
    ParticipatesIn,
)
from ucr_chatbot.api.summary_generation import generate_conversation_summary


bp = Blueprint("assistant_routes", __name__)


@bp.route("/assistant/dashboard")
@login_required
def assistant_dashboard():
    """Dashboard for assistants to view and handle redirected conversations."""
    user_email = current_user.email

    with Session(get_engine()) as session:
        assistant_courses = (
            session.query(ParticipatesIn)
            .filter_by(email=user_email, role="assistant")
            .all()
        )

        if not assistant_courses:
            flash("You do not have assistant permissions for any courses.", "danger")
            return redirect(url_for("web_interface.general_routes.course_selection"))

        course_ids = [ac.course_id for ac in assistant_courses]

        ongoing_conversations = (
            session.query(Conversations)
            .where(
                Conversations.course_id.in_(course_ids)
                & (Conversations.state == ConversationState.REDIRECTED),
            )
            .all()
        )

        prompt = """Given a conversation of a messages between a student and an AI tutor, generate a short, 1-3 sentence summary of the topic being discussed, focusing on the topic last being discussed and what the student is struggling on. 
                    Do not generate anything else, only the summary. """
        for conversation in ongoing_conversations:
            if not getattr(conversation, "summary", None):
                summary = generate_conversation_summary(
                    int(getattr(conversation, "id")), prompt, None, None
                )
                setattr(conversation, "summary", str(summary))

        resolved_conversations = (
            session.query(Conversations)
            .where(
                Conversations.course_id.in_(course_ids)
                & (Conversations.state == ConversationState.RESOLVED)
            )
            .all()
        )

        for conversation in resolved_conversations:
            conversation.messages = (
                session.query(Messages).filter_by(conversation_id=conversation.id).all()
            )

        course_names = {}
        for course in session.query(Courses).filter(Courses.id.in_(course_ids)).all():
            course_names[course.id] = course.name

        template = render_template(
            "assistant_dashboard.html",
            ongoing_conversations=ongoing_conversations,
            resolved_conversations=resolved_conversations,
            course_names=course_names,
        )

        session.commit()

    return template


@bp.route("/assistant/conversation/<int:conversation_id>")
@login_required
def assistant_conversation(conversation_id: int):
    """Assistant interface for handling a specific conversation."""
    user_email = current_user.email

    # Check if user is an assistant for this conversation's course
    with Session(get_engine()) as session:
        conversation = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )
        if not conversation:
            abort(404, description="Conversation not found")

        participation = (
            session.query(ParticipatesIn)
            .filter_by(
                email=user_email, course_id=conversation.course_id, role="assistant"
            )
            .first()
        )
        if not participation:
            flash(
                "You do not have assistant permissions for this conversation.", "danger"
            )
            return redirect(url_for("web_interface.general_routes.course_selection"))

        # Get course name
        course = session.query(Courses).filter_by(id=conversation.course_id).first()
        course_name = course.name if course else "Unknown Course"

    return render_template(
        "assistant_conversation.html",
        conversation_id=conversation_id,
        course_id=conversation.course_id,
        course_name=course_name,
        student_email=conversation.initiated_by,
    )


# TODO just use POST
@bp.route("/assistant/conversation/<int:conversation_id>/send", methods=["POST"])
@login_required
def assistant_send_message(conversation_id: int):
    """Allows assistants to send messages in a conversation.
    :param conversation_id: The ID of the conversation.
    """
    content = request.get_json()
    user_email = current_user.email
    message = content.get("message", "")

    # Check if user is an assistant for this conversation's course
    with Session(get_engine()) as session:
        conversation = (
            session.query(Conversations).filter_by(id=conversation_id).first()
        )
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        participation = (
            session.query(ParticipatesIn)
            .filter_by(
                email=user_email, course_id=conversation.course_id, role="assistant"
            )
            .first()
        )
        if not participation:
            return jsonify(
                {"error": "You do not have assistant permissions for this conversation"}
            ), 403

    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400

    # Add assistant message to the conversation
    assistant_message = Messages(
        body=message,
        conversation_id=conversation_id,
        type=MessageType.ASSISTANT_MESSAGE,
        written_by=user_email,
    )
    session.add(assistant_message)
    session.commit()

    return jsonify({"status": "sent", "message": "Assistant message sent successfully"})
