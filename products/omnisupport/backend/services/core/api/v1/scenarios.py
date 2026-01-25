"""Scenario and automation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.scenario import (
    Scenario,
    Trigger,
    ScenarioVariable,
    ScenarioExecution,
    ScenarioStatus,
    ExecutionStatus,
    TriggerType,
)
from shared.models.user import User
from shared.schemas.base import SuccessResponse, PaginatedResponse

from services.admin.scenarios.executor import get_scenario_executor
from services.admin.scenarios.nodes import get_all_node_definitions, get_nodes_by_category, NodeType
from services.admin.scenarios.templates import (
    get_all_templates,
    get_template,
    get_templates_by_category,
    get_templates_by_industry,
    get_template_categories,
)

router = APIRouter()


# ==================== Schemas ====================

class ScenarioCreate(BaseModel):
    """Scenario creation request."""
    name: str
    description: str | None = None
    nodes: list | None = None
    edges: list | None = None
    variables: dict | None = None
    icon: str | None = None
    color: str | None = None


class ScenarioUpdate(BaseModel):
    """Scenario update request."""
    name: str | None = None
    description: str | None = None
    nodes: list | None = None
    edges: list | None = None
    variables: dict | None = None
    icon: str | None = None
    color: str | None = None
    is_active: bool | None = None


class TriggerCreate(BaseModel):
    """Trigger creation request."""
    name: str
    type: TriggerType
    event_type: str | None = None
    conditions: list | None = None
    condition_logic: str = "and"
    config: dict | None = None
    channel_filter: list[str] | None = None
    priority: int = 0


class TriggerUpdate(BaseModel):
    """Trigger update request."""
    name: str | None = None
    event_type: str | None = None
    conditions: list | None = None
    condition_logic: str | None = None
    config: dict | None = None
    channel_filter: list[str] | None = None
    priority: int | None = None
    is_active: bool | None = None


class VariableCreate(BaseModel):
    """Variable creation request."""
    name: str
    display_name: str
    var_type: str
    description: str | None = None
    default_value: dict | None = None
    required: bool = False
    validation: dict | None = None


class TestExecutionRequest(BaseModel):
    """Test execution request."""
    trigger_event: str = "manual"
    trigger_data: dict | None = None


# ==================== Node Definitions ====================

@router.get("/nodes")
async def list_node_definitions(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    category: str | None = None,
):
    """Get available node definitions for scenario builder."""
    if category:
        nodes = get_nodes_by_category(category)
    else:
        nodes = get_all_node_definitions()

    return {
        "items": [
            {
                "type": node.type.value,
                "name": node.name,
                "description": node.description,
                "category": node.category,
                "icon": node.icon,
                "inputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node.inputs],
                "outputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node.outputs],
                "config_schema": node.config_schema,
            }
            for node in nodes
        ],
        "total": len(nodes),
    }


@router.get("/nodes/categories")
async def list_node_categories(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
):
    """Get node categories."""
    categories = set(node.category for node in get_all_node_definitions())
    return {
        "categories": [
            {"id": cat, "name": _get_category_name(cat)}
            for cat in sorted(categories)
        ]
    }


def _get_category_name(category: str) -> str:
    """Get localized category name."""
    names = {
        "flow": "Управление потоком",
        "actions": "Действия",
        "ai": "Искусственный интеллект",
        "integrations": "Интеграции",
    }
    return names.get(category, category)


# ==================== Templates ====================

@router.get("/templates")
async def list_templates(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    category: str | None = None,
    industry: str | None = None,
):
    """Get available scenario templates."""
    if category:
        templates = get_templates_by_category(category)
    elif industry:
        templates = get_templates_by_industry(industry)
    else:
        templates = get_all_templates()

    return {
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "industry": t.industry,
                "tags": t.tags,
                "nodes_count": len(t.nodes),
                "triggers": t.triggers,
            }
            for t in templates
        ],
        "total": len(templates),
    }


@router.get("/templates/categories")
async def list_template_categories(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
):
    """Get template categories."""
    return {"categories": get_template_categories()}


@router.get("/templates/{template_id}")
async def get_template_details(
    template_id: str,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
):
    """Get template details with full node/edge configuration."""
    template = get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден",
        )

    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "industry": template.industry,
        "tags": template.tags,
        "nodes": template.nodes,
        "edges": template.edges,
        "variables": template.variables,
        "triggers": template.triggers,
    }


@router.post("/from-template")
async def create_from_template(
    template_id: str,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str | None = None,
):
    """Create scenario from template."""
    template = get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден",
        )

    scenario = Scenario(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=name or template.name,
        description=template.description,
        nodes=template.nodes,
        edges=template.edges,
        variables=template.variables,
        template_category=template.category,
        status=ScenarioStatus.DRAFT,
    )
    db.add(scenario)
    await db.flush()

    # Create triggers from template
    for trigger_config in template.triggers:
        trigger = Trigger(
            tenant_id=current_user.tenant_id,
            scenario_id=scenario.id,
            name=f"{template.name} - Триггер",
            type=TriggerType.EVENT,
            event_type=trigger_config.get("event_type"),
            conditions=trigger_config.get("conditions", []),
            config={},
        )
        db.add(trigger)

    await db.commit()
    await db.refresh(scenario)

    return scenario


# ==================== Scenarios CRUD ====================

@router.get("")
async def list_scenarios(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ScenarioStatus | None = Query(None, alias="status"),
    is_active: bool | None = None,
    search: str | None = None,
):
    """List scenarios."""
    query = (
        select(Scenario)
        .where(Scenario.tenant_id == current_user.tenant_id)
        .where(Scenario.is_template == False)
        .options(
            selectinload(Scenario.triggers),
            selectinload(Scenario.variable_definitions),
        )
    )

    if status_filter:
        query = query.where(Scenario.status == status_filter)

    if is_active is not None:
        query = query.where(Scenario.is_active == is_active)

    if search:
        query = query.where(Scenario.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Scenario.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    scenarios = list(result.scalars().all())

    return PaginatedResponse.create(
        items=[_serialize_scenario(s) for s in scenarios],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_scenario(
    data: ScenarioCreate,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new scenario."""
    scenario = Scenario(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color,
        nodes=data.nodes or [],
        edges=data.edges or [],
        variables=data.variables or {},
        status=ScenarioStatus.DRAFT,
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    return _serialize_scenario(scenario)


@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get scenario by ID."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
        .options(
            selectinload(Scenario.triggers),
            selectinload(Scenario.variable_definitions),
        )
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    return _serialize_scenario(scenario)


@router.patch("/{scenario_id}")
async def update_scenario(
    scenario_id: UUID,
    data: ScenarioUpdate,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update scenario."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    if data.name is not None:
        scenario.name = data.name
    if data.description is not None:
        scenario.description = data.description
    if data.icon is not None:
        scenario.icon = data.icon
    if data.color is not None:
        scenario.color = data.color
    if data.nodes is not None:
        scenario.nodes = data.nodes
        scenario.version += 1
    if data.edges is not None:
        scenario.edges = data.edges
        scenario.version += 1
    if data.variables is not None:
        scenario.variables = data.variables
    if data.is_active is not None:
        scenario.is_active = data.is_active

    await db.commit()
    await db.refresh(scenario)

    return _serialize_scenario(scenario)


@router.post("/{scenario_id}/publish", response_model=SuccessResponse)
async def publish_scenario(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Publish scenario (make it active)."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    # Validate scenario has nodes
    if not scenario.nodes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сценарий должен содержать хотя бы один узел",
        )

    scenario.status = ScenarioStatus.ACTIVE
    scenario.is_active = True
    scenario.published_version = scenario.version
    await db.commit()

    return SuccessResponse(message="Сценарий опубликован")


@router.post("/{scenario_id}/pause", response_model=SuccessResponse)
async def pause_scenario(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Pause scenario."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    scenario.status = ScenarioStatus.PAUSED
    scenario.is_active = False
    await db.commit()

    return SuccessResponse(message="Сценарий приостановлен")


@router.post("/{scenario_id}/test")
async def test_scenario(
    scenario_id: UUID,
    data: TestExecutionRequest,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Test scenario execution with mock data."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    executor = get_scenario_executor()

    try:
        execution_id = await executor.execute(
            scenario_id=scenario_id,
            trigger_event=data.trigger_event,
            trigger_data=data.trigger_data or {},
            tenant_id=current_user.tenant_id,
        )

        # Get execution result
        exec_result = await db.execute(
            select(ScenarioExecution).where(ScenarioExecution.id == execution_id)
        )
        execution = exec_result.scalar_one_or_none()

        return {
            "execution_id": str(execution_id),
            "status": execution.status.value if execution else "unknown",
            "execution_log": execution.execution_log if execution else None,
            "result": execution.result if execution else None,
            "error_message": execution.error_message if execution else None,
        }

    except Exception as e:
        return {
            "execution_id": None,
            "status": "failed",
            "error_message": str(e),
        }


@router.delete("/{scenario_id}", response_model=SuccessResponse)
async def delete_scenario(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete scenario."""
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    await db.delete(scenario)
    await db.commit()

    return SuccessResponse(message="Сценарий удалён")


# ==================== Executions ====================

@router.get("/{scenario_id}/executions")
async def list_executions(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ExecutionStatus | None = Query(None, alias="status"),
):
    """List scenario executions."""
    # Verify scenario exists
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    query = (
        select(ScenarioExecution)
        .where(ScenarioExecution.scenario_id == scenario_id)
    )

    if status_filter:
        query = query.where(ScenarioExecution.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(ScenarioExecution.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    executions = list(result.scalars().all())

    return PaginatedResponse.create(
        items=[
            {
                "id": str(e.id),
                "status": e.status.value,
                "trigger_event": e.trigger_event,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error_message": e.error_message,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in executions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{scenario_id}/executions/{execution_id}")
async def get_execution(
    scenario_id: UUID,
    execution_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get execution details."""
    result = await db.execute(
        select(ScenarioExecution)
        .where(ScenarioExecution.id == execution_id)
        .where(ScenarioExecution.scenario_id == scenario_id)
        .where(ScenarioExecution.tenant_id == current_user.tenant_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Выполнение не найдено",
        )

    return {
        "id": str(execution.id),
        "scenario_id": str(execution.scenario_id),
        "status": execution.status.value,
        "trigger_event": execution.trigger_event,
        "trigger_data": execution.trigger_data,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "result": execution.result,
        "error_message": execution.error_message,
        "execution_log": execution.execution_log,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
    }


# ==================== Triggers ====================

@router.get("/triggers")
async def list_all_triggers(
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all triggers across scenarios."""
    result = await db.execute(
        select(Trigger)
        .where(Trigger.tenant_id == current_user.tenant_id)
        .options(selectinload(Trigger.scenario))
        .order_by(Trigger.priority.desc())
    )
    triggers = list(result.scalars().all())

    return {
        "items": [_serialize_trigger(t) for t in triggers],
        "total": len(triggers),
    }


@router.get("/{scenario_id}/triggers")
async def list_scenario_triggers(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List triggers for a scenario."""
    # Verify scenario exists
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    result = await db.execute(
        select(Trigger)
        .where(Trigger.scenario_id == scenario_id)
        .order_by(Trigger.priority.desc())
    )
    triggers = list(result.scalars().all())

    return {"items": [_serialize_trigger(t) for t in triggers], "total": len(triggers)}


@router.post("/{scenario_id}/triggers")
async def create_trigger(
    scenario_id: UUID,
    data: TriggerCreate,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create trigger for scenario."""
    # Verify scenario exists
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    trigger = Trigger(
        tenant_id=current_user.tenant_id,
        scenario_id=scenario_id,
        name=data.name,
        type=data.type,
        event_type=data.event_type,
        conditions=data.conditions or [],
        condition_logic=data.condition_logic,
        config=data.config or {},
        channel_filter=data.channel_filter or [],
        priority=data.priority,
    )
    db.add(trigger)
    await db.commit()
    await db.refresh(trigger)

    return _serialize_trigger(trigger)


@router.patch("/triggers/{trigger_id}")
async def update_trigger(
    trigger_id: UUID,
    data: TriggerUpdate,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update trigger."""
    result = await db.execute(
        select(Trigger)
        .where(Trigger.id == trigger_id)
        .where(Trigger.tenant_id == current_user.tenant_id)
    )
    trigger = result.scalar_one_or_none()

    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Триггер не найден",
        )

    if data.name is not None:
        trigger.name = data.name
    if data.event_type is not None:
        trigger.event_type = data.event_type
    if data.conditions is not None:
        trigger.conditions = data.conditions
    if data.condition_logic is not None:
        trigger.condition_logic = data.condition_logic
    if data.config is not None:
        trigger.config = data.config
    if data.channel_filter is not None:
        trigger.channel_filter = data.channel_filter
    if data.priority is not None:
        trigger.priority = data.priority
    if data.is_active is not None:
        trigger.is_active = data.is_active

    await db.commit()
    await db.refresh(trigger)

    return _serialize_trigger(trigger)


@router.delete("/triggers/{trigger_id}", response_model=SuccessResponse)
async def delete_trigger(
    trigger_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete trigger."""
    result = await db.execute(
        select(Trigger)
        .where(Trigger.id == trigger_id)
        .where(Trigger.tenant_id == current_user.tenant_id)
    )
    trigger = result.scalar_one_or_none()

    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Триггер не найден",
        )

    await db.delete(trigger)
    await db.commit()

    return SuccessResponse(message="Триггер удалён")


# ==================== Variables ====================

@router.get("/{scenario_id}/variables")
async def list_variables(
    scenario_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List scenario variables."""
    # Verify scenario exists
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    result = await db.execute(
        select(ScenarioVariable)
        .where(ScenarioVariable.scenario_id == scenario_id)
    )
    variables = list(result.scalars().all())

    return {
        "items": [
            {
                "id": str(v.id),
                "name": v.name,
                "display_name": v.display_name,
                "description": v.description,
                "var_type": v.var_type,
                "default_value": v.default_value,
                "required": v.required,
                "validation": v.validation,
            }
            for v in variables
        ],
        "total": len(variables),
    }


@router.post("/{scenario_id}/variables")
async def create_variable(
    scenario_id: UUID,
    data: VariableCreate,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create scenario variable."""
    # Verify scenario exists
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    # Check for duplicate
    existing = await db.execute(
        select(ScenarioVariable)
        .where(ScenarioVariable.scenario_id == scenario_id)
        .where(ScenarioVariable.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Переменная с таким именем уже существует",
        )

    variable = ScenarioVariable(
        scenario_id=scenario_id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        var_type=data.var_type,
        default_value=data.default_value,
        required=data.required,
        validation=data.validation,
    )
    db.add(variable)
    await db.commit()
    await db.refresh(variable)

    return {
        "id": str(variable.id),
        "name": variable.name,
        "display_name": variable.display_name,
        "description": variable.description,
        "var_type": variable.var_type,
        "default_value": variable.default_value,
        "required": variable.required,
        "validation": variable.validation,
    }


@router.delete("/{scenario_id}/variables/{variable_id}", response_model=SuccessResponse)
async def delete_variable(
    scenario_id: UUID,
    variable_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("scenarios:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete scenario variable."""
    result = await db.execute(
        select(ScenarioVariable)
        .where(ScenarioVariable.id == variable_id)
        .where(ScenarioVariable.scenario_id == scenario_id)
    )
    variable = result.scalar_one_or_none()

    if not variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Переменная не найдена",
        )

    # Verify scenario belongs to tenant
    scenario_result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .where(Scenario.tenant_id == current_user.tenant_id)
    )
    if not scenario_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сценарий не найден",
        )

    await db.delete(variable)
    await db.commit()

    return SuccessResponse(message="Переменная удалена")


# ==================== Helpers ====================

def _serialize_scenario(scenario: Scenario) -> dict:
    """Serialize scenario to dict."""
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "description": scenario.description,
        "icon": scenario.icon,
        "color": scenario.color,
        "status": scenario.status.value,
        "is_active": scenario.is_active,
        "version": scenario.version,
        "published_version": scenario.published_version,
        "nodes": scenario.nodes,
        "edges": scenario.edges,
        "variables": scenario.variables,
        "executions_count": scenario.executions_count,
        "successful_executions": scenario.successful_executions,
        "triggers": [_serialize_trigger(t) for t in scenario.triggers] if scenario.triggers else [],
        "variable_definitions": [
            {
                "id": str(v.id),
                "name": v.name,
                "display_name": v.display_name,
                "var_type": v.var_type,
                "required": v.required,
            }
            for v in scenario.variable_definitions
        ] if scenario.variable_definitions else [],
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None,
    }


def _serialize_trigger(trigger: Trigger) -> dict:
    """Serialize trigger to dict."""
    return {
        "id": str(trigger.id),
        "scenario_id": str(trigger.scenario_id),
        "name": trigger.name,
        "type": trigger.type.value,
        "event_type": trigger.event_type,
        "conditions": trigger.conditions,
        "condition_logic": trigger.condition_logic,
        "config": trigger.config,
        "channel_filter": trigger.channel_filter,
        "priority": trigger.priority,
        "is_active": trigger.is_active,
    }
