from flask import Blueprint, jsonify

from flask_login import current_user, login_required  # type: ignore
from pydantic import BaseModel as PydanticModel

from ucr_chatbot.web_helpers.limit import LimitUsage, LimitUsageList

bp = Blueprint("limit_routes", __name__)


@bp.get("/limits")
@login_required
def get_limit(course_id: int):
    """Responds with limit information"""
    limit_usages = LimitUsageList.get(email=current_user.email, course_id=course_id)
    return jsonify(LimitResponse(limits=limit_usages).model_dump())


class LimitResponse(PydanticModel):
    limits: list[LimitUsage]
