from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigOut,
    AgentExecuteRequest,
    AgentExecuteResponse,
)
from ..models import AgentConfig, AgentLog
from ..services.creator import CreatorService
from ..services.supervisor import SupervisorService
from ..services.reader import ReaderService

router = APIRouter(prefix="/api/admin/agents")


# ====== helper ======

def _agent_out(a: AgentConfig) -> AgentConfigOut:
    return AgentConfigOut(
        id=a.id,
        agent_type=a.agent_type,
        name=a.name,
        is_active=a.is_active,
        system_prompt=a.system_prompt or "",
        model=a.model,
        parameters=a.parameters_dict,
        capabilities=a.capabilities_list,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


# ====== Agent Config CRUD ======

@router.get("", response_model=List[AgentConfigOut])
async def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentConfig).order_by(AgentConfig.created_at.desc()).all()
    return [_agent_out(a) for a in agents]


@router.post("", response_model=AgentConfigOut, status_code=201)
async def create_agent(config: AgentConfigCreate, db: Session = Depends(get_db)):
    data = config.model_dump()
    parameters = data.pop("parameters", None)
    capabilities = data.pop("capabilities", None)
    db_agent = AgentConfig(**data)
    if parameters is not None:
        db_agent.parameters_dict = parameters
    if capabilities is not None:
        db_agent.capabilities_list = capabilities
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return _agent_out(db_agent)


@router.get("/{agent_id}", response_model=AgentConfigOut)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent config not found")
    return _agent_out(agent)


@router.put("/{agent_id}", response_model=AgentConfigOut)
async def update_agent(agent_id: int, update: AgentConfigUpdate, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent config not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        if field == "parameters" and value is not None:
            agent.parameters_dict = value
        elif field == "capabilities" and value is not None:
            agent.capabilities_list = value
        else:
            setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return _agent_out(agent)


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent config not found")
    db.query(AgentLog).filter(AgentLog.agent_config_id == agent_id).delete()
    db.delete(agent)
    db.commit()
    return {"detail": "deleted"}


# ====== Test / Execute ======

@router.post("/{agent_id}/test", response_model=AgentExecuteResponse)
async def test_agent(agent_id: int, request: AgentExecuteRequest, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent config not found")

    if agent.agent_type != request.agent_type:
        raise HTTPException(400, f"Agent type mismatch: config={agent.agent_type}, request={request.agent_type}")

    project_id = (request.context or {}).get("project_id", 0)

    if request.agent_type == "creator":
        svc = CreatorService()
        result = await svc.auto_write(project_id, request.chapter_id)
    elif request.agent_type == "supervisor":
        svc = SupervisorService()
        result = await svc.review(request.chapter_id)
    elif request.agent_type == "reader":
        svc = ReaderService()
        result = await svc.simulate_read(request.chapter_id)
    else:
        raise HTTPException(400, f"Unknown agent_type: {request.agent_type}")

    log = AgentLog(
        agent_config_id=agent_id,
        chapter_id=request.chapter_id,
        action=request.agent_type,
        prompt=str(request.context) if request.context else "",
        response=str(result),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return AgentExecuteResponse(status="ok", result=result, log_id=log.id)


# ====== Logs ======

@router.get("/logs")
async def list_agent_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AgentLog)
        .order_by(AgentLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "agent_config_id": log.agent_config_id,
            "chapter_id": log.chapter_id,
            "action": log.action,
            "prompt": log.prompt,
            "response": log.response,
            "tokens_used": log.tokens_used,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


# ====== Batch Delete ======

@router.delete("", response_model=dict)
async def delete_all_agents(db: Session = Depends(get_db)):
    """清空所有 Agent 配置"""
    db.query(AgentLog).delete()
    db.query(AgentConfig).delete()
    db.commit()
    return {"detail": "all agents deleted"}


# ====== Generate Config ======

@router.post("/generate-config")
async def generate_config(body: dict, db: Session = Depends(get_db)):
    """通过自然语言描述生成 Agent 配置"""
    from ..services.ai import generate_agent_config
    description = body.get("description", "")
    if not description:
        raise HTTPException(400, "description is required")
    result = await generate_agent_config(description)
    return result
