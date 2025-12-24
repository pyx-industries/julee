"""RST directive serializers.

Serializes Epic, Journey, and Accelerator domain objects to RST directive format.
"""

from ..entities.accelerator import Accelerator
from ..entities.epic import Epic
from ..entities.journey import Journey, StepType


def serialize_epic(epic: Epic) -> str:
    """Serialize an Epic to RST directive format.

    Produces RST matching the define-epic directive::

        .. define-epic:: slug

           Description text here.

        .. epic-story:: story_ref_1

        .. epic-story:: story_ref_2

    Args:
        epic: Epic domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [
        f".. define-epic:: {epic.slug}",
        "",
    ]

    if epic.description:
        # Indent description for RST directive content
        for line in epic.description.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    # Add story references
    for story_ref in epic.story_refs:
        lines.append(f".. epic-story:: {story_ref}")
        lines.append("")

    return "\n".join(lines)


def serialize_journey(journey: Journey) -> str:
    """Serialize a Journey to RST directive format.

    Produces RST matching the define-journey directive::

        .. define-journey:: slug
           :persona: persona_slug
           :intent: User wants to do something
           :outcome: User achieves goal
           :depends-on: dep1, dep2
           :preconditions: cond1
               cond2
           :postconditions: cond1
               cond2

           Goal description here.

        .. step-phase:: Phase Title

           Phase description.

        .. step-story:: Story Title

        .. step-epic:: epic_slug

    Args:
        journey: Journey domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-journey:: {journey.slug}"]

    # Add options
    if journey.persona:
        lines.append(f"   :persona: {journey.persona}")
    if journey.intent:
        lines.append(f"   :intent: {journey.intent}")
    if journey.outcome:
        lines.append(f"   :outcome: {journey.outcome}")
    if journey.depends_on:
        lines.append(f"   :depends-on: {', '.join(journey.depends_on)}")
    if journey.preconditions:
        # Multi-line option format
        lines.append(f"   :preconditions: {journey.preconditions[0]}")
        for cond in journey.preconditions[1:]:
            lines.append(f"       {cond}")
    if journey.postconditions:
        lines.append(f"   :postconditions: {journey.postconditions[0]}")
        for cond in journey.postconditions[1:]:
            lines.append(f"       {cond}")

    lines.append("")

    # Add goal as directive content
    if journey.goal:
        for line in journey.goal.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    # Add steps
    for step in journey.steps:
        if step.step_type == StepType.PHASE:
            lines.append(f".. step-phase:: {step.ref}")
            lines.append("")
            if step.description:
                for line in step.description.split("\n"):
                    lines.append(f"   {line}" if line.strip() else "")
                lines.append("")
        elif step.step_type == StepType.STORY:
            lines.append(f".. step-story:: {step.ref}")
            lines.append("")
        elif step.step_type == StepType.EPIC:
            lines.append(f".. step-epic:: {step.ref}")
            lines.append("")

    return "\n".join(lines)


def serialize_accelerator(accelerator: Accelerator) -> str:
    """Serialize an Accelerator to RST directive format.

    Produces RST matching the define-accelerator directive::

        .. define-accelerator:: slug
           :status: active
           :milestone: MVP
           :acceptance: Criteria met
           :sources-from: int1, int2
           :publishes-to: int1, int2
           :depends-on: accel1, accel2
           :feeds-into: accel1, accel2

           Objective description here.

    Args:
        accelerator: Accelerator domain object to serialize

    Returns:
        RST directive content as string
    """
    lines = [f".. define-accelerator:: {accelerator.slug}"]

    # Add options
    if accelerator.status:
        lines.append(f"   :status: {accelerator.status}")
    if accelerator.milestone:
        lines.append(f"   :milestone: {accelerator.milestone}")
    if accelerator.acceptance:
        lines.append(f"   :acceptance: {accelerator.acceptance}")

    # Format integration references (slug only, descriptions not preserved in RST)
    if accelerator.sources_from:
        slugs = [ref.slug for ref in accelerator.sources_from]
        lines.append(f"   :sources-from: {', '.join(slugs)}")
    if accelerator.publishes_to:
        slugs = [ref.slug for ref in accelerator.publishes_to]
        lines.append(f"   :publishes-to: {', '.join(slugs)}")

    # Accelerator dependencies
    if accelerator.depends_on:
        lines.append(f"   :depends-on: {', '.join(accelerator.depends_on)}")
    if accelerator.feeds_into:
        lines.append(f"   :feeds-into: {', '.join(accelerator.feeds_into)}")

    lines.append("")

    # Add objective as directive content
    if accelerator.objective:
        for line in accelerator.objective.split("\n"):
            lines.append(f"   {line}" if line.strip() else "")
        lines.append("")

    return "\n".join(lines)
