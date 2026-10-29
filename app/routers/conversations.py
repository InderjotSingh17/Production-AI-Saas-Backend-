
from fastapi import APIRouter, Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Conversation, User,Message
from app.schemas_conversations import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    ChatResponse,
)
from app.services.gemini import generate_response 
from redis.exceptions import RedisError
from app.config import settings
from app.services.redis_client import redis_client
from app.services.rate_limiter import enforce_rate_limit
from app.services.ai_usage import (
    enforce_daily_token_budget,
    record_token_usage,
)
from app.services.ai_cache import get_cached_response, cache_response
from app.services.observability import log_event,start_timer,elapsed_ms
import json
from fastapi.responses import StreamingResponse
from app.services.gemini import stream_response

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = conversation_data.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Conversation title cannot be empty.",
        )
    conversation = Conversation(
        title=title,
        user_id=current_user.id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        .all()
    )
    return conversations

@router.post(
    "/{conversation_id}/messages",
    response_model=ChatResponse,
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    request:Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    user_content = payload.content.strip()

    if not user_content:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )
    if len (user_content) > settings.AI_MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail="Message is too long.",
        )
    try:
        redis_client.ping()
        enforce_rate_limit(current_user.id)
        enforce_daily_token_budget(current_user.id)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later.",
        )
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_content,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(20)
        .all()
    )

    history.reverse()

    prompt = "\n".join(
        f"{'User' if message.role == 'user' else 'Assistant'}: "
        f"{message.content}"
        for message in history
    )

    prompt += "\nAssistant:"
    ai_started=start_timer()
    cache_hit=False
    try:
        ai_content= get_cached_response(prompt)
        if ai_content is not None:
            cache_hit = True
            total_tokens = 0
        else:
            ai_content, total_tokens = generate_response(prompt)
            record_token_usage(current_user.id, total_tokens)
            cache_response(prompt, ai_content)
        log_event(
            "ai_request_completed",
            request_id=request.state.request_id,
            user_id=current_user.id,
            conversation_id=conversation.id,
            duration_ms=elapsed_ms(ai_started),
            total_tokens=total_tokens,
            cache_hit=cache_hit,
        )
    except HTTPException:
        raise
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="AI usage tracking is temporarily unavailable.",
        )
    except Exception:
        log_event(
            "ai_request_failed",
            request_id=request.state.request_id,
            user_id=current_user.id,
            conversation_id=conversation.id,
            duration_ms=elapsed_ms(ai_started),
        )
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI service could not generate a response. "
                "Your message was saved; please try again."
            ),
        )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_content,
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        user_message=user_message,
        assistant_message=assistant_message,
    )


@router.post("/{conversation_id}/messages/stream")
def send_message_stream(
    conversation_id: int,
    payload: MessageCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    user_content = payload.content.strip()

    if not user_content:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    if len(user_content) > settings.AI_MAX_INPUT_CHARS:
        raise HTTPException(status_code=413, detail="Message is too long.")

    try:
        redis_client.ping()
        enforce_rate_limit(current_user.id)
        enforce_daily_token_budget(current_user.id)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable.",
        )

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(20)
        .all()
    )
    history.reverse()

    prompt = "\n".join(
        f"{'User' if item.role == 'user' else 'Assistant'}: {item.content}"
        for item in history
    ) + "\nAssistant:"

    cached_response = get_cached_response(prompt)
    user_id = current_user.id
    conversation_id_value = conversation.id

    def generate_events():
        full_response = []
        total_tokens = 0

        try:
            if cached_response is not None:
                full_response.append(cached_response)
                yield f"data: {json.dumps({'text': cached_response})}\n\n"
            else:
                for text_chunk, reported_tokens in stream_response(prompt):
                    full_response.append(text_chunk)
                    total_tokens = max(total_tokens, reported_tokens)

                    yield f"data: {json.dumps({'text': text_chunk})}\n\n"

            assistant_text = "".join(full_response)

            if not assistant_text:
                yield (
                    "event: error\n"
                    f"data: {json.dumps({'message': 'The AI returned an empty response.'})}\n\n"
                )
                return

            if cached_response is None:
                try:
                    record_token_usage(user_id, total_tokens)
                    cache_response(prompt, assistant_text)
                except RedisError:
                    log_event(
                        "ai_usage_tracking_failed",
                        request_id=getattr(request.state, "request_id", None),
                        user_id=user_id,
                    )

            assistant_message = Message(
                conversation_id=conversation_id_value,
                role="assistant",
                content=assistant_text,
            )
            db.add(assistant_message)
            db.commit()

            yield (
                "event: done\n"
                f"data: {json.dumps({'conversation_id': conversation_id_value})}\n\n"
            )

        except Exception:
            db.rollback()
            log_event(
                "ai_stream_failed",
                request_id=getattr(request.state, "request_id", None),
                user_id=user_id,
                conversation_id=conversation_id_value,
            )
            yield (
                "event: error\n"
                f"data: {json.dumps({'message': 'AI generation failed. Please try again.'})}\n\n"
            )
        finally:
            db.close()

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
